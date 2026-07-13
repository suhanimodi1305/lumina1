"""
Chat router — wraps existing apps/chat/ai_service.py unchanged.
"""
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

DJANGO_ROOT = Path(__file__).resolve().parents[3]
if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))

router = APIRouter()


class ChatMessageRequest(BaseModel):
    history:      list[dict[str, Any]]
    scan_context: dict[str, Any] | None = None
    mode:         str = "doctor"
    user_tier:    str = "normal"


class PhotoAnalysisRequest(BaseModel):
    history:   list[dict[str, Any]]
    image:     str           # base64 encoded
    mime_type: str = "image/jpeg"
    mode:      str = "doctor"


@router.post("/message")
async def chat_message(req: ChatMessageRequest):
    """
    Send conversation history to Groq AI.
    Uses existing ai_service.get_ai_response() and parse_product_tags() unchanged.
    """
    try:
        from apps.chat.ai_service import get_ai_response, parse_product_tags

        reply = get_ai_response(
            conversation_history=req.history,
            scan_context=req.scan_context,
            mode=req.mode,
            user_tier=req.user_tier,
        )

        product_tags = parse_product_tags(reply)

        return {
            "reply":        reply,
            "product_tags": product_tags,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/analyze-photo")
async def analyze_photo(req: PhotoAnalysisRequest):
    """
    Send a base64 photo for AI skin analysis within chat context.
    Uses existing ai_service.get_ai_response() with image_base64 parameter.
    """
    try:
        from apps.chat.ai_service import get_ai_response, parse_product_tags

        reply = get_ai_response(
            conversation_history=req.history,
            image_base64=req.image,
            image_media_type=req.mime_type,
            mode=req.mode,
        )

        product_tags = parse_product_tags(reply)

        return {
            "reply":        reply,
            "product_tags": product_tags,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Photo analysis error: {str(e)}")
