import json

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool

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
async def ask_news_agent(messages):
    final_answer = ""
    thread_id = "news_thread"
    async for chunk in news_agent.astream(
        {"messages": messages},

         config={
            "configurable":{
                "thread_id":"news_thread"
            }
        },

        stream_mode=["custom", "updates"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "custom":
            print(f"[NEWS PROGRESS] {chunk.get('data')}")

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
    
    return final_answer


