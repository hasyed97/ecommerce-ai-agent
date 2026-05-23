import pytest

from app.utils import llm_errors


class FakeRateLimitError(Exception):
    status_code = 429


class FakeQuotaError(Exception):
    def __str__(self):
        return "Error code: 429 - insufficient_quota"


def test_detects_rate_limit_by_status():
    assert llm_errors.is_rate_limit_error(FakeRateLimitError("busy"))


def test_detects_quota_message():
    assert llm_errors.is_quota_exceeded_error(FakeQuotaError())
    msg = llm_errors.user_message_for_llm_error(FakeQuotaError())
    assert "quota" in msg.lower()


def test_rate_limit_user_message():
    msg = llm_errors.user_message_for_llm_error(FakeRateLimitError("busy"))
    assert "rate limit" in msg.lower()


@pytest.mark.parametrize(
    "exc",
    [
        Exception("429 Too Many Requests"),
        Exception("rate limit exceeded"),
    ],
)
def test_detects_rate_limit_in_message(exc):
    assert llm_errors.is_rate_limit_error(exc)


def test_openai_rate_limit_type_name():
    class OpenAIRateLimitError(Exception):
        pass

    OpenAIRateLimitError.__name__ = "RateLimitError"
    assert llm_errors.is_rate_limit_error(OpenAIRateLimitError("rate limited"))
