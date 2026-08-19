from langgraph.checkpoint.postgres import PostgresSaver

from config import POSTGRES_URI
from agents.supervisor_agent import (
    create_supervisor_agent,
    ask_supervisor_agent,
)


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():

    with PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer:

        # Create/update LangGraph checkpoint tables
        checkpointer.setup()

        # Supervisor uses PostgreSQL checkpointer
        supervisor_agent = create_supervisor_agent(
            checkpointer
        )

        print("ReAct Multi-Agent System")
        print("Type 'exit' to stop.")

        messages = []

        while True:

            question = input("You: ").strip()

            if question.lower() in {"exit", "quit"}:
                print("Agent stopped.")
                break

            if not question:
                continue

            messages.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            answer = ask_supervisor_agent(
                supervisor_agent,
                messages,
            )

            messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )


if __name__ == "__main__":
    main()