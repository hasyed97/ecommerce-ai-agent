"""Product catalog tools."""

import json
from pathlib import Path

from langchain_core.tools import tool

from config import get_settings


def _load_products() -> list[dict]:
    path: Path = get_settings().products_path
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@tool
def search_products(query: str) -> str:
    """Search products by name or description (case-insensitive)."""
    q = query.lower().strip()
    matches = [
        p
        for p in _load_products()
        if q in p["name"].lower() or q in p["description"].lower()
    ]
    if not matches:
        return f"No products found for '{query}'."
    lines = [
        f"- {p['id']}: {p['name']} (${p['price']:.2f}, stock: {p['stock_count']})"
        for p in matches[:10]
    ]
    return "\n".join(lines)


@tool
def get_product_by_id(product_id: str) -> str:
    """Get full details for a product by ID (e.g. p_001)."""
    for p in _load_products():
        if p["id"] == product_id:
            return json.dumps(p, indent=2)
    return f"Product '{product_id}' not found."
