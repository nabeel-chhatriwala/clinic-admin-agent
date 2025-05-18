import io
import os
import sys
import wave
import aiofiles
from dotenv import load_dotenv
from fastapi import WebSocket
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.audio.vad.vad_analyzer import VADParams

from pipecat.services.openai.llm import OpenAILLMService

from pipecat.services.cartesia.tts import CartesiaTTSService

from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

load_dotenv(override=True)

logger.add(sys.stderr, level="DEBUG")
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from functions import verify_insurance, schedule_appointment, end_conversation
from funcSchemas import (
    schedule_appointment_function,
    verify_insurance_function,
    end_conversation_function,
)
from prompt import system_instruction

# Define a function using the standard schema
from datetime import datetime


# Register the function
async def save_audio(
    server_name: str, audio: bytes, sample_rate: int, num_channels: int
):
    if len(audio) > 0:
        filename = (
            f"{server_name}_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )
        with io.BytesIO() as buffer:
            with wave.open(buffer, "wb") as wf:
                wf.setsampwidth(2)
                wf.setnchannels(num_channels)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)
            async with aiofiles.open(filename, "wb") as file:
                await file.write(buffer.getvalue())
        logger.info(f"Merged audio saved to {filename}")
    else:
        logger.info("No audio data to save")


async def run_bot_normal(
    websocket_client: WebSocket, stream_sid: str, call_sid: str, testing: bool
):
    serializer = TwilioFrameSerializer(
        stream_sid=stream_sid,
        call_sid=call_sid,
        account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
    )

    transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(min_volume=0.5, stop_secs=0.5)
            ),
            serializer=serializer,
        ),
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-2024-11-20",
        params=OpenAILLMService.InputParams(
            temperature=0,
        ),
    )
    # 1. Create the context
    # 2. Create aggregators for message handling

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"), audio_passthrough=True
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="bf0a246a-8642-498a-9950-80c35e9276b5",
        push_silence_after_stop=testing,
    )

    llm.register_function(
        "verify_insurance",
        verify_insurance,
    )

    llm.register_function(
        "schedule_appointment",
        schedule_appointment,
    )

    llm.register_function(
        "end_conversation",
        end_conversation,
    )

    messages = [
        {
            "role": "system",
            "content": system_instruction,
        },
    ]

    tools = ToolsSchema(
        standard_tools=[
            verify_insurance_function,
            schedule_appointment_function,
            end_conversation_function,
        ]
    )

    # 1. Create the context
    context = OpenAILLMContext(messages, tools=tools)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),  # Websocket input from clients
            stt,  # Speech-To-Text
            context_aggregator.user(),
            llm,  # LLM
            tts,  # Text-To-Speech
            transport.output(),  # Websocket output to client
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            allow_interruptions=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        # Start recording.   await audiobuffer.start_recording()
        # Kick off the conversation.
        messages.append(
            {"role": "system", "content": "Please introduce yourself to the user."}
        )
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False, force_gc=True)

    await runner.run(task)
