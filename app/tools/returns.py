"""Return eligibility and request tools."""

import json
from datetime import date, datetime, timedelta

from langchain_core.tools import tool

from config import get_settings
from tools.orders import _load_orders


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def evaluate_return_policy(order: dict) -> dict:
    """Business rules for return eligibility."""
    settings = get_settings()
    window = timedelta(days=settings.return_window_days)
    today = date.today()

    if order.get("status") != "delivered":
        return {
            "eligible": False,
            "reason": f"Order status is '{order.get('status')}'. Only delivered orders can be returned.",
        }

    delivery = _parse_date(order.get("delivery_date"))
    if delivery is None:
        return {"eligible": False, "reason": "Delivery date is missing."}

    if today - delivery > window:
        return {
            "eligible": False,
            "reason": f"Return window of {settings.return_window_days} days has expired.",
            "delivery_date": order.get("delivery_date"),
        }

    return {
        "eligible": True,
        "reason": "Order is within the return window.",
        "delivery_date": order.get("delivery_date"),
    }


@tool
def check_return_eligibility(order_id: str) -> str:
    """Check if an order is eligible for return under store policy."""
    for o in _load_orders():
        if o["order_id"].upper() == order_id.upper():
            result = evaluate_return_policy(o)
            result["order_id"] = o["order_id"]
            return json.dumps(result, indent=2)
    return json.dumps({"eligible": False, "reason": f"Order '{order_id}' not found."})


@tool
def create_return_request(order_id: str, reason: str = "customer_request") -> str:
    """Create a return request if the order is eligible."""
    for o in _load_orders():
        if o["order_id"].upper() == order_id.upper():
            policy = evaluate_return_policy(o)
            if not policy["eligible"]:
                return json.dumps(
                    {"status": "rejected", "order_id": order_id, **policy},
                    indent=2,
                )
            return json.dumps(
                {
                    "status": "approved",
                    "order_id": order_id,
                    "return_id": f"RET-{order_id}",
                    "reason": reason,
                    "message": "Return label will be emailed within 24 hours.",
                },
                indent=2,
            )
    return json.dumps({"status": "error", "reason": f"Order '{order_id}' not found."})
