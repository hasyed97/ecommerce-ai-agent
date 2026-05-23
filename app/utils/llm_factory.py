"""Provider-agnostic chat model factory (OpenAI, Gemini)."""

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from config import Settings, get_settings
from tools import ALL_TOOLS

Provider = Literal["openai", "gemini"]


def _provider(settings: Settings) -> Provider:
    p = (settings.llm_provider or "openai").strip().lower()
    if p not in ("openai", "gemini"):
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Use 'openai' or 'gemini'."
        )
    return p  # type: ignore[return-value]


def is_llm_configured(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    provider = _provider(settings)
    if provider == "openai":
        return bool(settings.openai_api_key)
    return bool(settings.google_api_key)


def llm_config_hint(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    provider = _provider(settings)
    if provider == "gemini":
        return (
            "Gemini is not configured. Set LLM_PROVIDER=gemini and GOOGLE_API_KEY in .env."
        )
    return (
        "OpenAI is not configured. Set LLM_PROVIDER=openai and OPENAI_API_KEY in .env."
    )


def get_chat_model(settings: Settings | None = None) -> BaseChatModel | None:
    """Return an unbound chat model for the configured provider, or None if misconfigured."""
    settings = settings or get_settings()
    provider = _provider(settings)

    if provider == "openai":
        if not settings.openai_api_key:
            return None
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    if not settings.google_api_key:
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )


def build_agent_llm(settings: Settings | None = None):
    """Chat model with ecommerce tools bound."""
    model = get_chat_model(settings)
    if model is None:
        return None
    return model.bind_tools(ALL_TOOLS)
