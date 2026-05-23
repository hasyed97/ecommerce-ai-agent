"""Map provider LLM failures to user-friendly messages."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

RATE_LIMIT_MESSAGE = (
    "The AI service is temporarily busy (rate limit). "
    "Please wait a minute and try again."
)

QUOTA_EXCEEDED_MESSAGE = (
    "Your API account has no remaining quota. "
    "Check your provider billing or plan, then try again later."
)

GENERIC_LLM_ERROR_MESSAGE = (
    "Something went wrong while contacting the AI service. Please try again shortly."
)


def _status_code(exc: BaseException) -> int | None:
    for attr in ("status_code", "code", "http_status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value
    return None


def _walk_exceptions(exc: BaseException):
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _exception_text(exc: BaseException) -> str:
    parts: list[str] = []
    for item in _walk_exceptions(exc):
        parts.append(str(item))
        body = getattr(item, "body", None)
        if body is not None:
            parts.append(str(body))
    return " ".join(parts).lower()


def is_quota_exceeded_error(exc: BaseException) -> bool:
    text = _exception_text(exc)
    return (
        "insufficient_quota" in text
        or "exceeded your current quota" in text
        or "billing" in text
        and "quota" in text
    )


def is_rate_limit_error(exc: BaseException) -> bool:
    rate_limit_types: tuple[str, ...] = (
        "RateLimitError",
        "ResourceExhausted",
        "TooManyRequests",
    )
    for item in _walk_exceptions(exc):
        if type(item).__name__ in rate_limit_types:
            return True
        if _status_code(item) == 429:
            return True

    text = _exception_text(exc)
    return (
        "error code: 429" in text
        or "status': 429" in text
        or "status_code': 429" in text
        or "rate limit" in text
        or "too many requests" in text
        or "resource exhausted" in text
        or "quota exceeded" in text
    )


def user_message_for_llm_error(exc: BaseException) -> str:
    if is_quota_exceeded_error(exc):
        return QUOTA_EXCEEDED_MESSAGE
    if is_rate_limit_error(exc):
        return RATE_LIMIT_MESSAGE
    return GENERIC_LLM_ERROR_MESSAGE


def log_llm_error(exc: BaseException, *, provider: str) -> None:
    status = _status_code(exc)
    extra: dict[str, Any] = {"provider": provider}
    if status is not None:
        extra["status_code"] = status
    if is_rate_limit_error(exc):
        logger.warning("LLM rate limit (%s): %s", provider, exc, extra=extra)
    else:
        logger.exception("LLM call failed (%s)", provider, exc_info=exc, extra=extra)
