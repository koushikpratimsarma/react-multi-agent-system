import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import ToolRuntime, tool
from middleware.tool_limit import ToolCallLimitMiddleware
from config import model
from prompts import RESEARCH_AGENT_PROMPT
from db.database import async_save_message
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
async def ask_research_agent(messages, runtime: ToolRuntime):
    final_answer = ""
    writer = runtime.stream_writer

    # RESEARCH AGENT START
    writer({
        "event_type": "agent_start",
        "agent": "research_agent",
        "message": "Research agent started",
    })

    # SUB-AGENT QUERY
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
        "agent": "research_agent",
        "query": query,
    })

    # RESEARCH AGENT STREAM
    async for chunk in research_agent.astream(
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

        # CUSTOM EVENTS
        if chunk_type == "custom":

            data = chunk.get("data")

            print(
                f"[RESEARCH PROGRESS] {data}"
            )

            # Forward the event to Supervisor
            writer(data)

        # AGENT UPDATES
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

    # SAVE RESEARCH RESULT
    await async_save_message(
    thread_id="research_thread",
    role="agent",
    content=final_answer,
    agent_name="research_agent",
    )

    # RESEARCH AGENT COMPLETE
    writer({
        "event_type": "agent_complete",
        "agent": "research_agent",
        "message": "Research agent completed",
    })

    return final_answer

