import json

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool
from middleware.tool_limit import ToolCallLimitMiddleware
from config import model
from prompts import WEB_AGENT_PROMPT
from tools.tavily_search import tavily_web_search
from db.database import save_tool_call


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
def ask_web_agent(messages):
    final_answer = ""

    thread_id="web_thread"

    for chunk in web_agent.stream(
        {
            "messages": messages
        },
         config={
            "configurable":{
                "thread_id":"web_thread"
            }
        },
        stream_mode=["custom", "updates"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "custom":
            print(f"[PROGRESS] {chunk.get('data')}")

        elif chunk_type == "updates":
            update_data = chunk.get("data", {})

            for node_update in update_data.values():
                node_messages = node_update.get("messages", [])

                for message in node_messages:
                    if getattr(message, "type", None) == "ai":
                        content = getattr(message, "content", "")

                        if content:
                            final_answer = content

    # if final_answer:
    #     print(f"\nWeb Assistant: {final_answer}\n")

    save_tool_call(
        thread_id=thread_id,
        agent_name="web_agent",
        tool_name="tavily_web_search",
        tool_input=str(messages),
        tool_output=final_answer,
    )
        
    return final_answer

