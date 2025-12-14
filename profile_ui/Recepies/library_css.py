# profile/library_css.py
import streamlit as st

LIBRARY_CSS = """
<style>
/* Custom CSS for the Recipes & Shopping Lists page.
   Add your layout and style rules here later. */
</style>
"""


def inject_library_css() -> None:
    """Inject custom CSS for the library page."""
    st.markdown(LIBRARY_CSS, unsafe_allow_html=True)
