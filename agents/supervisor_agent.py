from langchain.agents import create_agent

from config import model
from prompts import SUPERVISOR_PROMPT
from middleware.agent_limit import AgentCallLimitMiddleware
from agents.web_agent import ask_web_agent
from agents.news_agent import ask_news_agent
from agents.research_agent import ask_research_agent


def create_supervisor_agent(checkpointer):

    return create_agent(
        model=model,
        tools=[
            ask_web_agent,
            ask_research_agent,
            ask_news_agent,
        ],
        system_prompt=SUPERVISOR_PROMPT,
        name="supervisor_agent",
        checkpointer=checkpointer,
        middleware=[
            AgentCallLimitMiddleware(max_agent_calls=5)
        ],
    )

async def ask_supervisor_agent(
    supervisor_agent,
    messages,
    thread_id,
):
    result = await supervisor_agent.ainvoke(
        {
            "messages": messages
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
    )

    final_answer = ""

    for message in result["messages"]:

        if getattr(message, "type", None) == "ai":

            content = getattr(
                message,
                "content",
                ""
            )

            if content:
                final_answer = content

    if final_answer:
        print(
            f"\nSupervisor Assistant:\n"
            f"{final_answer}\n"
        )

    return final_answer


async def stream_supervisor_agent(
    supervisor_agent,
    messages,
    thread_id,
):
    async for chunk in supervisor_agent.astream(
        {
            "messages": messages
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
        stream_mode=["custom", "messages"],
        version="v2",
    ):

        chunk_type = chunk.get("type")

        # --------------------------------
        # Tool / agent progress
        # --------------------------------
        if chunk_type == "custom":

            yield {
                "type": "progress",
                "data": chunk.get("data"),
            }

        # --------------------------------
        # LLM token streaming
        # --------------------------------  
        elif chunk_type == "messages":

            message = chunk.get("data")

            if not message:
                continue

            if isinstance(message, tuple):

                message_chunk, metadata = message

                # Only stream the supervisor agent's model output
                if (
                    metadata.get("lc_agent_name") != "supervisor_agent"
                    or metadata.get("langgraph_node") != "model"
                ):
                    continue

                content = getattr(
                    message_chunk,
                    "content",
                    "",
                )

                if content:
                    yield {
                        "type": "token",
                        "data": content,
                    }