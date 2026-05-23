"""Streamlit UI entry point."""

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from config import get_settings
from graph import agent_graph
from observability.langfuse_client import trace_chat_turn

st.set_page_config(page_title="Ecommerce AI Agent", page_icon="🛒", layout="wide")

st.title("🛒 Ecommerce Support Agent")
st.caption("Catalog · Orders · Returns — powered by LangGraph")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask about products, orders, or returns…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    lc_messages = [
        HumanMessage(content=m["content"])
        if m["role"] == "user"
        else AIMessage(content=m["content"])
        for m in st.session_state.messages
    ]

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m["role"] in ("user", "assistant")
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            with trace_chat_turn(
                prompt,
                history=history,
                metadata={"provider": get_settings().llm_provider},
            ) as trace:
                result = agent_graph.invoke({"messages": lc_messages})

                last = result["messages"][-1]
                reply = last.content if hasattr(last, "content") else str(last)
                tool_calls = getattr(last, "tool_calls", None) or []
                output: dict = {"assistant_message": reply}
                if tool_calls:
                    output["tool_calls"] = [
                        tc if isinstance(tc, dict) else getattr(tc, "name", str(tc))
                        for tc in tool_calls
                    ]
                trace.complete(output)

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

with st.sidebar:
    st.header("About")
    st.markdown(
        """
        **Example prompts**
        - Show me wireless mice
        - Status of order ORD-12345
        - Can I return order ORD-55566?
        """
    )
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
