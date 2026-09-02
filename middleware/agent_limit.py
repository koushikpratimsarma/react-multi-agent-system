from langchain.agents.middleware import AgentMiddleware


class AgentCallLimitMiddleware(AgentMiddleware):
    """Limit the number of agent calls made by the supervisor."""

    def __init__(self, max_agent_calls: int = 5):
        self.max_agent_calls = max_agent_calls
        self.agent_call_count = 0

    def wrap_tool_call(self, request, handler):
        """Intercept agent-tool calls before execution."""

        if self.agent_call_count >= self.max_agent_calls:
            raise RuntimeError(
                f"Agent call limit of "
                f"{self.max_agent_calls} reached."
            )

        self.agent_call_count += 1

        print(
            f"[AGENT LIMIT] "
            f"{self.agent_call_count}/{self.max_agent_calls}"
        )

        return handler(request)