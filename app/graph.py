"""LangGraph orchestration."""

from langgraph.graph import END, StateGraph

from nodes.agent_node import agent_node
from nodes.blocked_node import blocked_node
from nodes.guard_node import guard_node
from nodes.tool_node import tool_node
from nodes.validation_node import validation_node
from state import AgentState


def _route_after_guard(state: AgentState) -> str:
    if not state.get("guard_passed", True):
        return "blocked"
    return "agent"


def _route_after_agent(state: AgentState) -> str:
    nxt = state.get("next_node")
    if nxt == "tools":
        return "tools"
    if nxt == "validation":
        return "validation"
    return "end"


def _route_after_tools(state: AgentState) -> str:
    return "agent"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("guard", guard_node)
    graph.add_node("blocked", blocked_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("validation", validation_node)

    graph.set_entry_point("guard")

    graph.add_conditional_edges(
        "guard",
        _route_after_guard,
        {"agent": "agent", "blocked": "blocked"},
    )
    graph.add_edge("blocked", END)

    graph.add_conditional_edges(
        "agent",
        _route_after_agent,
        {"tools": "tools", "validation": "validation", "end": END},
    )
    graph.add_conditional_edges("tools", _route_after_tools, {"agent": "agent"})
    graph.add_edge("validation", END)

    return graph.compile()


agent_graph = build_graph()
