import json

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool
from middleware.tool_limit import ToolCallLimitMiddleware
from config import model
from prompts import RESEARCH_AGENT_PROMPT

from db.database import save_message

from tools.tavily_search import tavily_web_search
from tools.crawl_html import crawl_html_page
from tools.pdf_url_reader import extract_pdf_text
from agents.arxiv_agent import ask_arxiv_agent


checkpointer = InMemorySaver()

research_agent = create_agent(
    model=model,
    tools=[tavily_web_search, crawl_html_page, extract_pdf_text, ask_arxiv_agent],
    system_prompt=RESEARCH_AGENT_PROMPT,
    name="research_agent",
    checkpointer=checkpointer,
    middleware=[
        ToolCallLimitMiddleware(max_tool_calls=8)
    ],

)




with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)
    
@tool(description=descriptions["research_agent_tool"])
def ask_research_agent(messages):
    final_answer = ""

    for chunk in research_agent.stream(
        {
            "messages": messages
        },
        config={
            "configurable":{
                "thread_id":"research_thread"
            }
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

    save_message(
    thread_id="research_thread",
    role="agent",
    content=final_answer,
    agent_name="research_agent",
    )

    return final_answer