# python
# File: `angewandte-generative-ki/landing/landing_css.py`
import streamlit as st

LANDING_CSS = """
<style>
/* ========== Global: Fullscreen & kein Scrollen ========== */
html, body {
  height: 100%;
  overflow: hidden !important;
}

[data-testid="stAppViewContainer"] {
  height: 100vh !important;
  overflow: hidden !important;
}

/* Main zentriert */
section.main {
  height: 100vh !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;

  background: radial-gradient(
    circle at top,
    rgba(245,196,0,0.18),
    rgba(255,255,255,1) 55%
  ) !important;
}

/* Card – bewusst schmal & mobile-like */
section.main .block-container {
  width: min(380px, 92vw) !important;
  max-width: 380px !important;

  padding: 20px 14px 26px 14px !important;
  margin-bottom: 0 !important;


  backdrop-filter: blur(8px);
}

/* Header komplett aus */
header[data-testid="stHeader"] {
  display: none !important;
}

/* Inhalt sauber mittig */
section.main .block-container > div {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  text-align: center !important;
}

/* Logo: runter + minimal nach rechts (optische Mitte) */
[data-testid="stImage"] {
  display: flex !important;
  justify-content: center !important;
  width: 100% !important;
  margin-top: 18px !important;
  margin-bottom: 0px !important;
}

[data-testid="stImage"] img {
  display: block !important;
  margin: 0 auto !important;
  transform: translateX(65px);   /* <<< Logo leicht nach rechts */
}

/* Badges */
.landing-badges {
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: center;
  margin-bottom: 40px;
  margin-top: 0px;
}

.landing-badge {
  width: 100%;
  max-width: 250px;
  color: #009245;
  padding: 10px 10px;
  font-size: 15px;
  line-height: 1.25;
  text-align: center;
  font-weight: bold;
}

/* ========== Buttons: klein + Outline (keine Fläche) ========== */
.stButton {
  width: 100%;
  display: flex;
  justify-content: center;
}

/* Base Outline Button */
.stButton > button {
  width: auto !important;          /* <<< nicht full-width */
  min-width: 230px;               /* <<< angenehme Breite */
  max-width: 320px;
  font-weight: bold !important;    /* <<< jetzt fett */
  background: transparent !important;      /* <<< keine Fläche */
  border: 2px solid #009245 !important;    /* <<< Kontur */
  color: #009245 !important;               /* <<< grüne Schrift */
  border-radius: 999px !important;
  padding: 10px 16px !important;           /* <<< kleiner */
  font-size: 13px !important;              /* <<< kleiner */
  box-shadow: none !important;
  margin-bottom: 10px;
  transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease, transform 120ms ease;
}



/* Hover: gelber Hintergrund #F5C400 und weiße Schrift */
.stButton > button:hover {
  background: #F5C400 !important;
  border-color: #F5C400 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  transform: translateY(-1px);
}

/* Focus */
.stButton > button:focus,
.stButton > button:active {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(0,146,69,0.16) !important;
  color: #ffffff !important; /* falls Fokusfarbe sichtbar wird */
}

/* Mobile: Buttons wieder breiter (optional schöner auf kleinsten Screens) */
@media (max-width: 420px) {
  .stButton > button {
    width: 100% !important;
    max-width: 50px !important;
  }
}
</style>
"""

def inject_landing_css() -> None:
  st.markdown(LANDING_CSS, unsafe_allow_html=True)
