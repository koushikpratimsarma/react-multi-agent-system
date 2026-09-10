import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import ToolRuntime, tool
from middleware.tool_limit import ToolCallLimitMiddleware
from prompts import ARXIV_AGENT_PROMPT
from config import model
from tools.arxiv_search import arxiv_search
from db.database import async_save_tool_call

with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

checkpointer = InMemorySaver()

arxiv_agent = create_agent(
    model=model,
    tools=[arxiv_search],
    system_prompt=ARXIV_AGENT_PROMPT,
    name="arxiv_agent",
    checkpointer=checkpointer,
    middleware=[
        ToolCallLimitMiddleware(max_tool_calls=3)
    ],
)

@tool(description=descriptions["arxiv_agent_tool"])
async def ask_arxiv_agent(
    messages,
    runtime: ToolRuntime,
):

    final_answer = ""
    writer = runtime.stream_writer

    # ARXIV AGENT START
    writer({
        "event_type": "agent_start",
        "agent": "arxiv_agent",
        "message": "ArXiv agent started",
    })

    # SUB-AGENT QUERY
    query = messages

    if isinstance(messages, list) and messages:
        last_message = messages[-1]

        if isinstance(last_message, dict):
            query = last_message.get("content", "")
        else:
            query = getattr(
                last_message,
                "content",
                str(last_message),
            )
    if not isinstance(query, str):
        query = str(query)
    writer({
        "event_type": "subagent_query",
        "agent": "arxiv_agent",
        "query": query,
    })

    # ARXIV AGENT STREAM    
    async for chunk in arxiv_agent.astream(
        {
            "messages": messages
        },
        config={
            "configurable": {
                "thread_id": "arxiv_thread"
            }
        },
        stream_mode=["custom", "updates"],
        version="v2",
    ):

        chunk_type = chunk.get("type")

        # CUSTOM EVENTS
        if chunk_type == "custom":

            data = chunk.get("data")

            print(
                f"[ARXIV PROGRESS] {data}"
            )

            # Forward source/progress event
            writer(data)

        # Agent updates
        elif chunk_type == "updates":

            update_data = chunk.get("data", {})

            for node_update in update_data.values():

                node_messages = node_update.get(
                    "messages",
                    []
                )

                for message in node_messages:

                    if getattr(
                        message,
                        "type",
                        None
                    ) == "ai":

                        content = getattr(
                            message,
                            "content",
                            ""
                        )

                        if content:
                            final_answer = content

    # Save tool call asynchronously
    await async_save_tool_call(
        thread_id="arxiv_thread",
        agent_name="arxiv_agent",
        tool_name="ask_arxiv_agent",
        tool_input=str(messages),
        tool_output=final_answer,
    )

    # ARXIV AGENT COMPLETE
    writer({
        "event_type": "agent_complete",
        "agent": "arxiv_agent",
        "message": "ArXiv agent completed",
    })
    
    return final_answer