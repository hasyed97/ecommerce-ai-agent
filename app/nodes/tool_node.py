"""Tool execution router."""

import json

from langchain_core.messages import ToolMessage

from observability.langfuse_client import traced_node
from state import AgentState
from tools import TOOL_MAP
from utils.logger import get_logger

logger = get_logger(__name__)


@traced_node("tools")
def tool_node(state: AgentState) -> AgentState:
    tool_calls = state.get("tool_calls") or []
    results: list[ToolMessage] = []
    tool_results: list[dict] = []

    for call in tool_calls:
        name = call["name"] if isinstance(call, dict) else call.name
        args = call["args"] if isinstance(call, dict) else call.args
        call_id = call["id"] if isinstance(call, dict) else call.id

        fn = TOOL_MAP.get(name)
        if fn is None:
            output = json.dumps({"error": f"Unknown tool: {name}"})
        else:
            try:
                output = fn.invoke(args)
            except Exception as exc:
                logger.exception("Tool %s failed", name)
                output = json.dumps({"error": str(exc)})

        results.append(ToolMessage(content=output, tool_call_id=call_id, name=name))
        tool_results.append({"tool": name, "output": output})

    return {
        **state,
        "messages": results,
        "tool_results": tool_results,
        "next_node": "agent",
    }
