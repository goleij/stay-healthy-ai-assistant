import streamlit as st

WISHBOARD_CSS = """
<style>

/* =========================================================
   BASE TEXT COLOR
========================================================= */
html, body, .stApp {
    color: #23233C !important;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}



/* =========================================================
   BIGGER LABEL "Write your wish..."
========================================================= */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p,
div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p {
    font-size: 15px !important;
    font-weight: 500 !important;
    color: #23233C !important;
    margin-bottom: 8px !important;
    line-height: 1.2 !important;
}

/* Entfernt extra Abstand innerhalb des Labels */
div[data-testid="stTextInput"] label p,
div[data-testid="stWidgetLabel"] p {
    margin: 0 !important;
}


/* =========================================================
   HEADER
========================================================= */




.wishboard-header {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 16px 0 20px;
}
.wishboard-title {
    display: flex;
    justify-content: center;
    align-items: center;
}

.wishboard-title svg {
    transform: translateY(2px);
}

/* =========================================================
   CHAT ROWS
========================================================= */
.chat-row {
    display: flex;
    width: 100%;
    margin: 14px 0;
}

.chat-user {
    justify-content: flex-end;
}

.chat-assistant {
    justify-content: flex-start;
}

/* User bubble */
.chat-bubble-user {
    max-width: 85%;
    background: #E1EFE2;
    color: #23233C !important;
    padding: 12px 14px;
    border-radius: 14px;
    border-bottom-right-radius: 4px;
    font-size: 15px;
    white-space: pre-wrap;
}

/* Assistant bubble */
.chat-bubble-assistant {
    max-width: 85%;
    background: #ffffff;
    color: #23233C !important;
    padding: 12px 14px;
    border-radius: 14px;
    border-bottom-left-radius: 4px;
    border: 1px solid #e6e6e6;
    font-size: 15px;
    white-space: pre-wrap;
}

/* =========================================================
   INPUT FIELD – LIGHT GREEN
========================================================= */
div[data-testid="stTextInput"] input,
.stTextInput input {
    background-color: #E1EFE2 !important;
    color: #23233C !important;

    border: 1px solid #cfe3d3 !important;
    border-radius: 12px !important;

    min-height: 48px !important;
    padding: 0.7rem 0.95rem !important;
    font-size: 16px !important;
}

div[data-testid="stTextInput"] input:focus,
.stTextInput input:focus {
    border-color: #009245 !important;
    box-shadow: 0 0 0 0.2rem rgba(0,146,69,0.15) !important;
    outline: none !important;
}

div[data-testid="stTextInput"] input::placeholder,
.stTextInput input::placeholder {
    color: rgba(35,35,60,0.55) !important;
}

/* =========================================================
   SEND BUTTON – GREEN
========================================================= */
div[data-testid="stButton"] > button {
    background-color: #009245 !important;
    color: #ffffff !important;

    border: none !important;
    border-radius: 20px !important;

    min-height: 30px !important;
    padding-top:    0.2rem;
    padding-bottom: 0.2rem;
    padding-left:   3rem;
    padding-right:  3rem;
    font-size: 16px !important;
    font-weight: 700 !important;

    box-shadow: none !important;
    outline: none !important;
    cursor: pointer !important;
}

/* Hover + Click = GELB */
div[data-testid="stButton"] > button:hover,
div[data-testid="stButton"] > button:active,
div[data-testid="stButton"] > button:focus-visible {
    background-color: #F5C400 !important;
    transform: translateY(1px);
}





</style>
"""

def inject_css():
    st.markdown(WISHBOARD_CSS, unsafe_allow_html=True)

def load_css():
    inject_css()

def apply_css():
    inject_css()
