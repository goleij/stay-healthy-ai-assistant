# plan/plan_css.py
import streamlit as st

PLAN_CSS = """
<style>
/* =========================================================
   TEXT – ONLY PLAN CONTENT (NO GLOBAL / SIDEBAR IMPACT)
========================================================= */
.stMarkdown,
.stMarkdown p,
.stMarkdown span,
.stMarkdown li,
.stExpander,
.stExpander p,
.stExpander li,
.stExpander summary,
.stRadio label {
    color: #23233C !important;
}

/* =========================================================
   VOICE MODE BUTTON — PERFECT PILL
========================================================= */
.stButton > button {
    border: 2px solid #009245 !important;   /* default green */
    background: transparent !important;

    
    padding: 0 !important;


    border-radius: 20px !important;

    min-height: 30px !important;
    padding-top:    0.2rem;
    padding-bottom: 0.2rem;
    padding-left:   1.5rem;
    padding-right:  1.5rem;

    box-shadow: none !important;
    outline: none !important;

    transition: border-color 0.15s ease;
}

/* Inner wrapper */
.stButton > button > div {
    
    border-radius: 20px !important;
    min-height: 30px !important;
    padding-top:    0.2rem;
    padding-bottom: 0.2rem;
    padding-left:   1.5rem;
    padding-right:  1.5rem;

    font-size: 14px !important;
    font-weight: 600 !important;
    color: #23233C !important;

    background: transparent !important;
    border: none !important;
    box-shadow: none !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    transition: background-color 0.15s ease, color 0.15s ease;
}

/* ---------------- HOVER ---------------- */
.stButton > button:hover {
    border-color: #F5C400 !important;       /* border yellow */
}

.stButton > button:hover > div {
    background-color: #F5C400 !important;  /* yellow bg */
}

/* FORCE TEXT TO WHITE (fix) */
.stButton > button:hover > div,
.stButton > button:hover > div * {
    color: #ffffff !important;
}

/* ---------------- ACTIVE / CLICK ---------------- */
.stButton > button:active,
.stButton > button:focus,
.stButton > button:focus-visible {
    border-color: #F5C400 !important;
}

.stButton > button:active > div,
.stButton > button:focus > div,
.stButton > button:focus-visible > div {
    background-color: #F5C400 !important;
}

/* FORCE TEXT TO WHITE (active) */
.stButton > button:active > div,
.stButton > button:active > div *,
.stButton > button:focus > div,
.stButton > button:focus > div *,
.stButton > button:focus-visible > div,
.stButton > button:focus-visible > div * {
    color: #ffffff !important;
}

/* Remove focus artifacts */
.stButton > button:focus,
.stButton > button:focus-visible,
.stButton > button:active,
.stButton > button > div:focus,
.stButton > button > div:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

/* =========================================================
   DAY EXPANDERS — FULL STRIP STYLE
========================================================= */
.stExpander details {
    border: none !important;
    border-radius: 16px !important;
    padding: 0 !important;
    margin-bottom: 14px !important;

    background: #E1EFE2 !important;
    overflow: hidden !important;
    box-shadow: none !important;
}

.stExpander summary {
    padding: 14px 18px !important;
    font-size: 18px !important;
    font-weight: 700 !important;

    cursor: pointer !important;
    list-style: none !important;
    background: #E1EFE2 !important;
}

.stExpander details:hover summary {
    background: rgba(225, 239, 226, 0.9) !important;
}

/* Content area */
.stExpander details[open] .streamlit-expanderContent {
    background: #ffffff !important;
}

/* =========================================================
   SHOPPING ITEM
========================================================= */
.shopping-item {
    padding: 8px 10px;
    margin: 4px 0;
    border-radius: 10px;
    background: #fdfdfd;
    border: 1px solid #ececec;
    font-size: 13px;
    color: #23233C !important;
}
</style>
"""

PLAN_TOGGLE_CSS = """
<style>
/* =========================================================
   MEALS / WORKOUT PILLS
========================================================= */
div[data-testid="stRadio"] > div {
    display: flex;
    flex-direction: row;
    gap: 12px;
    margin-bottom: 18px;
}

div[data-testid="stRadio"] label {
    border-radius: 999px !important;
    padding: 8px 20px !important;

    background: transparent !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #23233C !important;

    cursor: pointer !important;
    border: 2px solid #009245 !important;
}

/* Selected */
div[data-testid="stRadio"] label:has(input:checked) {
    background: rgba(0, 146, 69, 0.18) !important;
}

/* Remove focus artifacts */
div[data-testid="stRadio"] label:focus,
div[data-testid="stRadio"] label:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}
</style>
"""

def inject_plan_css() -> None:
    st.markdown(PLAN_CSS, unsafe_allow_html=True)

def inject_plan_toggle_css() -> None:
    st.markdown(PLAN_TOGGLE_CSS, unsafe_allow_html=True)
