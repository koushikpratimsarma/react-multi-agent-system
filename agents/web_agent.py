from langchain.agents import create_agent
from langchain.tools import tool

from config import model
from prompts import WEB_AGENT_PROMPT
from tools.tavily_search import tavily_web_search

web_agent = create_agent(
    model=model,
    tools=[tavily_web_search],
    system_prompt=WEB_AGENT_PROMPT,
    name="web_agent",
)


WEB_AGENT_DESCRIPTION = """
Delegate the user's request to the Web Agent when the answer requires searching
the internet. Suitable for current events, breaking news, weather, stock prices,
recent technologies, company updates, live information, and other information
that may have changed after the model's knowledge cutoff.
Do not use this tool for general knowledge or conceptual questions that can be
answered directly by the language model."""

@tool(description=WEB_AGENT_DESCRIPTION)
def ask_web_agent(messages):
    final_answer = ""

    for chunk in web_agent.stream(
        {
            "messages": messages
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

    return final_answer

