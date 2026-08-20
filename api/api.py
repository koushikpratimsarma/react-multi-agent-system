from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4
from langgraph.checkpoint.postgres import PostgresSaver
from db.database import save_message

from config import POSTGRES_URI
from agents.supervisor_agent import (
    create_supervisor_agent,
    ask_supervisor_agent,
)


app = FastAPI(
    title="Multi-Agent System",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "message": "Agent API is running"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    thread_id = str(uuid4())

    with PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:

        checkpointer.setup()

        supervisor_agent = create_supervisor_agent(
            checkpointer
        )

        messages = [
            {
                "role": "user",
                "content": request.message,
            }
        ]
        # Save user message to PostgreSQL
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
        # Save assistant response to PostgreSQL
        save_message(
            thread_id=thread_id,
            role="assistant",
            content=answer,
            agent_name="supervisor_agent",
        )

        return {
            "answer": answer
        }