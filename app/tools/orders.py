"""Order lookup tools."""

import json
from pathlib import Path

from langchain_core.tools import tool

from config import get_settings


def _load_orders() -> list[dict]:
    path: Path = get_settings().orders_path
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@tool
def get_order(order_id: str) -> str:
    """Get order details by order ID (e.g. ORD-12345)."""
    for o in _load_orders():
        if o["order_id"].upper() == order_id.upper():
            return json.dumps(o, indent=2)
    return f"Order '{order_id}' not found."


@tool
def list_orders_by_customer(customer_name: str) -> str:
    """List orders for a customer by name (case-insensitive partial match)."""
    name = customer_name.lower().strip()
    matches = [o for o in _load_orders() if name in o["customer_name"].lower()]
    if not matches:
        return f"No orders found for customer '{customer_name}'."
    return json.dumps(matches, indent=2)
