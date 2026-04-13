import asyncio
import httpx

async def test_webhook():
    payload = {
        "message": {
            "type": "user-message",
            "call": {
                "id": "test_call_001",
                "customer": {
                    "number": "+1234567890"
                }
            },
            "transcript": "Hello, I want to file a complaint against my landlord for not returning my security deposit. It has been two months since I moved out."
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://127.0.0.1:8000/voice-webhook", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Connection error: {e}. Make sure the FastAPI server is running.")

if __name__ == "__main__":
    asyncio.run(test_webhook())
