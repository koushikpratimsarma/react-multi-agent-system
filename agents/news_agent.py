from langchain.agents import create_agent
from langchain.tools import tool

from config import model
from prompts import NEWS_AGENT_PROMPT
from tools.exa_news_search import exa_news_search

news_agent = create_agent(
    model=model,
    tools=[exa_news_search],
    system_prompt=NEWS_AGENT_PROMPT,
    name="news_agent",
)


NEWS_AGENT_DESCRIPTION = """
Delegate the user's request to the News Agent when the question asks about
latest news, recent events, breaking developments, company announcements,
political developments, technology news, financial news, or events from a
specific recent time period.

The News Agent uses Exa to search recent articles, compare publication dates
and event dates, remove duplicate reports, verify information across reliable
sources, and produce a clear news summary.

Do not use this tool for stable general knowledge, simple weather questions,
or deep academic research involving research papers and literature reviews.
"""

@tool(description=NEWS_AGENT_DESCRIPTION)
def ask_news_agent(messages):
    final_answer = ""

    for chunk in news_agent.stream(
        {"messages": messages},
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

    return final_answer


