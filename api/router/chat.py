"""Chat routes."""

from fastapi import APIRouter, Depends

from api.schema.chat import ChatRequest, ChatResponse
from fastapi.responses import StreamingResponse
from auth.dependencies import get_current_user
from auth.schemas import UserOut
from api.service.chat import (
    create_chat_response,
    create_chat_stream,
)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserOut = Depends(get_current_user),
) -> ChatResponse:
    return await create_chat_response(request, user_name=current_user.username)


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: UserOut = Depends(get_current_user),
):

    return StreamingResponse(
        create_chat_stream(request, user_name=current_user.username),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )