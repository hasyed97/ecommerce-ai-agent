"""Agent state schema for LangGraph."""

from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str | None
    tool_calls: list[dict] | None
    tool_results: list[dict] | None
    guard_passed: bool
    guard_reason: str | None
    validation_passed: bool
    validation_message: str | None
    next_node: Literal["agent", "tools", "validation", "end"] | None
