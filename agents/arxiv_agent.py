import json

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import ToolRuntime, tool
from middleware.tool_limit import ToolCallLimitMiddleware
from prompts import ARXIV_AGENT_PROMPT
from config import model
from tools.arxiv_search import arxiv_search
from db.database import save_tool_call


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
def ask_arxiv_agent(messages, runtime= ToolRuntime):
    final_answer = ""

    for chunk in arxiv_agent.stream(
        {
            "messages": messages
        },

         config={
            "configurable":{
                "thread_id":"arxiv_thread"
            }
        },
        stream_mode=["custom", "updates"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "custom":
            print(f"[ARXIV PROGRESS] {chunk.get('data')}")

        elif chunk_type == "updates":
            update_data = chunk.get("data", {})

            for node_update in update_data.values(): 
                node_messages = node_update.get("messages", [])

                for message in node_messages:
                    if getattr(message, "type", None) == "ai":
                        content = getattr(message, "content", "")

                        if content:
                            final_answer = content

    save_tool_call(
        thread_id=thread_id,
        agent_name="research_agent",
        tool_name="ask_arxiv_agent",
        tool_input=str(messages),
        tool_output=final_answer,
    )

    return final_answer