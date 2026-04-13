import logging
from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import VapiWebhookRequest, VapiWebhookResponse, ProcessRequest
from app.services.vapi_service import process_interaction

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/voice-webhook", response_model=VapiWebhookResponse)
async def vapi_webhook(payload: VapiWebhookRequest):
    """
    Receives Vapi webhook payload.
    Synchronously runs the absolute full pipeline end-to-end to return the targeted TTS response.
    """
    msg_type = payload.message.type
    logger.info(f"Received Webhook, type: {msg_type}")

    if msg_type in ["assistant-request", "user-message", "conversation-update"] and payload.message.transcript:
        call_id = payload.message.call.id if payload.message.call else "unknown"
        number = payload.message.call.customer.number if (payload.message.call and payload.message.call.customer and payload.message.call.customer.number) else "+10000000000"
        transcript = payload.message.transcript
        
        # 1-5. Execute the entire integrated flow synchronously!
        action = await process_interaction(transcript, number, call_id)
        
        # 6. Return voice response format
        voice_response = f"Based on your situation, here's what you can do: {action}"
        return VapiWebhookResponse(message=voice_response)

    return VapiWebhookResponse(message="I am listening.")

@router.post("/process")
async def process_internal(request: ProcessRequest):
    """
    Internal endpoint to bypass Vapi structure and submit a transcript manually.
    """
    logger.info(f"Received manual process request for number {request.phone_number}")
    action = await process_interaction(request.transcript, request.phone_number)
    return {"status": "processing_completed", "action": action}
