import logging
from twilio.rest import Client
from app.config import settings

logger = logging.getLogger(__name__)

# Twilio normally handles up to 1600 characters automatically, 
# but we implement defensive manual chunking per your requirements.
MAX_SMS_LENGTH = 1500 

def get_twilio_client():
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return None
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)

def format_voice_response(summary: str) -> str:
    """
    Format concise summary for Vapi TTS.
    Strips complex formatting to make it speakable.
    """
    if not summary:
        return "I have received your issue and am processing it now."
        
    # A concise TTS-friendly output
    return f"I have processed your issue regarding {summary}. A formal complaint draft is being sent to your phone number shortly."

async def send_sms(phone: str, complaint: str):
    """
    Sends complaint text to user phone with length handling 
    and robust error handling.
    """
    client = get_twilio_client()
    
    prefix = "Nyaya Mitra Draft:\n"
    full_text = prefix + complaint
    
    # SMS length handling (split if needed)
    chunks = [full_text[i:i+MAX_SMS_LENGTH] for i in range(0, len(full_text), MAX_SMS_LENGTH)]
    
    if not client:
        for i, chunk in enumerate(chunks):
            logger.warning(f"[MOCK SMS] Chunk {i+1}/{len(chunks)} to {phone}: {chunk}")
        return

    for i, chunk in enumerate(chunks):
        try:
            body = chunk
            if len(chunks) > 1:
                body = f"({i+1}/{len(chunks)}) " + chunk
                
            message = client.messages.create(
                body=body,
                from_=settings.twilio_phone_number,
                to=phone
            )
            logger.info(f"SMS chunk {i+1}/{len(chunks)} sent to {phone}. SID: {message.sid}")
        except Exception as e:
            logger.error(f"Error handling for failed send on chunk {i+1} to {phone}: {e}")
