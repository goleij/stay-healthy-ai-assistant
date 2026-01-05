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
from meditation import render_meditation_page
from wishboard.wishboard_ui import render_wishboard_chat

from app_css import inject_app_css


# =========================================================
# PAGE CONFIG (MUST BE FIRST)
# =========================================================
st.set_page_config(
    page_title="Stay Healthy AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_app_css()


# =========================================================
# AUTH / LANDING
# =========================================================
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    stage = st.session_state.get("auth_stage", "landing")
    if stage == "landing":
        show_landing_page()
    else:
        show_auth_page()
    st.stop()


# =========================================================
# SESSION DEFAULTS
# =========================================================
ensure_session_defaults()


# =========================================================
# HELPERS: map page-state <-> sidebar label
# =========================================================
MENU_ITEMS = [
    "Profile page",
    "Chat",
    "Plan",
    "Shopping list",
    "Meditation",
    "Wish board",
    "Settings",
    "Logout",
]


def _page_to_menu(page: str | None, main_view: str | None) -> str:
    """Which sidebar item should be selected for the current page?"""
    if page == "profile":
        return "Profile page"
    if page == "library":
        return "Shopping list"
    if page == "meditation":
        return "Meditation"
    if page == "wishboard":
        return "Wish board"
    if page == "settings":
        return "Settings"
    if page == "main":
        return "Chat" if (main_view or "plan").lower() == "chat" else "Plan"

    # page == "form" (onboarding) or unknown:
    # keep last chosen menu so radio doesn't jump around
    return st.session_state.get("_last_menu", "Profile page")


def _apply_menu(menu: str) -> None:
    """Apply routing based on sidebar selection."""
    if menu == "Profile page":
        st.session_state.page = "profile"

    elif menu == "Chat":
        st.session_state.page = "main"
        st.session_state["main_view"] = "chat"

    elif menu == "Plan":
        st.session_state.page = "main"
        st.session_state["main_view"] = "plan"

    elif menu == "Shopping list":
        st.session_state.page = "library"

    elif menu == "Meditation":
        st.session_state.page = "meditation"

    elif menu == "Wish board":
        st.session_state.page = "wishboard"

    elif menu == "Settings":
        st.session_state.page = "settings"

    elif menu == "Logout":
        st.session_state.clear()
        st.rerun()


# =========================================================
# DISABLE EVERYTHING DURING FINAL ONBOARDING STEP
# =========================================================
if (
    st.session_state.get("page") == "form"
    and st.session_state.get("onboarding_step") == 11
):
    render_user_form()
    st.stop()


# =========================================================
# SIDEBAR – STABLE + REFLECT CURRENT PAGE
# =========================================================
current_page = st.session_state.get("page", "form")
current_main_view = st.session_state.get("main_view", "plan")

default_menu = _page_to_menu(current_page, current_main_view)
default_index = MENU_ITEMS.index(default_menu) if default_menu in MENU_ITEMS else 0

with st.sidebar:
    menu = st.radio(
        "",
        MENU_ITEMS,
        index=default_index,
        key="sidebar_menu",
        label_visibility="collapsed",
    )

# remember last menu choice (helps keep sidebar stable during onboarding/form)
st.session_state["_last_menu"] = menu


# =========================================================
# HANDLE NAVIGATION (works also during onboarding/form)
# =========================================================
# Always allow logout
if menu == "Logout":
    _apply_menu(menu)

else:
    # If user is in onboarding ("form") and chooses another menu item,
    # allow leaving the form and reset the wizard so it starts clean next time.
    if st.session_state.get("page") == "form":
        # Leaving onboarding -> reset step so it doesn't resume mid-way later
        st.session_state.onboarding_step = 0
        _apply_menu(menu)
        st.rerun()
    else:
        _apply_menu(menu)

save_state_for_current_user()


# =========================================================
# PAGE ROUTING
# =========================================================
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
