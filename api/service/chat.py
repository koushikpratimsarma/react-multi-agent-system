"""Chat orchestration service."""
import asyncio
from uuid import uuid4
import json
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
#from langgraph.checkpoint.postgres import PostgresSaver

from agents.supervisor_agent import (
    ask_supervisor_agent,
    create_supervisor_agent,
    stream_supervisor_agent,
)
from api.schema.chat import ChatRequest, ChatResponse
from config import POSTGRES_URI
from db.database import async_save_message


async def create_chat_response(request: ChatRequest) -> ChatResponse:
    thread_id = str(uuid4())
    messages = [{"role": "user", "content": request.message}]

    async with AsyncPostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:
        await checkpointer.setup()
        supervisor_agent = create_supervisor_agent(checkpointer)

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

    return ChatResponse(answer=answer)


async def create_chat_stream(request: ChatRequest):

    thread_id = str(uuid4())

    messages = [
        {
            "role": "user",
            "content": request.message,
        }
    ]

    async with AsyncPostgresSaver.from_conn_string(
        POSTGRES_URI
    ) as checkpointer:

        await checkpointer.setup()

        supervisor_agent = create_supervisor_agent(
            checkpointer
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

            if event["type"] == "progress":

                print(
                    f"[PROGRESS] {event['data']}"
                )

            elif event["type"] == "token":

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

            # CHANGE 2: add await
            await async_save_message(
                thread_id=thread_id,
                role="assistant",
                content=final_answer,
                agent_name="supervisor_agent",
            )