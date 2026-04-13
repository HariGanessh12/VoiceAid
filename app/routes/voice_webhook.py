import logging
from fastapi import APIRouter, Body
from app.models.schemas import ProcessRequest
from app.services.vapi_service import process_interaction
from app.services.memory_service import get_recent_memories

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/voice-webhook")
async def vapi_webhook(payload: dict = Body(default={})):
    """
    Accepts either the simple frontend payload or the nested Vapi webhook payload.
    """
    # Frontend demo shape:
    # { "message": "hello", "call": { "from": "demo_user" } }
    if isinstance(payload.get("message"), str):
        transcript = payload.get("message", "").strip()
        user_id = payload.get("call", {}).get("from") or "demo_user"
        call_id = payload.get("call", {}).get("id") or "demo_call"

        if transcript:
            action = await process_interaction(transcript, user_id, call_id)
            return {"message": f"Based on your situation, here's what you can do: {action}"}

        return {"message": "I am listening."}

    # Vapi webhook shape
    message = payload.get("message", {})
    msg_type = message.get("type")
    logger.info(f"Received Webhook, type: {msg_type}")

    transcript = message.get("transcript", "")
    if msg_type in ["assistant-request", "user-message", "conversation-update"] and transcript:
        call = message.get("call") or {}
        call_id = call.get("id") or "unknown"
        customer = call.get("customer") or {}
        number = customer.get("number") or "+10000000000"

        action = await process_interaction(transcript, number, call_id)
        voice_response = f"Based on your situation, here's what you can do: {action}"
        return {"message": voice_response}

    return {"message": "I am listening."}

@router.post("/process")
async def process_internal(request: ProcessRequest):
    """
    Internal endpoint to bypass Vapi structure and submit a transcript manually.
    """
    logger.info(f"Received manual process request for number {request.phone_number}")
    action = await process_interaction(request.transcript, request.phone_number)
    return {"status": "processing_completed", "action": action}


@router.get("/history")
async def get_history(user_id: str):
    """
    Returns recent memory items for the demo history page.
    """
    items = await get_recent_memories(user_id=user_id)
    return {"history": items}
