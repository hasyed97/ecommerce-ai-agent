from langchain_core.messages import HumanMessage

from app.config import get_settings
from app.graph import agent_graph


def test_graph_invoke_catalog_question_no_api_key(monkeypatch):
    """Without API keys the agent returns a configuration hint."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    get_settings.cache_clear()

    result = agent_graph.invoke(
        {"messages": [HumanMessage(content="Show me keyboards in the catalog")]}
    )
    assert result["messages"]
    last = result["messages"][-1]
    assert "not configured" in last.content.lower()
