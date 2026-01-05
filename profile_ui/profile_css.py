import streamlit as st

PROFILE_CSS = """
<style>

/* ========================================================= */
/* Layout: Personal info grid */
/* ========================================================= */
.personal-info-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    align-items: start;
}
.personal-info-item { padding: 6px 0; }
.personal-info-label { font-size: 0.98rem; font-weight: 600; margin-bottom: 4px; }
.personal-info-value { font-size: 1.4rem; font-weight: 700; line-height: 1.05; }

@media (max-width: 700px) {
    .personal-info-grid { grid-template-columns: repeat(2, 1fr); }
    .personal-info-value { font-size: 1.15rem; }
}

/* ========================================================= */
/* File uploader */
/* ========================================================= */
[data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"] {
    display: none;
}

/* ========================================================= */
/* BUTTONS – green normal, yellow hover, white text */
/* ========================================================= */
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stButton"] button,
button[kind="primary"],
.stButton > button,
[data-testid="stFileUploader"] button {
    background-color: #009245 !important;
    border: 1px solid #009245 !important;
    color: #ffffff !important;
    box-shadow: none !important;
    
    border-radius: 20px !important;

    min-height: 30px !important;
    padding-top:    0.2rem;
    padding-bottom: 0.2rem;
    padding-left:   1.5rem;
    padding-right:  1.5rem;
    transition: background-color 150ms ease, border-color 150ms ease;
}

/* Hover */
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stButton"] button:hover,
button[kind="primary"]:hover,
.stButton > button:hover,
[data-testid="stFileUploader"] button:hover {
    background-color: #F5C400 !important;
    border-color: #F5C400 !important;
    color: #ffffff !important; /* stays white */
}

/* ========================================================= */
/* Inputs / Textareas / Selects background: #E1EFE2 */
/* ========================================================= */
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"],
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"],
div[data-baseweb="select"] > div {
    background-color: #E1EFE2 !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background-color: #E1EFE2 !important;
}

/* dropdown menu */
ul[role="listbox"] {
    background-color: #E1EFE2 !important;
}

/* multiselect tags */
span[data-baseweb="tag"] {
    background-color: #009245 !important;
    color: #ffffff !important;
}
span[data-baseweb="tag"] * {
    color: #ffffff !important;
}

/* ========================================================= */
/* REMOVE black outlines / replace focus with green */
/* ========================================================= */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="select"] > div {
    border: 1px solid #B7D8C0 !important;
    box-shadow: none !important;
    outline: none !important;
}

div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within > div,
div[data-baseweb="select"]:focus-within > div {
    border: 1px solid #009245 !important;
    box-shadow: 0 0 0 2px rgba(0,146,69,0.25) !important;
    outline: none !important;
}

div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}

/* ========================================================= */
/* Expander / Form border */
/* ========================================================= */
div[data-testid="stExpander"],
details[role="group"],
div[data-baseweb="expander"],
div[data-testid="stForm"] {
    border: 1px solid #B7D8C0 !important;
    box-shadow: none !important;
    border-radius: 8px !important;
    background: transparent !important;
}

/* ========================================================= */
/* Avatar */
/* ========================================================= */
.profile-avatar-circle {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid #e5e7eb;
    background: #E1EFE2;
    display: flex;
    align-items: center;
    justify-content: center;
}
.profile-avatar-circle img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.profile-avatar-empty {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    border: 1px dashed #d1d5db;
    background: #E1EFE2;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #6b7280 !important;
    text-align: center;
    padding: 8px;
}

</style>
"""

def inject_profile_css() -> None:
    st.markdown(PROFILE_CSS, unsafe_allow_html=True)
