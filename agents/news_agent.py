import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import ToolRuntime, tool
from middleware.tool_limit import ToolCallLimitMiddleware
from config import model
from prompts import NEWS_AGENT_PROMPT
from tools.exa_news_search import exa_news_search
from db.database import async_save_tool_call

checkpointer = InMemorySaver()

news_agent = create_agent(
    model=model,
    tools=[exa_news_search],
    system_prompt=NEWS_AGENT_PROMPT,
    name="news_agent",
    checkpointer=checkpointer,
    middleware=[
        ToolCallLimitMiddleware(max_tool_calls=3)
    ],
)

with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)
    
@tool(description=descriptions["news_agent_tool"])
async def ask_news_agent(messages, runtime: ToolRuntime):
    final_answer = ""
    #thread_id = "news_thread"
    writer = runtime.stream_writer

    writer({
        "event_type": "agent_start",
        "agent": "news_agent",
        "message": "News agent started",
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
        "agent": "news_agent",
        "query": query,
    })

    supervisor_thread_id = runtime.config["configurable"]["thread_id"]
    thread_id = f"{supervisor_thread_id}_news"

    async for chunk in news_agent.astream(
        {"messages": [{"role": "user", "content": query}]},

         config={
            "configurable":{
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
                f"[NEWS PROGRESS] {data}"
            )

            writer(data)

        elif chunk_type == "updates":
            update_data = chunk.get("data", {})

            for node_update in update_data.values(): 
                node_messages = node_update.get("messages", [])

                for message in node_messages:
                    if getattr(message, "type", None) == "ai":
                        content = getattr(message, "content", "")

                        if content:
                            final_answer = content

    await async_save_tool_call(
        thread_id=thread_id,
        agent_name="news_agent",
        tool_name="news_search",
        tool_input=str(messages),
        tool_output=final_answer,
    )
    writer({
        "event_type": "agent_complete",
        "agent": "news_agent",
        "message": "News agent completed",
    })
    
    return final_answer


