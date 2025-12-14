# plan/plan_css.py
import streamlit as st

PLAN_CSS = """
<style>
/* Shopping list item style */
.shopping-item {
    padding: 8px 10px;
    margin: 4px 0;
    border-radius: 10px;
    background: #fdfdfd;
    border: 1px solid #ececec;
    font-size: 13px;
}
</style>
"""

# Simple & safe: just makes the radio look like pills, does not hide anything
PLAN_TOGGLE_CSS = """
<style>
/* Show Meals / Workout radios horizontally with some spacing */
div[data-testid="stRadio"] > div {
    display: flex;
    flex-direction: row;
    gap: 8px;
    margin-bottom: 16px;
}

/* Each option looks like a pill */
div[data-testid="stRadio"] label {
    border-radius: 999px;
    padding: 6px 18px;
    background: #f5f5f5;
    color: #777777;
    font-weight: 500;
    cursor: pointer;
    border: none;
}

/* Selected option: light green background and green text */
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
div[data-testid="stRadio"] label:has(input:checked) {
    background: #e4f4e8;
    color: #1f4f34;
}
</style>
"""


def inject_plan_css() -> None:
    """Inject general CSS for plan pages."""
    st.markdown(PLAN_CSS, unsafe_allow_html=True)


def inject_plan_toggle_css() -> None:
    """Inject CSS for the Meals / Workout pill toggle."""
    st.markdown(PLAN_TOGGLE_CSS, unsafe_allow_html=True)
