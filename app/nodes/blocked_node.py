"""Response when guard blocks a request."""

from langchain_core.messages import AIMessage

from observability.langfuse_client import traced_node
from state import AgentState


@traced_node("blocked")
def blocked_node(state: AgentState) -> AgentState:
    reason = state.get("guard_reason") or "Request blocked."
    return {**state, "messages": [AIMessage(content=reason)]}
