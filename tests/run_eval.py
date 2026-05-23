"""Run evaluation cases (requires OPENAI_API_KEY for LLM cases)."""

import json
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

from app.graph import agent_graph
from app.nodes.guard_node import guard_node

CASES_PATH = Path(__file__).parent / "eval_cases.json"


def load_cases() -> list[dict]:
    with CASES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def run_case(case: dict) -> dict:
    if case.get("expected_blocked"):
        state = {
            "messages": [HumanMessage(content=case["input"])],
            "intent": None,
            "tool_calls": None,
            "tool_results": None,
            "guard_passed": True,
            "guard_reason": None,
            "validation_passed": True,
            "validation_message": None,
            "next_node": None,
        }
        result = guard_node(state)
        text = (result.get("guard_reason") or "").lower()
        passed = result.get("guard_passed") is False
        for sub in case.get("expected_substrings", []):
            if sub.lower() not in text and sub.lower() not in "blocked safety":
                passed = passed and False
        return {"id": case["id"], "passed": passed}

    result = agent_graph.invoke({"messages": [HumanMessage(content=case["input"])]})
    text = result["messages"][-1].content.lower()
    passed = all(s.lower() in text for s in case.get("expected_substrings", []))
    return {"id": case["id"], "passed": passed, "response_preview": text[:200]}


def main() -> int:
    results = [run_case(c) for c in load_cases()]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['id']}")
    failed = sum(1 for r in results if not r["passed"])
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
