"""Deep Research Agent package.

Handles complex, multi-step research queries that require planning,
multiple source types, and synthesis into comprehensive reports.
"""

from .agent import ask_deep_research_agent, create_deep_research_agent

__all__ = ["ask_deep_research_agent", "create_deep_research_agent"]