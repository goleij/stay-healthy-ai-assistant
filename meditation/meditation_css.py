import streamlit as st


MEDITATION_CSS = """
<style>
@import url("https://fonts.googleapis.com/icon?family=Material+Icons");
@import url('https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap');

/* ============================
   STREAMLIT SLIDER — FULL GREEN
   ============================ */

/* 1) Value bubble */
div[data-testid="stSliderThumbValue"] {
    color: #009245 !important;
    font-weight: 700 !important;
}

/* 2) Active track */
.stSlider .rc-slider-track {
    background-color: #009245 !important;
}

/* 3) Handle */
.stSlider .rc-slider-handle {
    background: #009245 !important;
    border-color: #009245 !important;
    box-shadow: 0 0 0 2px #00924533 !important;
}
.stSlider .rc-slider-handle:hover,
.stSlider .rc-slider-handle:active,
.stSlider .rc-slider-handle:focus {
    background: #f8c42c !important;
    border-color: #f8c42c !important;
}

/* Slider value label (various Streamlit versions) */
.stSlider .css-1y4p8pa,
.stSlider .st-emotion-cache-1y4p8pa,
.stSlider .st-emotion-cache-1r6slb0,
.stSlider .st-emotion-cache-1r6slb0 span {
    color: #009245 !important;
}

/* Slider handle (Streamlit/Emotion) */
.st-emotion-cache-11xx4re {
    -webkit-box-align: center;
    align-items: center;
    background-color: #009245 !important;
    border-radius: 100% !important;
    border-style: none !important;
    display: flex;
    -webkit-box-pack: center;
    justify-content: center;
    height: 0.75rem !important;
    width: 0.75rem !important;
    box-shadow: none !important;
}

/* Streamlit Radio/Slider inner circle/handle background fix */
.st-e6 {
    background-color: #009245 !important;
}

/* ============================
   RADIO (selected green)
   ============================ */
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] {
    border-color: #009245 !important;
}
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] svg {
    color: #009245 !important;
    fill: #009245 !important;
}
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] circle {
    fill: #009245 !important;
    stroke: #009245 !important;
}
.stRadio [data-baseweb="radio"] label {
    color: #23233a !important;
    font-weight: 700 !important;
    font-size: 14px !important;   /* compact labels */
}

/* ============================
   SLIDER (Baseweb)
   ============================ */
.stSlider > div[data-baseweb="slider"] .rc-slider-track {
    background-color: #009245 !important;
}
.stSlider > div[data-baseweb="slider"] .rc-slider-handle {
    border-color: #009245 !important;
    background: #009245 !important;
    box-shadow: 0 0 0 2px #00924533;
}
.stSlider > div[data-baseweb="slider"] .rc-slider-dot-active {
    border-color: #009245 !important;
}

/* ============================
   TEXT FIELDS
   ============================ */
.stTextInput > div > input,
.stTextArea > div > textarea,
input[type="text"],
textarea {
    background: #e1efe3 !important;
    border-radius: 8px !important;
    border: 1.5px solid #b6d1c2 !important;
    font-size: 14px !important;
    font-family: 'Roboto', Arial, sans-serif !important;
    color: #23233a !important;
    transition: background 0.2s, border 0.2s;
}
.stTextInput > div > input:hover,
.stTextInput > div > input:focus,
.stTextArea > div > textarea:hover,
.stTextArea > div > textarea:focus,
input[type="text"]:hover,
input[type="text"]:focus,
textarea:hover,
textarea:focus {
    background: #f8c42c !important;
    border-color: #f8c42c !important;
    outline: none !important;
}

/* Font everywhere */
.stApp, .stApp * {
    font-family: 'Roboto', Arial, sans-serif !important;
}

/* Main container */
.stApp .main > div {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    position: relative;
    background: #f7f8fb;
    min-height: 600px;
}

/* Meditation SVG background at bottom (if used) */
.meditation-bg-svg {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100vw;
    height: 200px;
    z-index: 0;
    pointer-events: none;
}

/* ============================
   HEADINGS
   ============================ */

/* h1 (if used somewhere) */
h1, .stApp h1, .stMarkdown h1, .stMarkdown > h1 {
    font-size: 26px !important;
    font-weight: 700 !important;
    margin-bottom: 0.7em;
}

/* h2 default: keep smaller for section titles (Style/Length/Ambient Style) */
h2, .stApp h2, .stMarkdown h2, .stMarkdown > h2 {
    font-size: 16px !important;
    font-weight: 700 !important;
    margin-bottom: 0.6em;
}

/* SPECIAL: page title "## Meditation Studio" is an h2 -> make ONLY the first one bigger */
.stMarkdown h2:first-of-type,
.stMarkdown > h2:first-of-type {
    font-size: 28px !important;
    font-weight: 700 !important;
    margin-bottom: 1rem !important;
}

/* h3 */
h3, .stApp h3, .stMarkdown h3, .stMarkdown > h3 {
    font-size: 15px !important;
    font-weight: 700 !important;
    margin-bottom: 0.5em;
}

/* Body text */
body, .stApp, .stApp p, .stMarkdown, .stMarkdown p, .meditation-text {
    font-size: 14px !important;
    font-weight: 400 !important;
    color: #23233a !important;
}

/* ============================
   BUTTONS
   ============================ */
.stButton > button {
    background-color: #009245 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 20px !important;
    min-height: 36px !important;

    padding-top:    0.35rem;
    padding-bottom: 0.35rem;
    padding-left:   2rem;
    padding-right:  2rem;

    font-size: 14px !important;
    font-weight: 700 !important;
    box-shadow: none !important;
    outline: none !important;
    cursor: pointer !important;
}

/* Hover/Active: yellow bg + WHITE text */
.stButton > button:hover,
.stButton > button:active {
    background: #f8c42c !important;
    color: #ffffff !important;
    border: 3px solid #f8c42c !important;
}

/* Sometimes Streamlit wraps label in <p> */
.stButton > button:hover p,
.stButton > button:active p {
    color: #ffffff !important;
}

/* Selected button: add border in text color (dark border) */
.stButton > button.selected,
.stButton > button[aria-pressed="true"],
.stButton > button[style*='border: 3px solid #23233a'] {
    border: 3px solid #23233a !important;
    color: #ffff !important;
}

/* COMPACT padding for the two top tab-buttons (use_container_width=True) */
button[data-testid="baseButton"][aria-label="Neue Meditation"],
button[data-testid="baseButton"][aria-label="Gespeicherte Meditationen"] {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
}

/* Streamlit primary color var (optional) */
:root {
  --primary-color: #009245 !important;
}

/* ========================================
   MOBILE FIXES — TOUCH INTERACTION SUPPORT
   ======================================== */
@media (max-width: 768px) {

    .stButton > button,
    .stSlider .rc-slider-handle,
    input[type="text"],
    textarea {
        touch-action: manipulation;
    }

    /* Tap/Focus -> yellow + white text */
    .stButton > button:active,
    .stButton > button:focus-visible {
        background: #f8c42c !important;
        color: #ffffff !important;
        border: 3px solid #f8c42c !important;
    }
    .stButton > button:active p,
    .stButton > button:focus-visible p {
        color: #ffffff !important;
    }

    /* Slider handle bigger on mobile */
    .stSlider .rc-slider-handle {
        width: 1.2rem !important;
        height: 1.2rem !important;
        margin-top: -6px !important;
    }

    /* Slider on touch */
    .stSlider .rc-slider-handle:active {
        background: #f8c42c !important;
        border-color: #f8c42c !important;
    }

    .stSlider .rc-slider-track { height: 6px !important; }
    .stSlider .rc-slider-rail  { height: 6px !important; }

    /* Inputs */
    input[type="text"],
    textarea,
    .stTextInput > div > input,
    .stTextArea > div > textarea {
        font-size: 14px !important;
        padding: 0.9em !important;
    }

    /* Radio layout */
    .stRadio [data-baseweb="radio"] > div {
        padding: 6px 10px !important;
    }
    .stRadio label {
        padding-left: 6px !important;
        font-size: 14px !important;
    }

    /* Keep title big on mobile, sections small */
    .stMarkdown h2:first-of-type,
    .stMarkdown > h2:first-of-type {
        font-size: 28px !important;
    }
    h2 { font-size: 16px !important; }
    h3 { font-size: 15px !important; }

    /* Main container tighter */
    .stApp .main > div {
        max-width: 100% !important;
        padding: 0 12px !important;
    }

    .meditation-bg-svg { height: 160px !important; }

    /* Compact padding for top tabs also on mobile */
    button[data-testid="baseButton"][aria-label="Neue Meditation"],
    button[data-testid="baseButton"][aria-label="Gespeicherte Meditationen"] {
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
}

/* =======================================
   MOBILE TOUCH FIX — DEACTIVATE HOVER
   ======================================= */
@media (hover: none) and (pointer: coarse) {

    .stButton > button:hover {
        background: #009245 !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button:hover p {
        color: #ffffff !important;
    }

    .stButton > button:active,
    .stButton > button:focus-visible {
        background: #f8c42c !important;
        color: #ffffff !important;
        border: 3px solid #f8c42c !important;
    }
    .stButton > button:active p,
    .stButton > button:focus-visible p {
        color: #ffffff !important;
    }
}

/* ============================
   FIX: Material Icons override
   ============================ */
.material-icons,
.material-symbols-rounded,
.material-symbols-outlined,
.material-symbols-sharp,
[class*="material-symbols"],
[class*="material-icons"],
.st-emotion-cache-pd6qx2,
.st-emotion-cache-17hxo5v {
    font-family: 'Material Icons', 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Symbols Sharp' !important;
    font-style: normal !important;
    font-weight: normal !important;
    font-size: inherit;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    direction: ltr;
    -webkit-font-smoothing: antialiased;
}
/* FORCE white text inside buttons (fix blue text issue) */
.stButton > button,
.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: #ffffff !important;
}

/* FIX: reduce left/right padding for meditation tab buttons */
button[data-testid="baseButton"][aria-label="Neue Meditation"],
button[data-testid="baseButton"][aria-label="Gespeicherte Meditationen"] {
    padding-left: 0.4rem !important;
    padding-right: 0.4rem !important;
}

/* FIX: make radio buttons perfectly circular */
.stRadio [data-baseweb="radio"] > div {
    
    padding: 0.2rem !important;          /* <-- WICHTIG */
    border-radius: 50% !important;
    display: flex;
    align-items: center;
    justify-content: center;
}

span.st-emotion-cache-zkd0x0 {
    font-family: 'Material Symbols Rounded' !important;
}

.stRadio [data-baseweb="radio"] > div[aria-checked="true"] {
    border-color: #009245 !important;
}
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] svg {
    color: #009245 !important;
    fill: #009245 !important;
}
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] circle {
    fill: #009245 !important;
    stroke: #009245 !important;
}
.stRadio [data-baseweb="radio"] label {
    color: #23233a !important;
    font-weight: 700 !important;
    font-size: 14px !important;   /* compact labels */
}

</style>
"""

def inject_meditation_css() -> None:
    st.markdown(MEDITATION_CSS, unsafe_allow_html=True)
