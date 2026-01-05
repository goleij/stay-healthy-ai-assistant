# wishboard_ui.py

import os
import html
import json
import re
import streamlit as st
import textwrap
from . import wishboard_css as css


# ---------------------------------------------------------
# Profil laden
# ---------------------------------------------------------
def load_user_profile(username: str) -> dict:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(base_dir, "..", "profiles.json")

        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get(username, {}).get("profile", {})
    except Exception:
        return {}


# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------
def _normalize_list(x) -> list[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str):
        s = x.strip()
        return [s] if s else []
    return [str(x).strip()]


def _normalize_allergies(profile: dict) -> list[str]:
    items = _normalize_list(profile.get("allergies", ""))
    out = []
    for it in items:
        for part in re.split(r"[,;/|]+", it):
            p = part.strip().lower()
            if p:
                out.append(p)
    return list(dict.fromkeys(out))


def _get_conditions(profile: dict) -> list[str]:
    items = _normalize_list(profile.get("health_conditions"))
    issues = str(profile.get("health_issues", "") or "").strip()
    if issues:
        items.append(issues)

    out = []
    for it in items:
        for part in re.split(r"[,;/|]+", it):
            p = part.strip().lower()
            if p:
                out.append(p)
    return list(dict.fromkeys(out))


# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------
def _ensure_state() -> None:
    if "wishboard_chat" not in st.session_state:
        st.session_state["wishboard_chat"] = []
    if "wishboard_input" not in st.session_state:
        st.session_state["wishboard_input"] = ""


def _add_user_message(text: str):
    st.session_state["wishboard_chat"].append({"role": "user", "text": text})


def _add_assistant_message(text: str):
    st.session_state["wishboard_chat"].append({"role": "assistant", "text": text})


# ---------------------------------------------------------
# Simple assistant reply (placeholder)
# ---------------------------------------------------------
def _generate_assistant_reply(user_text: str) -> str:
    return f"✨ Dein Wunsch wurde gespeichert:\n\n**{user_text}**"


# ---------------------------------------------------------
# Button callback
# ---------------------------------------------------------
def _on_send_click():
    text = st.session_state["wishboard_input"].strip()
    if not text:
        return

    _add_user_message(text)
    reply = _generate_assistant_reply(text)
    _add_assistant_message(reply)

    st.session_state["wishboard_input"] = ""


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
def render_wishboard_chat() -> None:
    css.load_css()
    _ensure_state()

    # -----------------------------------------------------
    # BIG GREEN GIFT ICON
    # -----------------------------------------------------
    gift_svg = """
    <svg xmlns="http://www.w3.org/2000/svg"
         width="80" height="80" viewBox="0 0 24 24"
         fill="none" stroke="#009245" stroke-width="2.2"
         stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="8" width="18" height="4" rx="1"/>
      <path d="M12 8v13"/>
      <path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/>
      <path d="M7.5 8a2.5 2.5 0 0 1 0-5A4.8 8 0 0 1 12 8a4.8 8 0 0 1 4.5-5 2.5 2.5 0 0 1 0 5"/>
    </svg>
    """

    st.markdown(
        f"""<div class="wishboard-header">
      <h2 class="wishboard-title">{gift_svg}</h2>
    </div>""",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Chat messages
    # -----------------------------------------------------
    for msg in st.session_state["wishboard_chat"]:
        role = msg["role"]
        if role == "user":
            text = html.escape(msg["text"]).replace("\n", "<br>")
            bubble_class = "chat-bubble-user"
            row_class = "chat-row chat-user"
        else:
            text = msg["text"]
            bubble_class = "chat-bubble-assistant"
            row_class = "chat-row chat-assistant"

        st.markdown(
            f'<div class="{row_class}"><div class="{bubble_class}">{text}</div></div>',
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # Input + Button
    # -----------------------------------------------------
    st.text_input(
        "Write your wish...",
        key="wishboard_input",
        placeholder="z.B. 'I want chips or low-carb chocolate muffins.'",
    )

    st.button("Send", on_click=_on_send_click)


# ---------------------------------------------------------
# Public entry points
# ---------------------------------------------------------
def render_wishboard_page():
    render_wishboard_chat()


def app():
    render_wishboard_chat()


if __name__ == "__main__":
    app()
