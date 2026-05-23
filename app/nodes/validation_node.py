"""Business-rule validation after tool use (returns policy)."""

import json

from langchain_core.messages import AIMessage

from observability.langfuse_client import traced_node
from state import AgentState
from tools.returns import evaluate_return_policy
from tools.orders import _load_orders


@traced_node("validation")
def validation_node(state: AgentState) -> AgentState:
    """Re-check return-related tool outputs against policy."""
    tool_results = state.get("tool_results") or []
    validation_passed = True
    validation_message = None

    for tr in tool_results:
        if tr.get("tool") not in ("check_return_eligibility", "create_return_request"):
            continue
        try:
            payload = json.loads(tr["output"])
        except json.JSONDecodeError:
            continue

        if payload.get("status") == "approved" and not payload.get("eligible", True):
            validation_passed = False
            validation_message = "Return approval conflicted with policy."
            break

        order_id = payload.get("order_id")
        if order_id and "eligible" in payload:
            order = next(
                (o for o in _load_orders() if o["order_id"].upper() == order_id.upper()),
                None,
            )
            if order:
                expected = evaluate_return_policy(order)
                if payload.get("eligible") != expected.get("eligible"):
                    validation_passed = False
                    validation_message = "Return eligibility mismatch detected."
                    break

    if not validation_passed:
        return {
            **state,
            "validation_passed": False,
            "validation_message": validation_message,
            "messages": [
                AIMessage(
                    content=(
                        "I cannot complete that return request because it "
                        f"violates our policy: {validation_message}"
                    )
                )
            ],
            "next_node": "end",
        }

    return {
        **state,
        "validation_passed": True,
        "validation_message": None,
        "next_node": "end",
    }
