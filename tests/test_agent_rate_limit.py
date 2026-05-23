from langchain_core.messages import AIMessage, HumanMessage

from app.config import get_settings
from app.nodes import agent_node


def test_agent_node_handles_rate_limit(monkeypatch):
    class FakeLLM:
        def invoke(self, messages):
            raise Exception("Error code: 429 - rate limit exceeded")

    monkeypatch.setattr(agent_node, "build_agent_llm", lambda settings=None: FakeLLM())
    monkeypatch.setattr(agent_node, "is_llm_configured", lambda settings=None: True)
    get_settings.cache_clear()

    state = {
        "messages": [HumanMessage(content="hello")],
        "intent": None,
        "tool_calls": None,
        "tool_results": None,
        "guard_passed": True,
        "guard_reason": None,
        "validation_passed": True,
        "validation_message": None,
        "next_node": None,
    }
    result = agent_node.agent_node(state)
    assert result["next_node"] == "end"
    assert isinstance(result["messages"][-1], AIMessage)
    assert "rate limit" in result["messages"][-1].content.lower()
