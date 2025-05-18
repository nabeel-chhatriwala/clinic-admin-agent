# Clinic Front Desk Admin

This project is a FastAPI-based chatbot that integrates with Twilio to handle WebSocket connections and provide real-time communication. The project includes endpoints for starting a call and handling WebSocket connections.

**You will need API keys for three services: Cartesia, Deepgram, and OpenAI.** Make sure you have valid API keys for each and add them to your `.env` file as described below.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configure Twilio URLs](#configure-twilio-urls)
- [Running the Application](#running-the-application)
- [Usage](#usage)

## Features

- **FastAPI**: A modern, fast (high-performance), web framework for building APIs with Python 3.6+.
- **WebSocket Support**: Real-time communication using WebSockets.
- **CORS Middleware**: Allowing cross-origin requests for testing.

## Requirements

- Python 3.10
- ngrok (for tunneling)
- Twilio Account
- API keys for Cartesia, Deepgram, and OpenAI

## Installation

1. **Set up a virtual environment** (optional but recommended):

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. **Install dependencies**:

   ```sh
   pip install -r requirements.txt
   ```

3. **Create .env**:
   Copy the example environment file and update with your settings, including your API keys for Cartesia, Deepgram, and OpenAI:

   ```sh
   cp env.example .env
   ```
   Edit the `.env` file and set the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   CARTESIA_API_KEY=your_cartesia_api_key
   ```

4. **Install ngrok**:
   Follow the instructions on the [ngrok website](https://ngrok.com/download) to download and install ngrok.

## Configure Twilio URLs

1. **Start ngrok**:
   In a new terminal, start ngrok to tunnel the local server:

   ```sh
   ngrok http 8765
   ```

2. **Update the Twilio Webhook**:

   - Go to your Twilio phone number's configuration page
   - Under "Voice Configuration", in the "A call comes in" section:
     - Select "Webhook" from the dropdown
     - Enter your ngrok URL (e.g., http://<ngrok_url>)
     - Ensure "HTTP POST" is selected
   - Click Save at the bottom of the page

3. **Configure streams.xml**:
   - Copy the template file to create your local version:
     ```sh
     cp templates/streams.xml.template templates/streams.xml
     ```
   - In `templates/streams.xml`, replace `<your server url>` with your ngrok URL (without `https://`)
   - The final URL should look like: `wss://abc123.ngrok.app/ws`

## Running the Application

Choose one of these two methods to run the application:

### Using Python (Option 1)

**Run the FastAPI application**:

```sh
python server.py
```

If everything is set up correctly, upon calling the Twilio number you just configured, the pipeline will be triggered and the chatbot will begin handling the call automatically.

