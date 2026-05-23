from tools.catalog import search_products, get_product_by_id
from tools.orders import get_order, list_orders_by_customer
from tools.returns import check_return_eligibility, create_return_request

ALL_TOOLS = [
    search_products,
    get_product_by_id,
    get_order,
    list_orders_by_customer,
    check_return_eligibility,
    create_return_request,
]

TOOL_MAP = {t.name: t for t in ALL_TOOLS}
