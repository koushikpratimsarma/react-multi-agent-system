"""Deep Research Agent

Creates a deep agent using `create_deep_agent` that handles complex,
multi-step research queries by decomposing them, searching multiple
sources, and synthesizing findings into comprehensive reports.

"""

import json
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import ToolRuntime, tool
from middleware.tool_limit import ToolCallLimitMiddleware
from config import model
from prompts import DEEP_RESEARCH_AGENT_PROMPT
from db.database import async_save_message
from tools.tavily_search import tavily_web_search
from tools.arxiv_search import arxiv_search
from tools.crawl_html import crawl_html_page
from tools.pdf_url_reader import extract_pdf_text

checkpointer = InMemorySaver()

deep_research_agent = create_deep_agent(
    model=model,
    tools=[
        tavily_web_search,
        arxiv_search,
        crawl_html_page,
        extract_pdf_text,
    ],
    system_prompt=DEEP_RESEARCH_AGENT_PROMPT,
    name="deep_research_agent",
    checkpointer=checkpointer,
    skills=[
        "agents/deep_research/skills/academic-research",
        "agents/deep_research/skills/fact-checking",
        "agents/deep_research/skills/web-research",
    ],
    middleware=[
        ToolCallLimitMiddleware(max_tool_calls=12)
    ],
)

with open("descriptions.json", "r", encoding="utf-8") as f:
    _descriptions = json.load(f)


@tool(description=_descriptions["deep_research_agent_tool"])
async def ask_deep_research_agent(
    messages,
    runtime: ToolRuntime,
):
    """Entry point called by the Supervisor Agent for deep research queries.

    Follows the same streaming pattern as other sub-agents:
    - agent_start / subagent_query events
    - forwards tool/progress events from the internal deep research agent
    - saves the final result to the database
    - agent_complete event
    """
    final_answer = ""
    writer = runtime.stream_writer

    # DEEP RESEARCH AGENT START
    writer({
        "event_type": "agent_start",
        "agent": "deep_research_agent",
        "message": "Deep research agent started",
    })

    # EXTRACT QUERY
    query = messages
    if isinstance(messages, list) and messages:
        last_message = messages[-1]
        if isinstance(last_message, dict):
            query = last_message.get("content", "")
        else:
            query = getattr(last_message, "content", str(last_message))
    if not isinstance(query, str):
        query = str(query)

    writer({
        "event_type": "subagent_query",
        "agent": "deep_research_agent",
        "query": query,
    })

    # RUN INTERNAL DEEP RESEARCH AGENT
    supervisor_thread_id = runtime.config["configurable"]["thread_id"]
    deep_thread_id = f"{supervisor_thread_id}_deep_research"

    async for chunk in deep_research_agent.astream(
        {"messages": [{"role": "user", "content": query}]},
        config={"configurable": {"thread_id": deep_thread_id}},
        stream_mode=["custom", "updates"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "custom":
            data = chunk.get("data")
            print(f"[DEEP RESEARCH PROGRESS] {data}")
            writer(data)

        elif chunk_type == "updates":
            update_data = chunk.get("data") or {}

            if not isinstance(update_data, dict):
                continue

            for node_name, node_update in update_data.items():

                # Some LangGraph node updates can be None
                if not isinstance(node_update, dict):
                    continue

                node_messages = node_update.get("messages") or []

                if not isinstance(node_messages, list):
                    continue

                for message in node_messages:

                    # Extract only AI messages
                    if getattr(message, "type", None) != "ai":
                        continue

                    # Skip AI messages that are requesting tool execution
                    if getattr(message, "tool_calls", None):
                        continue

                    content = getattr(message, "content", "")

                    if isinstance(content, str) and content.strip():
                        final_answer = content

    # SAVE RESULT
    await async_save_message(
        thread_id=deep_thread_id,
        role="agent",
        content=final_answer,
        agent_name="deep_research_agent",
    )

    # DEEP RESEARCH AGENT COMPLETE
    writer({
        "event_type": "agent_complete",
        "agent": "deep_research_agent",
        "message": "Deep research agent completed",
    })

    return final_answer


def create_deep_research_agent(checkpointer=None, user_name=None):
    """Factory function for creating the deep research agent.

    Returns the underlying LangGraph agent instance.
    """
    return deep_research_agent