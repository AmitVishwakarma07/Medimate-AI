from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..models import User
from ..schemas import ChatIn, ChatOut
from ..services import ai_service

router = APIRouter(prefix="/api", tags=["Chatbot"])


@router.get("/chat/status")
def chat_status(user: User = Depends(get_current_user)):
    return {
        "external_ai_available": ai_service.llm_configured(),
        "external_ai_consent": bool(user.ai_consent),
        "mode": "llm" if (ai_service.llm_configured() and user.ai_consent) else "rule_based",
        "disclaimer": ai_service.DISCLAIMER,
    }


@router.post("/chat", response_model=ChatOut)
def chat(data: ChatIn, user: User = Depends(get_current_user)):
    return ai_service.answer(data.message.strip(), bool(user.ai_consent))
