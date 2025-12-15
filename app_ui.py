import streamlit as st

from auth import show_auth_page
from landing import show_landing_page
from storage.profile_manager import (
    ensure_session_defaults,
    save_state_for_current_user,
)
from plan import render_user_form
from main_page import render_main_page
from profile_ui import render_profile_page
from profile_ui.Recepies.library_ui import render_library_page
from app_css import inject_sidebar_css
from meditation import render_meditation_page
from wishboard.wishboard_ui import render_wishboard_chat

st.set_page_config(
    page_title="Stay Healthy AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Auth / Landing ----------
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:

    stage = st.session_state.get("auth_stage", "landing")

    if stage == "landing":
        show_landing_page()
    else:
        show_auth_page()

    st.stop()

ensure_session_defaults()

# ---------- Disable everything during loading step ----------
if st.session_state.get("page") == "form" and st.session_state.get("onboarding_step") == 11:
    render_user_form()
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    inject_sidebar_css()

    st.markdown("### Profile")
    if st.button("Profile page", use_container_width=True, key="btn_profile_page"):
        st.session_state.page = "profile"
        save_state_for_current_user()
        st.rerun()

    st.markdown("---")

    if st.button("Chat", use_container_width=True, key="btn_chat"):
        st.session_state.page = "main"
        st.session_state["main_view"] = "chat"
        save_state_for_current_user()
        st.rerun()

    if st.button("Plan", use_container_width=True, key="btn_plan"):
        st.session_state.page = "main"
        st.session_state["main_view"] = "plan"
        save_state_for_current_user()
        st.rerun()

    if st.button("Shopping list", use_container_width=True, key="btn_shopping"):
        st.session_state.page = "library"
        save_state_for_current_user()
        st.rerun()

    if st.button("Meditation", use_container_width=True, key="btn_meditation"):
        st.session_state.page = "meditation"
        st.rerun()

    if st.button("Wish board", use_container_width=True, key="btn_wishboard"):
        st.session_state.page = "wishboard"
        st.rerun()

    st.markdown("---")

    if st.button("Settings", use_container_width=True, key="btn_settings"):
        st.session_state.page = "settings"
        st.rerun()

    if st.button("Logout", use_container_width=True, key="btn_logout"):
        st.session_state.clear()
        st.rerun()

# ---------- Page routing ----------
page = st.session_state.get("page", "form")

if page == "form":
    render_user_form()

elif page == "main":
    render_main_page()

elif page == "profile":
    render_profile_page()

elif page == "library":
    render_library_page()

elif page == "meditation":
    render_meditation_page()

elif page == "wishboard":
     render_wishboard_chat()

elif page == "settings":
    st.info("Settings page coming soon...")

else:
    st.session_state.page = "form"
    render_user_form()
