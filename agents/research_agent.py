from langchain.agents import create_agent
from langchain.tools import tool

from config import model
from prompts import RESEARCH_AGENT_PROMPT

from tools.tavily_search import tavily_web_search
from tools.crawl_html import crawl_html_page
from tools.extract_pdf import extract_pdf_text

research_agent = create_agent(
    model=model,
    tools=[tavily_web_search, crawl_html_page, extract_pdf_text],
    system_prompt=RESEARCH_AGENT_PROMPT,
    name="research_agent",
)


RESEARCH_AGENT_DESCRIPTION= """
Delegate the user's request to the Research Agent for in-depth analysis,
technical explanations, research papers, literature reviews, comparisons,
multi-source reasoning, or complex topics that require detailed investigation.
Do not use this tool for simple factual or real-time web queries.
"""

@tool(description=RESEARCH_AGENT_DESCRIPTION)
def ask_research_agent(messages):
    final_answer = ""

    for chunk in research_agent.stream(
        {
            "messages": messages
        },
        stream_mode=["custom", "updates"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "custom":
            print(f"[RESEARCH PROGRESS] {chunk.get('data')}")

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
    #     print(f"\nResearch Assistant:\n{final_answer}\n")

    return final_answer
