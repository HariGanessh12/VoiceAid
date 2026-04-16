# VoiceAid - Backend

A voice-first AI legal assistant backend. This system receives webhooks from Vapi (voice input), synthesizes the query into a structured legal issue using OpenAI, queries past interactions from Qdrant, and texts the user a drafted complaint via Twilio.

## Prerequisites

- Python 3.10+
- OpenAI API Key
- Twilio Account SID & Auth Token (optional for testing)
- Qdrant Cluster Details (optional, uses local memory by default)
- Vapi Dashboard set up

## Setup Instructions

1. **Clone/Navigate to Repo**
   ```bash
   cd VoiceAid
   ```

2. **Create a virtual environment & Install dependencies**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   # source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Create a `.env` file in the project root and fill out your keys.
   ```bash
   # Windows PowerShell
   New-Item .env -ItemType File

   # Or create the file manually and add your values
   ```

   For Qdrant demo mode, keep these defaults:
   ```env
   QDRANT_SEED_DEMO_DATA=true
   QDRANT_ALLOW_RUNTIME_WRITES=false
   ```
   This seeds exactly 2 demo memories in Qdrant and prevents extra runtime writes.

4. **Run the FastAPI server**
   ```bash
   uvicorn main:app --reload
   ```

5. **Expose Localhost (ngrok)**
   If running locally, use ngrok to expose your port:
   ```bash
   ngrok http 8000
   ```
   Provide the `https://<your-ngrok-url>.ngrok-free.app/api/vapi/webhook` to your Vapi assistant's _Phone Call End Webhook URL_.

## Integration Details

- **Vapi:** Triggers `/api/vapi/webhook` at the end of every call. The server asynchronously processes the transcript.
- **Qdrant:** Maintains past structured interactions based on embeddings from text-embedding-ada-002 (or v3-small).
- **Twilio:** Sends the final tailored draft as an SMS to the user phone number reported by Vapi.
