import logging
from fastapi import APIRouter, Body, HTTPException, status
from app.models.schemas import ProcessRequest
from app.services.vapi_service import process_interaction
from app.services.memory_service import get_recent_memories, store_memory

router = APIRouter()
logger = logging.getLogger(__name__)


def _raise_backend_error(action: str, exc: Exception) -> None:
    message = str(exc).lower()
    if "403" in message or "401" in message or "forbidden" in message or "unauthorized" in message:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{action} is unavailable because Qdrant credentials were rejected.",
        ) from exc

    if (
        "all connection attempts failed" in message
        or "connection refused" in message
        or "timed out" in message
        or "name or service not known" in message
        or "temporary failure in name resolution" in message
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{action} is unavailable because Qdrant could not be reached.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{action} failed due to an internal backend error.",
    ) from exc

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
            try:
                action = await process_interaction(transcript, user_id, call_id)
            except Exception as exc:
                _raise_backend_error("Voice processing", exc)
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

        try:
            action = await process_interaction(transcript, number, call_id)
        except Exception as exc:
            _raise_backend_error("Voice processing", exc)
        voice_response = f"Based on your situation, here's what you can do: {action}"
        return {"message": voice_response}

    return {"message": "I am listening."}

@router.post("/process")
async def process_internal(request: ProcessRequest):
    """
    Internal endpoint to bypass Vapi structure and submit a transcript manually.
    """
    logger.info(f"Received manual process request for number {request.phone_number}")
    try:
        action = await process_interaction(request.transcript, request.phone_number)
    except Exception as exc:
        _raise_backend_error("Processing request", exc)
    return {"status": "processing_completed", "action": action}


@router.get("/history")
async def get_history(user_id: str):
    """
    Returns recent memory items for the demo history page.
    """
    try:
        items = await get_recent_memories(user_id=user_id)
    except Exception as exc:
        _raise_backend_error("History lookup", exc)
    return {"history": items}


@router.post("/memory")
async def save_memory(payload: dict = Body(default={})):
    """
    Stores a conversation summary directly in Qdrant for the history page.
    """
    user_id = payload.get("user_id") or "demo_user"
    text = payload.get("text", "").strip()
    issue_type = payload.get("issue_type") or "conversation"

    if not text:
        return {"status": "ignored"}

    try:
        await store_memory(user_id=user_id, text=text, issue_type=issue_type)
    except Exception as exc:
        _raise_backend_error("Memory storage", exc)
    return {"status": "stored"}
