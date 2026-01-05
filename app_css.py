import streamlit as st

APP_CSS = """
<style>

/* =========================================================
   HEADER + BACKGROUND TRANSPARENT
========================================================= */
header[data-testid="stHeader"],
div[data-testid="stToolbar"]{
  background: transparent !important;
}

.stApp,
.stAppViewContainer,
.stMain,
.stMainBlockContainer,
section.main,
section.main > div{
  background: transparent !important;
}

html, body{
  overflow-x: hidden;
}

/* =========================================================
   VARIABLES
========================================================= */
:root{
  --text: #23233C;
  --primary: #009245;
  --hover: #F5C400;
  --fs-text: 14px;

  /* Sidebar text size */
  --sidebar-h2: 16px;
}

/* =========================================================
   GLOBAL TEXT
========================================================= */
html, body, .stApp{
  color: var(--text);
  font-size: var(--fs-text);
}

/* =========================================================
   INFO / ALERT TEXT COLOR (e.g. Settings page)
========================================================= */
div[data-testid="stAlert"],
div[data-testid="stAlert"] p{
  color: #23233C !important;
}

/* =========================================================
   WAVES BACKGROUND (NOW FOREGROUND OVERLAY)
========================================================= */
.app-bg-top,
.app-bg-bottom{
  position: fixed;
  left: 0;
  width: 100vw;
  z-index: 50;            /* <-- Wellen in den Vordergrund */
  pointer-events: none;   /* Klicks gehen durch die Wellen durch */
  overflow: hidden;
}

.app-bg-top{
  top: 0;
  height: 200px;
}

.app-bg-top svg{
  transform: translateY(-40px);
}

.app-bg-bottom{
  bottom: 0;
  height: 150px;
}

.app-bg-top svg,
.app-bg-bottom svg{
  width: 110vw;
  max-width: none;
  height: 100%;
  display: block;
}

/* =========================================================
   CONTENT POSITIONING (MOVE DOWN)
========================================================= */
.block-container{
  position: relative;
  z-index: 1;

  /* Push content down away from top waves */
  padding-top: 120px;
  padding-bottom: 260px;
}

/* =========================================================
   SIDEBAR TOGGLE (HAMBURGER ALWAYS VISIBLE)
========================================================= */

/* Sidebar closed */
div[data-testid="collapsedControl"]{
  position: fixed !important;
  top: 0.9rem !important;
  left: 0.9rem !important;
  z-index: 99999 !important;

  background: rgba(0,146,69,0.95) !important;
  border-radius: 12px !important;
  padding: 0.3rem 0.4rem !important;
  box-shadow: 0 6px 20px rgba(0,0,0,0.14) !important;
}

div[data-testid="collapsedControl"] button{
  display: inline-flex !important;
  background: transparent !important;
  border: none !important;
}

div[data-testid="collapsedControl"] svg,
div[data-testid="collapsedControl"] svg *{
  fill: #ffffff !important;
  stroke: #ffffff !important;
  color: #ffffff !important;
}


/* Sidebar open */
button[data-testid="stSidebarCollapseButton"]{
  display: inline-flex !important;
  background: rgba(0,146,69,0.95) !important;
  border-radius: 12px !important;
  padding: 0.3rem 0.4rem !important;
  box-shadow: 0 6px 20px rgba(0,0,0,0.14) !important;
}

button[data-testid="stSidebarCollapseButton"] svg,
button[data-testid="stSidebarCollapseButton"] svg *{
  fill: #ffffff !important;
  stroke: #ffffff !important;
  color: #ffffff !important;
}


/* =========================================================
   SIDEBAR – MENU STYLE
========================================================= */
[data-testid="stSidebar"]{
  background-color: var(--primary) !important;
  padding-top: 1.6rem;
}

/* Hide only real Streamlit buttons */
[data-testid="stSidebar"] .stButton > button{
  display: none !important;
}

/* Force vertical menu */
[data-testid="stSidebar"] div[role="radiogroup"]{
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  gap: 0 !important;
}

/* Each menu row */
[data-testid="stSidebar"] div[role="radiogroup"] > label{
  width: 100% !important;
  background: transparent !important;
  border: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Hide radio circle */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child{
  display: none !important;
}



/* Menu text */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child,
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child *{
  color: #ffffff !important;
  font-size: var(--sidebar-h2) !important;
  font-weight: 600 !important;
  margin: 0.4rem 0 !important;
  padding-left: 0.9rem !important;
  position: relative !important;
  display: inline-block !important;
  width: fit-content !important;
  cursor: pointer !important;
  line-height: 1.2 !important;
}

/* Hover underline – exact word width */
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover > div:last-child::after{
  content: "";
  position: absolute;
  left: 2.3rem;
  bottom: -1px;
  width: 100%;
  height: 2px;
  background-color: var(--hover);
}

/* Active underline – exact word width */
[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div::after{
  content: "";
  position: absolute;
  left: 2.3rem;
  bottom: -1px;
  width: 100%;
  height: 2px;
  background-color: var(--hover);
}

/* Divider before Settings */
[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-last-child(2){
  margin-top: 1.4rem !important;
  padding-top: 1.4rem !important;
  border-top: 1px solid rgba(255,255,255,0.25) !important;
}






</style>
"""

APP_WAVES_HTML = """
<div class="app-bg-top">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 426.346 205.887" preserveAspectRatio="none">
  <g>
    <path d="M-.33,497.483s140.7-134.181,304.313-85.721
             S560.864-6.2,560.864-6.2L536.517,756.867-8.455,750.7Z"
          transform="translate(284.703 619.672) rotate(-155)"
          fill="#009245" opacity="0.16"/>
    <path d="M1.071,373.166s140.7-134.181,304.313-85.721
             S530.827-5.868,530.827-5.868l7.09,638.418L-7.055,626.382Z"
          transform="translate(367.723 485.569) rotate(-155)"
          fill="#009245"/>
  </g>
</svg>
</div>

<div class="app-bg-bottom">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 414 198" preserveAspectRatio="none">
  <g>
    <path d="M1.681,786.1s137.4-128.75,294.973-84.552
             s220.989-280.56,220.989-280.56v605.319H-8.888Z"
          transform="translate(-20.721 -630.787)"
          fill="#009245" opacity="0.16"/>
    <path d="M1.681,786.1s137.4-128.75,294.973-84.552
             s220.989-280.56,220.989-280.56v605.319H-8.888Z"
          transform="translate(-24.289 -602.249)"
          fill="#009245"/>
  </g>
</svg>
</div>
"""

def inject_app_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown(APP_WAVES_HTML, unsafe_allow_html=True)
