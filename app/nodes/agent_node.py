"""LLM reasoning node with tool binding."""

from langchain_core.messages import AIMessage, SystemMessage

from config import get_settings
from prompts.system_prompt import SYSTEM_PROMPT
from state import AgentState
from observability.langfuse_client import trace_llm_generation, traced_node
from utils.llm_errors import log_llm_error, user_message_for_llm_error
from utils.llm_factory import build_agent_llm, is_llm_configured, llm_config_hint
from utils.logger import get_logger

logger = get_logger(__name__)


@traced_node("agent")
def agent_node(state: AgentState) -> AgentState:
    settings = get_settings()
    llm = build_agent_llm(settings)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]

    if llm is None or not is_llm_configured(settings):
        reply = AIMessage(
            content=f"{llm_config_hint(settings)} You can still use tools via tests."
        )
        return {**state, "messages": [reply], "next_node": "end"}

    model_name = (
        settings.openai_model
        if settings.llm_provider == "openai"
        else settings.gemini_model
    )

    try:
        with trace_llm_generation(
            name="agent_llm",
            model=model_name,
            messages=messages,
            metadata={"provider": settings.llm_provider},
        ) as gen_trace:
            response = llm.invoke(messages)
            gen_trace.complete(
                {
                    "content": response.content,
                    "tool_calls": response.tool_calls or [],
                }
            )
    except Exception as exc:
        log_llm_error(exc, provider=settings.llm_provider)
        reply = AIMessage(content=user_message_for_llm_error(exc))
        return {**state, "messages": [reply], "next_node": "end"}

    logger.info(
        "Agent response provider=%s tool_calls=%s",
        settings.llm_provider,
        bool(response.tool_calls),
    )

    next_node = "tools" if response.tool_calls else "validation"
    return {
        **state,
        "messages": [response],
        "tool_calls": response.tool_calls or [],
        "next_node": next_node,
    }
