from langchain.agents import create_agent

from config import model
from prompts import SUPERVISOR_PROMPT

from agents.web_agent import ask_web_agent
from agents.news_agent import ask_news_agent
from agents.research_agent import ask_research_agent

# Main routing agent responsible for selecting the appropriate specialized agent.
supervisor_agent = create_agent(
    model=model,
    tools=[ask_web_agent, ask_research_agent, ask_news_agent],
    system_prompt=SUPERVISOR_PROMPT,
    name="supervisor_agent",
)



def ask_supervisor_agent(messages):
    final_answer = ""

    for chunk in supervisor_agent.stream(
        {
            "messages": messages
        },
        stream_mode=["custom", "updates"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "custom":
            print(f"[SUPERVISOR PROGRESS] {chunk.get('data')}")

        elif chunk_type == "updates":
            update_data = chunk.get("data", {})

            for node_update in update_data.values():
                node_messages = node_update.get("messages", [])

                for message in node_messages:
                    if getattr(message, "type", None) == "ai":
                        content = getattr(message, "content", "")

                        if content:
                            final_answer = content

    if final_answer:
        print(f"\nSupervisor Assistant:\n{final_answer}\n")

    return final_answer