CLASSIFIER_PROMPT = """Classify the user message into exactly one intent:
- catalog: product search, recommendations, pricing, stock
- orders: order status, tracking, delivery
- returns: return eligibility, refunds, exchanges
- general: greetings or unclear requests

Reply with only the intent label, nothing else.
"""
