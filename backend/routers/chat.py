import logging
import os

from fastapi import APIRouter, HTTPException

from schemas import ChatRequest, ChatOut
from services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatOut)
async def chat_endpoint(req: ChatRequest):
    persona = req.persona or os.getenv("CHAT_PERSONA", "stoic")
    try:
        result = await chat_service.chat(req.message, persona)
        return ChatOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Chat endpoint error: %s", e)
        raise HTTPException(status_code=500, detail="Chat failed — check LLM_PROVIDER and API key")
