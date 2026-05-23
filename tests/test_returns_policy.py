from datetime import date, timedelta

from app.tools.orders import _load_orders
from app.tools.returns import evaluate_return_policy
from app.config import get_settings


def test_delivered_within_window_eligible():
    order = next(o for o in _load_orders() if o["order_id"] == "ORD-12345")
    result = evaluate_return_policy(order)
    assert result["eligible"] is True


def test_processing_order_not_eligible():
    order = next(o for o in _load_orders() if o["order_id"] == "ORD-999")
    result = evaluate_return_policy(order)
    assert result["eligible"] is False
    assert "delivered" in result["reason"].lower()


def test_expired_delivery_not_eligible(monkeypatch):
    settings = get_settings()
    old_date = (date.today() - timedelta(days=settings.return_window_days + 5)).isoformat()
    order = {
        "order_id": "ORD-TEST",
        "status": "delivered",
        "delivery_date": old_date,
    }
    result = evaluate_return_policy(order)
    assert result["eligible"] is False
    assert "window" in result["reason"].lower()
