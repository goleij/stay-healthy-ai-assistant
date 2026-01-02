# profile/library_css.py
import streamlit as st

LIBRARY_CSS = """
<style>


/* Make sure page fills the viewport */
.stMain,
.stMainBlockContainer{
  min-height: 100vh;
}

/* --- Background wave (BOTTOM) --- */
.auth-bg-bottom{
  position: fixed;
  left: 0;
  bottom: 0;          /* stays at viewport bottom */
  width: 100vw;
  height: 150px;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

/* SVG sizing */
.auth-bg-bottom svg{
  width: 110vw;
  max-width: none;
  height: 100%;
  display: block;
}

/* Content above wave */
.block-container{
  position: relative;
  z-index: 1;
  padding-bottom: 150px;   /* exactly wave height */
}

/* Prevent horizontal scroll */
html, body{
  overflow-x: hidden;
}








:root{
  --text: #23233C;
  --primary: #009245;
  --primary-hover: #F5C400;

  --fs-h1: 1.8rem;
  --fs-h2: 1.3rem;
  --fs-h3: 1.1rem;
  --fs-button: 0.95rem;
  --fs-text: 0.9rem;
}

html, body, .stApp{
  color: var(--text);
  font-size: var(--fs-text);
}

/* Headings */
h1{ font-size: var(--fs-h1); }
h2{ font-size: var(--fs-h2); }
h3{ font-size: var(--fs-h3); }

/* Center buttons */
.stButton{
  display: flex !important;
  justify-content: center !important;
}

/* Buttons (Back to profile etc.) */
.stButton > button{
  width: min(420px, 180%) !important;
  margin-top: 0.75rem !important;

  min-height: 44px !important;
  padding: 0.6rem 1.25rem !important;

  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;

  font-size: var(--fs-button);
  font-weight: 700;
  white-space: nowrap;

  border-radius: 999px !important;
  background-color: var(--primary) !important;
  color: #ffffff !important;
  border: none !important;

  cursor: pointer;
}

/* Hover */
.stButton > button:hover{
  background-color: var(--primary-hover) !important;
  color: var(--text) !important;
}

/* Focus */
.stButton > button:focus{
  outline: 2px solid rgba(245,196,0,0.6) !important;
  outline-offset: 2px !important;
}
</style>
"""

def inject_library_css() -> None:
    st.markdown(LIBRARY_CSS, unsafe_allow_html=True)

    st.markdown('''
  
   <div class="auth-bg-bottom">

    <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="200" viewBox="0 0 414 198" preserveAspectRatio="none">
       <g>
           <path d="M1.681,786.1s137.4-128.75,294.973-84.552,220.989-280.56,220.989-280.56v605.319H-8.888Z" transform="translate(-20.721 -630.787)" fill="#009245" opacity="0.16"/>
           <path d="M1.681,786.1s137.4-128.75,294.973-84.552,220.989-280.56,220.989-280.56v605.319H-8.888Z" transform="translate(-24.289 -602.249)" fill="#009245"/>
       </g>
   </div>
   ''', unsafe_allow_html=True)




