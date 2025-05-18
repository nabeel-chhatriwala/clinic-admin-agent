import datetime
import random
from pipecat.services.llm_service import FunctionCallParams

from pipecat.frames.frames import TTSSpeakFrame

from pipecat.frames.frames import EndTaskFrame

from pipecat.processors.frame_processor import FrameDirection
available_doctors = ["Dr. Patel", "Dr. Rivera", "Dr. Kim"]
unavailable_doctors = ["Dr. Strange"]

def generate_open_slots():
    today = datetime.datetime.today()
    slots = []
    for i in range(5):
        day = today + datetime.timedelta(days=i)
        for hour in [9, 11, 13, 15, 16]:  # 2 PM = 14 is taken
            slots.append({
                "date": day.strftime("%Y-%m-%d"),
                "time": f"{hour}:00"
            })
    return slots

open_slots = generate_open_slots()

async def verify_insurance(params: FunctionCallParams):
    # Accept both "insurance_provider" and "provider" as keys for compatibility
    provider = params.arguments.get("provider", "").lower()

    # Accept both int and str for policy_number, and always treat as string for digit/length checks
    policy_number = params.arguments.get("policy_number", "")
    if isinstance(policy_number, int):
        policy_number_str = str(policy_number)
    else:
        policy_number_str = str(policy_number).strip()

    procedure = params.arguments.get("procedure", "")

    response = {}

    if provider in ["blue cross", "blue shield"]:
        if policy_number_str.isdigit() and len(policy_number_str) == 8:
            num = int(policy_number_str)
            print(num)
            if 40_000_000 <= num < 60_000_000:
                allowed_procedures = ["Routine check-up", "Flu shot", "Blood test", "X-ray"]
            elif 60_000_000 <= num < 80_000_000:
                allowed_procedures = [
                    "Cholesterol screening", "MRI", "Pap smear",
                    "Routine check-up", "Flu shot", "Blood test", "X-ray"
                ]
            else:
                allowed_procedures = []
            if procedure in allowed_procedures:
                response['status'] = (
                    "Great news! Your insurance policy is active and fully covers the requested procedure. "
                    "If you have any other questions or need help with something else, please let me know—I'm here to help!"
                )
            else:
                response['status'] = (
                    "Thank you for your patience. Unfortunately, it appears that your insurance policy does not cover this particular procedure. "
                    "If you'd like, I can check coverage for a different procedure or assist you with any other questions you may have."
                )
        else:
            response['status'] = (
                "I'm sorry, but the policy number you provided doesn't seem to be valid. "
                "Could you please double-check the number and share it with me again? I'm happy to help you verify your insurance."
            )
    elif provider == "aetna":
        if policy_number_str.isdigit() and len(policy_number_str) == 8:
            num = int(policy_number_str)
            print(num)
            if 30_000_000 <= num < 40_000_000:
                allowed_procedures = ["Routine check-up", "Flu shot", "Blood test", "X-ray"]
            elif 40_000_000 <= num < 50_000_000:
                allowed_procedures = ["Cholesterol screening", "MRI", "Pap smear", "Routine check-up"]
            else:
                allowed_procedures = []
            if procedure in allowed_procedures:
                response['status'] = (
                    "Wonderful! Your insurance policy is active and covers the procedure you requested. "
                    "If you have any more questions or need further assistance, please let me know—I'm always happy to help."
                )
            else:
                response['status'] = (
                    "Thank you for providing your information. It looks like your insurance policy does not cover this specific procedure. "
                    "If you have questions about other procedures or need help with anything else, just let me know."
                )
        else:
            response['status'] = (
                "It seems the policy number you entered isn't quite right. "
                "Would you mind checking it again and letting me know? I'm here to assist you every step of the way."
            )
    else:
        response['status'] = (
            "I'm sorry, but I wasn't able to verify your insurance with the information provided. "
            "Could you please double-check your insurance provider and policy number? I'm here to help you get this sorted out."
        )

    await params.result_callback(response)


async def schedule_appointment(params: FunctionCallParams):
    from datetime import datetime

    first_name = params.arguments.get("first_name")
    last_name = params.arguments.get("last_name")
    preferred_date = params.arguments.get("preferred_date")
    preferred_time = params.arguments.get("preferred_time")
    reason_for_visit = params.arguments.get("reason_for_visit", "")
    doctor_preference = params.arguments.get("doctor_preference", "")

    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else None

    response = {
        "status": "rejected",
        "first_name": first_name,
        "last_name": last_name,
        "preferred_date": preferred_date,
        "preferred_time": preferred_time
    }

    # Check if the selected date is in the past
    try:
        # Accepts ISO format or 'YYYY-MM-DD'
        today = datetime.now().date()
        selected_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
        if selected_date < today:
            response["reason"] = "The selected date is in the past. Please choose a future date."
            await params.result_callback(response)
            return
    except Exception as e:
        response["reason"] = f"Invalid date format: {preferred_date}"
        await params.result_callback(response)
        return

    # Check if requested time is taken
    if preferred_time == "14:00":
        # Suggest an alternative slot (first one available on same day)
        alt_slot = next(
            (slot for slot in open_slots if slot["date"] == preferred_date and slot["time"] != "14:00"),
            None
        )
        if alt_slot:
            response["status"] = "conflict"
            response["reason"] = "2:00 PM is already booked"
            response["alternative_slot"] = alt_slot
        else:
            response["reason"] = "No other slots available on that date"
        await params.result_callback(response)
        return

    # Check doctor availability
    if doctor_preference:
        if doctor_preference in unavailable_doctors:
            other_doctor = random.choice(available_doctors)
            response["status"] = "conflict"
            response["reason"] = f"{doctor_preference} is unavailable"
            response["suggested_doctor"] = other_doctor 
            await params.result_callback(response)
            return

    # Confirm appointment if valid
    response.update({
        "status": "confirmed",
        "reason_for_visit": reason_for_visit,
        "assigned_doctor": doctor_preference or random.choice(available_doctors),
        "confirmation_message": f"Appointment booked for {full_name or 'the patient'} on {preferred_date} at {preferred_time} with {doctor_preference or 'an available doctor'}."
    })

    await params.result_callback(response)

async def end_conversation(params: FunctionCallParams):
    closing_message = params.arguments.get("closing_message")

    await params.llm.push_frame(TTSSpeakFrame(closing_message))

    # Signal that the task should end after processing this frame
    await params.llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)