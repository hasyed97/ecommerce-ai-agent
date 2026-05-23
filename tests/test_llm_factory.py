import pytest

from app.config import Settings, get_settings
from app.utils import llm_factory


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_openai_model_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    settings = get_settings()
    model = llm_factory.get_chat_model(settings)
    assert model is not None
    assert model.__class__.__name__ == "ChatOpenAI"


def test_gemini_model_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    get_settings.cache_clear()
    settings = get_settings()
    model = llm_factory.get_chat_model(settings)
    assert model is not None
    assert model.__class__.__name__ == "ChatGoogleGenerativeAI"


def test_missing_key_returns_none(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    settings = Settings.model_construct(openai_api_key="", llm_provider="openai")
    assert llm_factory.get_chat_model(settings) is None
    assert llm_factory.is_llm_configured(settings) is False


def test_invalid_provider_raises():
    settings = Settings.model_construct(
        llm_provider="anthropic",
        openai_api_key="test",
        google_api_key="test",
    )
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        llm_factory.get_chat_model(settings)
