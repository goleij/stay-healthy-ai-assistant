import streamlit as st

CHAT_CSS = """
<style>

/* =========================================================
   LINKE MENÜSPALTE (Hintergrund)
========================================================= */
div[data-testid="column"]:first-child,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {
  background-color: #E1EFE2 !important;
  border-radius: 14px !important;
  padding: 14px 12px !important;
}

/* =========================================================
   ALLGEMEINES BUTTON-STYLING (z.B. Send / Clear)
========================================================= */
div[data-testid="stButton"] {
  width: 100% !important;
  display: flex !important;
  justify-content: flex-start !important;
}

div[data-testid="stButton"] > button {
  background-color: #009245 !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 15px !important;
  min-height: 20px !important; 
  padding-top:    0.2rem;
  padding-bottom: 0.2rem;
  padding-left:   3rem;
  padding-right:  3rem;
  font-size: 0.95rem !important;
  font-weight: 700 !important;
  transition: all 0.2s ease-in-out !important;
}

/* Hover für die Standard-Buttons rechts */
div[data-testid="stButton"] > button:hover {
  background-color: #F5C400 !important;
  color: #ffffff !important;
}

/* =========================================================
   LINKE SPALTE: NUR KONTUR (New Chat & Chat-Liste)
========================================================= */

/* Selektiert Buttons nur in der linken Spalte */
div[data-testid="column"]:first-child div[data-testid="stButton"] > button,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button {
  background-color: transparent !important; 
  background: transparent !important;
  border: 2px solid #009245 !important;    /* Grüne Kontur */
  color: #009245 !important;               /* Grüner Text */
}

/* Zwingt den Text innerhalb dieser Buttons auf Grün */
div[data-testid="column"]:first-child div[data-testid="stButton"] > button p,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button p {
  color: #009245 !important;
}

/* HOVER & ACTIVE: Füllen mit Gelb, Text wird weiß */
div[data-testid="column"]:first-child div[data-testid="stButton"] > button:hover,
div[data-testid="column"]:first-child div[data-testid="stButton"] > button:active,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button:hover,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button:active {
  background-color: #F5C400 !important;
  border-color: #F5C400 !important;
  color: #ffffff !important;
}

/* Text-Farbe bei Hover in Weiß ändern */
div[data-testid="column"]:first-child div[data-testid="stButton"] > button:hover p,
div[data-testid="column"]:first-child div[data-testid="stButton"] > button:active p,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button:hover p,
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button:active p {
  color: #ffffff !important;
}

/* =========================================================
   SELECTBOX & INPUTS
========================================================= */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  background-color: #E1EFE2 !important;
  border-radius: 12px !important;
}

.stTextInput input {
  background-color: #E1EFE2 !important;
  color: #23233C !important;
  border: 1px solid #cfe3d3 !important;
  border-radius: 12px !important;
}

</style>
"""

def inject_chat_css() -> None:
    st.markdown(CHAT_CSS, unsafe_allow_html=True)