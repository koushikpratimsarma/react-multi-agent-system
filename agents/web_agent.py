import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import ToolRuntime, tool
from middleware.tool_limit import ToolCallLimitMiddleware
from config import model
from prompts import WEB_AGENT_PROMPT
from tools.tavily_search import tavily_web_search
from db.database import async_save_tool_call

checkpointer = InMemorySaver()

web_agent = create_agent(
    model=model,
    tools=[tavily_web_search],
    system_prompt=WEB_AGENT_PROMPT,
    name="web_agent",
    checkpointer=checkpointer,
    middleware=[
        ToolCallLimitMiddleware(max_tool_calls=3)
    ],
)

with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["web_agent_tool"])
async def ask_web_agent(messages, runtime: ToolRuntime):

    final_answer = ""
    writer = runtime.stream_writer
    writer({
        "event_type": "agent_start",
        "agent": "web_agent",
        "message": "Web agent started",
    })
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
        "agent": "web_agent",
        "query": query,
    })

    thread_id = "web_thread"

    async for chunk in web_agent.astream(
        {
            "messages": messages
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
        stream_mode=["custom", "updates"],
        version="v2",
    ):

        chunk_type = chunk.get("type")

        if chunk_type == "custom":

            data = chunk.get("data")

            print(
                f"[WEB PROGRESS] {data}"
            )

            # Forward custom events to supervisor
            writer(data)

        elif chunk_type == "updates":

            update_data = chunk.get(
                "data",
                {}
            )
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

    await async_save_tool_call(
        thread_id=thread_id,
        agent_name="web_agent",
        tool_name="tavily_web_search",
        tool_input=str(messages),
        tool_output=final_answer,
    )
    writer({
        "event_type": "agent_complete",
        "agent": "web_agent",
        "message": "Web agent completed",
    })
    
    return final_answer