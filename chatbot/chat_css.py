# chat/chat_css.py
import streamlit as st

CHAT_CSS = """
<style>
/* --- Chat layout: sidebar + main area --- */

.chat-sidebar-card,
.chat-main-card {
    background: transparent;
    border-radius: 0;
    border: none;
    box-shadow: none;
    padding: 0;
    margin-top: 0.5rem;
}

/* Sidebar title + subtitle */
.chat-sidebar-title {
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
}
.chat-sidebar-subtitle {
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 0.6rem;
}

/* Sidebar chat list buttons */
.chat-sidebar-list .stButton > button {
    width: 100%;
    border-radius: 999px;
    border: 0;
    margin-bottom: 0.35rem;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    font-size: 0.9rem;
    text-align: left;
    padding: 0.35rem 0.75rem;
}
.chat-sidebar-list .stButton > button:hover {
    background: #e0f2fe;
}

/* Main header + description */
.chat-main-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.2rem;
}
.chat-main-header span {
    font-size: 1.1rem;
    font-weight: 600;
}
.chat-main-description {
    font-size: 0.9rem;
    color: #64748b;
    margin-bottom: 0.8rem;
}

/* Buttons inside main chat card (clear, send, tools) */
.chat-main-card .stButton > button {
    border-radius: 999px;
    padding: 0.25rem 0.9rem;
    font-size: 0.9rem;
}

</style>
"""


def inject_chat_css() -> None:
    """Inject custom CSS for the chat tab."""
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
