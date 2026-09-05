"""Chat routes."""

from fastapi import APIRouter

from api.schema.chat import ChatRequest, ChatResponse
from fastapi.responses import StreamingResponse
from api.service.chat import (
    create_chat_response,
    create_chat_stream,
)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await create_chat_response(request)

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    return StreamingResponse(
        create_chat_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )