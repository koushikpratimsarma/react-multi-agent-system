"""Chat orchestration service."""

from uuid import uuid4

from langgraph.checkpoint.postgres import PostgresSaver

from agents.supervisor_agent import ask_supervisor_agent, create_supervisor_agent
from api.schema.chat import ChatRequest, ChatResponse
from config import POSTGRES_URI
from db.database import save_message


def create_chat_response(request: ChatRequest) -> ChatResponse:
    thread_id = str(uuid4())
    messages = [{"role": "user", "content": request.message}]

    with PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:
        checkpointer.setup()
        supervisor_agent = create_supervisor_agent(checkpointer)

        save_message(
            thread_id=thread_id,
            role="user",
            content=request.message,
            agent_name=None,
        )

        answer = ask_supervisor_agent(
            supervisor_agent,
            messages,
            thread_id,
        )

        save_message(
            thread_id=thread_id,
            role="assistant",
            content=answer,
            agent_name="supervisor_agent",
        )

    return ChatResponse(answer=answer)