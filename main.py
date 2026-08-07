from agents.supervisor_agent import ask_supervisor_agent


# ---------------------------------------------------------
# 6. Main program
# ---------------------------------------------------------

def main():
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

        answer = ask_supervisor_agent(messages)

        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

if __name__ == "__main__":
    main()