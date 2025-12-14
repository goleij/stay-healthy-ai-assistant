import streamlit as st

MEDITATION_CSS = """
<style>

.stApp .main > div {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
}

.meditation-text {
    line-height: 1.7;
    font-size: 1.1rem;
}

/* Navigation Tabs */
.button-tab {
    padding: 8px 16px;
    border-radius: 10px;
    border: 1px solid #ddd;
    margin-right: 8px;
    cursor: pointer;
    background-color: #f8f9fa;
}
.button-tab:hover {
    background-color: #e9ecef;
}

/* SELECTED button */
.button-tab.selected {
    background-color: #007bff;
    color: white !important;
    border-color: #007bff;
    font-weight: 600;
}

.stButton > button {
    border-radius: 12px;
}

</style>
"""

def inject_meditation_css():
    st.markdown(MEDITATION_CSS, unsafe_allow_html=True)
