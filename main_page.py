import streamlit as st

from plan import render_plan_tab
from chatbot import render_chat_tab
from llm_utils import list_local_models


def render_main_page() -> None:
    """Main page that shows either Plan OR Chatbot depending on sidebar selection."""

    # -------- Profile check -------- #
    if not st.session_state.get("profile"):
        st.warning("No profile found. Please fill the form first.")
        if st.button("Go to form"):
            st.session_state.page = "form"
            st.rerun()
        return

    # -------- Ensure models exist (only validation here) -------- #
    available_models = list_local_models()
    if not available_models:
        st.error(
            "No local models found. Make sure Ollama is running and at least one model "
            "has been pulled (e.g. `ollama pull llama3.2:3b`)."
        )
        return

    # keep a valid model in session (fallback)
    if "model_name" not in st.session_state or st.session_state["model_name"] not in available_models:
        st.session_state["model_name"] = available_models[0]

    # -------- Decide which view to show -------- #
    current_view = st.session_state.get("main_view", "plan")
    current_view = (current_view or "plan").lower()

    model_name = st.session_state.get("model_name")

    if current_view == "chat":
        render_chat_tab(model_name)
    else:
        render_plan_tab(model_name)

