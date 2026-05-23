from app.tools.catalog import search_products, get_product_by_id
from app.tools.orders import get_order, list_orders_by_customer
from app.tools.returns import check_return_eligibility, create_return_request


def test_search_products_finds_mouse():
    out = search_products.invoke({"query": "mouse"})
    assert "p_001" in out
    assert "Wireless Ergonomic Mouse" in out


def test_get_product_by_id():
    out = get_product_by_id.invoke({"product_id": "p_003"})
    assert "Noise Cancelling Headphones" in out


def test_get_order():
    out = get_order.invoke({"order_id": "ORD-12345"})
    assert "Alice Smith" in out
    assert "delivered" in out


def test_list_orders_by_customer():
    out = list_orders_by_customer.invoke({"customer_name": "Bob"})
    assert "ORD-999" in out


def test_return_eligibility_delivered_recent():
    out = check_return_eligibility.invoke({"order_id": "ORD-12345"})
    assert "eligible" in out


def test_return_rejected_processing():
    out = create_return_request.invoke({"order_id": "ORD-999"})
    assert "rejected" in out
