"""Chat orchestration service."""
import asyncio
from uuid import uuid4
import json
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agents.supervisor_agent import (
    ask_supervisor_agent,
    create_supervisor_agent,
    stream_supervisor_agent,
)
from api.schemas.chat import ChatRequest, ChatResponse
from config import POSTGRES_URI
from db.database import async_save_message, get_messages

async def create_chat_response(
    request: ChatRequest,
    user_name: str,
) -> ChatResponse:
    # Reuse existing thread_id or generate a new one
    thread_id = request.thread_id or str(uuid4())

    # Load previous conversation history if thread exists
    previous_messages = await get_messages(thread_id) if request.thread_id else []
    messages = [
        *previous_messages,
        {"role": "user", "content": request.message},
    ]

    async with AsyncPostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:
        await checkpointer.setup()
        supervisor_agent = create_supervisor_agent(checkpointer, user_name=user_name)

        await async_save_message(
            thread_id=thread_id,
            role="user",
            content=request.message,
            agent_name=None,
        )
        try:
            answer = await ask_supervisor_agent(
                supervisor_agent,
                messages,
                thread_id,
            )
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            raise

        await async_save_message(
            thread_id=thread_id,
            role="assistant",
            content=answer,
            agent_name="supervisor_agent",
        )

    return ChatResponse(answer=answer, thread_id=thread_id)

async def create_chat_stream(
    request: ChatRequest,
    user_name: str,
):

    # Reuse existing thread_id or generate a new one
    thread_id = request.thread_id or str(uuid4())

    # Load previous conversation history if thread exists
    previous_messages = await get_messages(thread_id) if request.thread_id else []
    messages = [
        *previous_messages,
        {
            "role": "user",
            "content": request.message,
        },
    ]

    # Send the identifier before generation starts.  Previously it was sent
    # only after the full stream completed, so a cancelled/failed stream left
    # the browser without the conversation identifier needed for follow-ups.
    yield f"data: {json.dumps({'type': 'thread_id', 'data': thread_id})}\n\n"

    async with AsyncPostgresSaver.from_conn_string(
        POSTGRES_URI
    ) as checkpointer:

        await checkpointer.setup()

        supervisor_agent = create_supervisor_agent(
            checkpointer,
            user_name=user_name,
        )

        # CHANGE 1: add await
        await async_save_message(
            thread_id=thread_id,
            role="user",
            content=request.message,
            agent_name=None,
        )

        final_answer = ""

        async for event in stream_supervisor_agent(
            supervisor_agent,
            messages,
            thread_id,
        ):

            if event["type"] == "token":

                token = event["data"]

                final_answer += token

                print(
                    token,
                    end="",
                    flush=True,
                )

            yield (
                f"data: {json.dumps(event, default=str)}\n\n"
            )

        if final_answer:
            await async_save_message(
                thread_id=thread_id,
                role="assistant",
                content=final_answer,
                agent_name="supervisor_agent",
            )

