"""Chat routes."""

from fastapi import APIRouter

from api.schema.chat import ChatRequest, ChatResponse
from api.service.chat import create_chat_response


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return create_chat_response(request)