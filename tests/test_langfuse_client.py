from app.observability.langfuse_client import ChatTrace, _serialize_messages, traced_node
from langchain_core.messages import HumanMessage, SystemMessage


class FakeSpan:
    def __init__(self):
        self.updates: list[dict] = []

    def update(self, **kwargs):
        self.updates.append(kwargs)


def test_chat_trace_complete_sets_output():
    span = FakeSpan()
    trace = ChatTrace(span)
    trace.complete({"assistant_message": "hello"})
    assert span.updates[-1]["output"] == {"assistant_message": "hello"}


def test_serialize_messages():
    data = _serialize_messages(
        [SystemMessage(content="sys"), HumanMessage(content="hi")]
    )
    assert data[0]["content"] == "sys"
    assert data[1]["content"] == "hi"


def test_traced_node_wraps_without_langfuse(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")

    @traced_node("test_node")
    def sample_node(state: dict) -> dict:
        return {**state, "next_node": "done"}

    result = sample_node({"messages": [], "next_node": None})
    assert result["next_node"] == "done"
