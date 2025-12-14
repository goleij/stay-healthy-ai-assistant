import streamlit as st

from plan import render_plan_tab
from chatbot import render_chat_tab
from llm_utils import list_local_models


def render_main_page() -> None:
    """Main page with model selection and either Plan OR Chatbot (no tabs)."""
    st.title("AI Lifestyle Coach")

    # -------- Profile check -------- #
    if not st.session_state.get("profile"):
        st.warning("No profile found. Please fill the form first.")
        if st.button("Go to form"):
            st.session_state.page = "form"
            st.rerun()
        return

    # -------- Model selection -------- #
    available_models = list_local_models()
    if not available_models:
        st.error(
            "No local models found. Make sure Ollama is running and at least one model "
            "has been pulled (e.g. `ollama pull llama3.2:3b`)."
        )
        return

    default_model = st.session_state.get("model_name") or available_models[0]
    try:
        default_index = available_models.index(default_model)
    except ValueError:
        default_index = 0

    model_name = st.selectbox(
        "Choose a model:",
        available_models,
        index=default_index,
        key="model_select_main",
    )
    st.session_state["model_name"] = model_name

    st.write("")

    # -------- Decide which view to show (Plan OR Chatbot) -------- #
    # this is set in app_ui.py when user clicks "Chat" or "Plan"
    current_view = st.session_state.get("main_view", "plan")
    current_view = (current_view or "plan").lower()

    if current_view == "chat":
        # Only chatbot
        render_chat_tab(model_name)
    else:
        # Only plan
        render_plan_tab(model_name)
