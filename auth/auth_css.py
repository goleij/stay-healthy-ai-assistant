# auth/auth_css.py
import streamlit as st

AUTH_CSS = """
<style>
/* Optional: slightly center and style auth area */
.block-container {
    max-width: 500px;
}

/* Button styling */
.stButton > button {
    width: 100%;
    border-radius: 999px;
    font-weight: 600;
}

/* Small tweaks for inputs and headings */
h1, h2, h3 {
    text-align: center;
}
</style>
"""


def inject_auth_css():
    """Inject custom CSS for the auth page."""
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
