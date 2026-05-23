"""Prompt injection and unsafe-input filter."""

import re

from langchain_core.messages import HumanMessage

from config import get_settings
from observability.langfuse_client import traced_node
from state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(your\s+)?(system|safety)\s+prompt",
    r"you\s+are\s+now\s+(a\s+)?(developer|admin|root)",
    r"reveal\s+(the\s+)?(system\s+)?prompt",
    r"jailbreak",
    r"<\s*script",
    r"```\s*system",
]


def injection_score(text: str) -> float:
    """Heuristic score 0–1; higher means more suspicious."""
    lowered = text.lower()
    hits = sum(1 for p in INJECTION_PATTERNS if re.search(p, lowered, re.I))
    if len(text) > 4000:
        hits += 1
    if hits == 0:
        return 0.0
    return min(1.0, 0.5 + (hits - 1) * 0.25)


@traced_node("guard")
def guard_node(state: AgentState) -> AgentState:
    settings = get_settings()
    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if last_human is None:
        return {
            **state,
            "guard_passed": True,
            "guard_reason": None,
            "next_node": "agent",
        }

    score = injection_score(last_human.content)
    if score >= settings.max_injection_score:
        logger.warning("Guard blocked message (score=%.2f)", score)
        return {
            **state,
            "guard_passed": False,
            "guard_reason": "Your message was blocked for safety reasons. Please rephrase your request.",
            "next_node": "end",
        }

    return {
        **state,
        "guard_passed": True,
        "guard_reason": None,
        "next_node": "agent",
    }
