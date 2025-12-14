# storage/profile_manager.py
import os
import streamlit as st
from .file_utils import load_json, save_json

# Root directory = folder where app_ui.py is
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

USERS_FILE = os.path.join(ROOT_DIR, "users.json")
PROFILES_FILE = os.path.join(ROOT_DIR, "profiles.json")


# -------- Users helpers -------- #
def load_users() -> dict:
    """Load users from users.json."""
    return load_json(USERS_FILE)


def save_users(users: dict):
    """Save users to users.json."""
    save_json(USERS_FILE, users)


# -------- Profiles/helpers -------- #
def load_profiles() -> dict:
    """Load user profiles (per-user state)."""
    return load_json(PROFILES_FILE)


def save_profiles(profiles: dict):
    """Save user profiles."""
    save_json(PROFILES_FILE, profiles)


def ensure_session_defaults():
    """Ensure base keys exist in session_state."""
    if "page" not in st.session_state:
        st.session_state.page = "form"
    if "profile" not in st.session_state:
        st.session_state.profile = {}
    if "plan_text" not in st.session_state:
        st.session_state.plan_text = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def load_state_for_user(username: str):
    """Load saved state for a given username into session_state."""
    profiles = load_profiles()
    data = profiles.get(username, {})

    st.session_state.page = data.get("page", "form")
    st.session_state.profile = data.get("profile", {})
    st.session_state.plan_text = data.get("plan_text")
    st.session_state.chat_history = data.get("chat_history", [])


def save_state_for_current_user():
    """Save current session_state for the logged-in user."""
    username = st.session_state.get("username")
    if not username:
        return

    profiles = load_profiles()
    profiles[username] = {
        "page": st.session_state.get("page", "form"),
        "profile": st.session_state.get("profile", {}),
        "plan_text": st.session_state.get("plan_text"),
        "chat_history": st.session_state.get("chat_history", []),
    }
    save_profiles(profiles)
