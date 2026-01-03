# auth/auth_css.py
import streamlit as st

AUTH_CSS = """
<style>

/* Make Streamlit header/toolbar transparent (removes white top bar) */
header[data-testid="stHeader"]{
  background: transparent !important;
}

div[data-testid="stToolbar"]{
  background: transparent !important;
}

/* Make the main page background transparent so waves are visible */
.stApp,
.stAppViewContainer,
.stMain,
.stMainBlockContainer,
section.main,
section.main > div{
  background: transparent !important;
}

/* --- Background waves (top & bottom) --- */

.auth-bg-top{
  top: 0;
  height: 200px;          /* mehr Platz */
  overflow: visible;      /* nicht abschneiden */
}

.auth-bg-top svg{
  transform: translateY(-40px);
}


.auth-bg-top,
.auth-bg-bottom{
  position: fixed;
  left: 0;
  width: 100vw;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}


.auth-bg-bottom{ bottom: 0; height: 150px; }  /* oder bottom:-40px */

/* Make SVG fill the container width */
.auth-bg-top svg,
.auth-bg-bottom svg{
  width: 110vw;
  max-width: none;
  height: 100%;
  display: block;
}

/* Keep content above + make room for bottom wave */
.block-container{
  position: relative;
  z-index: 1;
  padding-bottom: 260px;
}

/* Optional: prevent horizontal scrollbar */
html, body{ overflow-x: hidden; }





/* =========================================================
   VARIABLES
========================================================= */
:root{
  --text: #23233C;
  --primary: #009245;
  --primary-hover: #F5C400;
  --input-bg: #E1EFE2;
  --input-border: #cfe3d3;

  --fs-h1: 1.8rem;
  --fs-h2: 1.3rem;
  --fs-h3: 1.1rem;
  --fs-label: 0.85rem;
  --fs-text: 0.9rem;
}

/* =========================================================
   BASE LAYOUT
========================================================= */
.block-container{
  max-width: 500px;
}

html, body, .stApp{
  color: var(--text);
  font-size: var(--fs-text);
}

/* =========================================================
   HEADINGS
========================================================= */
h1{ font-size: var(--fs-h1); text-align: center; }
h2{ font-size: var(--fs-h2); text-align: center; }
h3{ font-size: var(--fs-h3); text-align: center; }

/* Center helper text like "Don't have an account?" */
div[data-testid="stMarkdownContainer"] p{
  text-align: center;
}

/* =========================================================
   FORM
========================================================= */
.stForm{

  border-radius: 12px;
}

/* =========================================================
   LABELS
========================================================= */
.stTextInput label{
  font-size: var(--fs-label);
  font-weight: 600;
  color: var(--text) !important;
}

/* =========================================================
   INPUTS
========================================================= */
.stTextInput input{
  background-color: var(--input-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--input-border) !important;
  border-radius: 10px !important;
  min-height: 44px !important;
  padding: 0.55rem 0.9rem !important;
}

.stTextInput input:focus{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 0.2rem rgba(0,146,69,0.15) !important;
  outline: none !important;
}




/* =========================================================
   🔴 BUTTON STYLE (LOGIN + CREATE ACCOUNT)
========================================================= */
div[data-testid="stElementContainer"]{
  width: 100% !important;
}

div[data-testid="stFormSubmitButton"],
div[data-testid="stButton"]{
  width: 100% !important;
  display: flex !important;
  justify-content: center !important;
}

div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stButton"] > button{
  width: 100% !important;
  max-width: 420px !important;
  margin: 0.75rem 0 0 0 !important;

  min-height: 44px !important;
  padding: 0.6rem 1.25rem !important;

  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;

  font-weight: 700 !important;
  border-radius: 999px !important;

  background-color: var(--primary) !important;
  color: #ffffff !important;
  border: none !important;

  cursor: pointer !important;
}

/* =========================================================
   HOVER
========================================================= */
.stButton > button:hover,
.stFormSubmitButton button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
.stForm button[type="submit"]:hover{
  background-color: var(--primary-hover) !important;
  color: var(--text) !important;
}

/* =========================================================
   FOCUS
========================================================= */
.stButton > button:focus,
.stFormSubmitButton button:focus,
div[data-testid="stFormSubmitButton"] button:focus,
.stForm button[type="submit"]:focus{
  outline: 2px solid rgba(245,196,0,0.6) !important;
  outline-offset: 2px !important;
}

/* =========================================================
   PASSWORD EYE (NEUTRAL)
========================================================= */
.stTextInput button{
  background: transparent !important;
  color: var(--text) !important;
  border: none !important;
  padding: 0.25rem !important;
}

/* Divider */
hr{ margin: 1.25rem 0; }


div[data-testid="stForm"]{
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
}

div[data-testid="stForm"] div[data-testid="stFormSubmitButton"]{
  width: 100% !important;
  display: flex !important;
  justify-content: center !important;
}

div[data-testid="stFormSubmitButton"] > button{
  width: auto !important;
  max-width: none !important;
  min-width: 140px !important;
  padding: 0.4rem 1.2rem !important;
  min-height: 36px !important;
}


</style>
"""

def inject_auth_css():
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown('''
<div class="auth-bg-top">
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="426.346" height="205.887" viewBox="0 0 426.346 205.887" preserveAspectRatio="none">
  
  <g>
    <path d="M-.33,497.483s140.7-134.181,304.313-85.721S560.864-6.2,560.864-6.2L536.517,756.867-8.455,750.7Z" transform="translate(284.703 619.672) rotate(-155)" fill="#009245" opacity="0.16"/>
    <path d="M1.071,373.166s140.7-134.181,304.313-85.721S530.827-5.868,530.827-5.868l7.09,638.418L-7.055,626.382Z" transform="translate(367.723 485.569) rotate(-155)" fill="#009245"/>
  </g>
</svg>


</div>
<div class="auth-bg-bottom">
 
 <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="200" viewBox="0 0 414 198" preserveAspectRatio="none">
    <g>
        <path d="M1.681,786.1s137.4-128.75,294.973-84.552,220.989-280.56,220.989-280.56v605.319H-8.888Z" transform="translate(-20.721 -630.787)" fill="#009245" opacity="0.16"/>
        <path d="M1.681,786.1s137.4-128.75,294.973-84.552,220.989-280.56,220.989-280.56v605.319H-8.888Z" transform="translate(-24.289 -602.249)" fill="#009245"/>
    </g>
  </svg>
</div>
''', unsafe_allow_html=True)