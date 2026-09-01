from langchain.agents.middleware import AgentMiddleware


class ToolCallLimitMiddleware(AgentMiddleware):
    """Limit the number of tool calls made by an agent."""

    def __init__(self, max_tool_calls: int = 5):
        self.max_tool_calls = max_tool_calls

    def wrap_tool_call(self, request, handler):
        """Intercept every tool call before execution."""

        state = request.state

        tool_call_count = state.get("tool_call_count", 0)

        if tool_call_count >= self.max_tool_calls:
            raise RuntimeError(
                f"Tool call limit of {self.max_tool_calls} reached."
            )

        state["tool_call_count"] = tool_call_count + 1

        print(
            f"[TOOL LIMIT] "
            f"{state['tool_call_count']}/{self.max_tool_calls}"
        )

        return handler(request)