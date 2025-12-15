import streamlit as st

_CSS = """
/* ---------- Grundlayout ---------- */
.wishboard-header {
    text-align: center;
    padding-top: 8px;
    padding-bottom: 8px;
}

/* Jede Chat-Zeile */
.chat-row {
    display: flex !important;      /* Wichtig */
    width: 100%;
    margin: 12px 0;
}

/* User-Nachrichten (rechts) */
.chat-user {
    justify-content: flex-end !important;
}

/* KI-Nachrichten (links) */
.chat-assistant {
    justify-content: flex-start !important;
}

/* Bubble des Users */
.chat-bubble-user {
    max-width: 80%;
    background: #DCF8C6;   /* WhatsApp-Grün */
    color: #111;
    padding: 10px 14px;
    border-radius: 14px;
    border-bottom-right-radius: 2px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    font-size: 15px;
    white-space: pre-wrap; /* Zeilenumbrüche */
}

/* Bubble der KI */
.chat-bubble-assistant {
    max-width: 80%;
    background: #FFFFFF;
    color: #111;
    padding: 10px 14px;
    border-radius: 14px;
    border-bottom-left-radius: 2px;
    border: 1px solid #e6e6e6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    font-size: 15px;
    white-space: pre-wrap; /* Zeilenumbrüche */
}

/* Chat-Container Padding */
.chat-container {
    padding: 10px 14px;
}

/* Eingabefeld schöner */
input[type=text] {
    border-radius: 10px !important;
    padding: 8px !important;
}

/* Senden-Button */
button[kind="secondary"] {
    border-radius: 10px !important;
}
"""

def inject_css() -> None:
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)

def load_css() -> None:
    inject_css()

def apply_css() -> None:
    inject_css()

def local_css() -> None:
    inject_css()
