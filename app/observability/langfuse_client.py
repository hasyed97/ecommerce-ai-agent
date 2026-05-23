"""Langfuse tracing (optional when keys are configured)."""

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

StateT = TypeVar("StateT", bound=dict[str, Any])


def get_langfuse():
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as exc:
        logger.warning("Langfuse unavailable: %s", exc)
        return None


def _serialize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for msg in messages:
        role = getattr(msg, "type", None) or msg.__class__.__name__.replace("Message", "").lower()
        entry: dict[str, Any] = {"role": role, "content": getattr(msg, "content", str(msg))}
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            entry["tool_calls"] = tool_calls
        serialized.append(entry)
    return serialized


def _serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Serialize agent state for Langfuse input/output."""
    out: dict[str, Any] = {}
    for key, value in state.items():
        if key == "messages" and value:
            out[key] = _serialize_messages(list(value))
        else:
            out[key] = value
    return out


class ChatTrace:
    """Update the active Langfuse observation when a trace completes."""

    def __init__(self, span: Any | None) -> None:
        self._span = span

    def complete(self, output: dict[str, Any], *, level: str | None = None) -> None:
        if self._span is None:
            return
        kwargs: dict[str, Any] = {"output": output}
        if level:
            kwargs["level"] = level
        self._span.update(**kwargs)

    def fail(self, message: str) -> None:
        self.complete({"error": message}, level="ERROR")


@contextmanager
def trace_span(
    name: str,
    *,
    input: Any = None,
    metadata: dict[str, Any] | None = None,
) -> Generator[ChatTrace, None, None]:
    """Open a Langfuse span (no flush — use trace_chat_turn at request boundary)."""
    client = get_langfuse()
    if client is None:
        yield ChatTrace(None)
        return

    trace = ChatTrace(None)
    with client.start_as_current_observation(
        name=name,
        as_type="span",
        input=input,
        metadata=metadata or {},
    ) as span:
        trace = ChatTrace(span)
        try:
            yield trace
        except Exception as exc:
            trace.fail(str(exc))
            raise


def traced_node(name: str) -> Callable[[Callable[[StateT], StateT]], Callable[[StateT], StateT]]:
    """Decorator for LangGraph nodes — records state input/output on a Langfuse span."""

    def decorator(fn: Callable[[StateT], StateT]) -> Callable[[StateT], StateT]:
        @wraps(fn)
        def wrapper(state: StateT) -> StateT:
            with trace_span(name, input=_serialize_state(state)) as trace:
                result = fn(state)
                trace.complete(_serialize_state(result))
                return result

        return wrapper

    return decorator


@contextmanager
def trace_chat_turn(
    user_message: str,
    *,
    history: list[dict[str, str]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Generator[ChatTrace, None, None]:
    """Trace a full chat request; child node spans nest under this observation."""
    client = get_langfuse()
    if client is None:
        yield ChatTrace(None)
        return

    trace_input: dict[str, Any] = {"user_message": user_message}
    if history:
        trace_input["conversation"] = history

    trace = ChatTrace(None)
    try:
        with client.start_as_current_observation(
            name="chat_turn",
            as_type="agent",
            input=trace_input,
            metadata=metadata or {},
        ) as span:
            trace = ChatTrace(span)
            try:
                yield trace
            except Exception as exc:
                trace.fail(str(exc))
                raise
    finally:
        try:
            client.flush()
        except Exception as exc:
            logger.warning("Langfuse flush failed: %s", exc)


@contextmanager
def trace_llm_generation(
    *,
    name: str,
    model: str,
    messages: list[Any],
    metadata: dict[str, Any] | None = None,
) -> Generator[ChatTrace, None, None]:
    """Trace a single LLM call (generation) with message input/output."""
    client = get_langfuse()
    if client is None:
        yield ChatTrace(None)
        return

    trace = ChatTrace(None)
    with client.start_as_current_observation(
        name=name,
        as_type="generation",
        model=model,
        input={"messages": _serialize_messages(messages)},
        metadata=metadata or {},
    ) as span:
        trace = ChatTrace(span)
        try:
            yield trace
        except Exception as exc:
            trace.fail(str(exc))
            raise
