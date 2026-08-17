import json

from langchain.agents import create_agent
from langchain.tools import tool

from prompts import ARXIV_AGENT_PROMPT
from config import model
from tools.arxiv_search import arxiv_search


with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)


arxiv_agent = create_agent(
    model=model,
    tools=[arxiv_search],
    system_prompt=ARXIV_AGENT_PROMPT,
    name="arxiv_agent",
)


@tool(description=descriptions["arxiv_agent_tool"])
def ask_arxiv_agent(messages):
    final_answer = ""

    for chunk in arxiv_agent.stream(
        {
            "messages": messages
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

    return final_answer