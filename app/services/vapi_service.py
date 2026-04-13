import logging
import uuid

from app.services.memory_service import init_qdrant, retrieve_context, store_memory
from app.services.llm_service import process_legal_issue
from app.services.sms_service import send_sms

logger = logging.getLogger(__name__)

async def process_interaction(transcript: str, phone_number: str, call_id: str = None) -> str:
    """
    Synchronous logic that processes a transcript, retrieves context, uses the LLM, and sends SMS.
    Returns the action string for TTS reply.
    """
    call_id = call_id or uuid.uuid4().hex
    if not transcript or not transcript.strip():
        logger.info("Empty transcript. No action taken.")
        return

    logger.info(f"Processing call/transcript: {call_id[:8]} for {phone_number}")
    
    await init_qdrant()
    
    # Use phone_number as our unique user_id
    past_context = await retrieve_context(user_id=phone_number, query=transcript)
    
    structured_issue, sms_complaint, action = await process_legal_issue(transcript, past_context)
    
    # Store the synthesized knowledge instead of the raw rambling transcript
    await store_memory(user_id=phone_number, text=structured_issue, issue_type="legal_complaint")
    
    await send_sms(phone_number, sms_complaint)
    logger.info("Processing successfully completed.")
    return action
