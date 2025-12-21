import streamlit as st

MEDITATION_CSS = """
<style>
@import url('https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap');

/* Slider-Track (Linie) grün */
.stSlider .rc-slider-track {
    background-color: #009245 !important;
}

/* Slider Value-Label (Zahl über dem Handle) grün */
.stSlider .css-1y4p8pa, /* Streamlit 1.x */
.stSlider .st-emotion-cache-1y4p8pa, /* Streamlit 1.x/2.x */
.stSlider .st-emotion-cache-1r6slb0, /* Streamlit 2.x */
.stSlider .st-emotion-cache-1r6slb0 span {
    color: #009245 !important;
}

/* Slider handle (Streamlit/Emotion) gezielt grün und rund */
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
/* Force green for selected radio button inner circle and label */
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
}

/* Force green for slider handle and track */
.stSlider .rc-slider-track {
    background-color: #009245 !important;
}
.stSlider .rc-slider-handle {
    border-color: #009245 !important;
    background: #009245 !important;
    box-shadow: 0 0 0 2px #00924533 !important;
}
.stSlider .rc-slider-dot-active {
    border-color: #009245 !important;
}
.stSlider .rc-slider-handle:active, .stSlider .rc-slider-handle:focus, .stSlider .rc-slider-handle:hover {
    border-color: #f8c42c !important;
    background: #f8c42c !important;
}



/* Radio-Button: selected (checked) Farbe auf #009245 */
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] {
    border-color: #009245 !important;
}
.stRadio [data-baseweb="radio"] svg {
    color: #009245 !important;
}
.stRadio [data-baseweb="radio"] > div[aria-checked="true"] svg {
    color: #009245 !important;
}

/* Slider (Lautstärkeregler) Farbe auf #009245 */
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

/* Text fields */
.stTextInput > div > input,
.stTextArea > div > textarea,
input[type="text"],
textarea {
    background: #e1efe3 !important;
    border-radius: 8px !important;
    border: 1.5px solid #b6d1c2 !important;
    font-size: 18px !important;
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

.stApp, .stApp * {
    font-family: 'Roboto', Arial, sans-serif !important;
}

.stApp .main > div {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    position: relative;
    background: #f7f8fb;
    min-height: 600px;
}

/* Meditation SVG background at bottom */
.meditation-bg-svg {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100vw;
    height: 200px;
    z-index: 0;
    pointer-events: none;
}

/* Headings */
h1, .stApp h1, .stMarkdown h1, .stMarkdown > h1 {
    font-size: 30px !important;
    font-weight: 700 !important;
    margin-bottom: 0.7em;
}
h2, .stApp h2, .stMarkdown h2, .stMarkdown > h2 {
    font-size: 25px !important;
    font-weight: 700 !important;
    margin-bottom: 0.6em;
}
h3, .stApp h3, .stMarkdown h3, .stMarkdown > h3 {
    font-size: 20px !important;
    font-weight: 700 !important;
    margin-bottom: 0.5em;
}

/* Body text */
body, .stApp, .stApp p, .stMarkdown, .stMarkdown p, .meditation-text, .stTextInput input, .stTextArea textarea {
    font-size: 18px !important;
    font-weight: 400 !important;
}

/* Tab Navigation (keep for future, not used now) */
.meditation-tabs-row {
    display: flex;
    border-bottom: 2px solid #e0e0e0;
    margin-bottom: 0.5rem;
    margin-top: 0.5rem;
}
.meditation-tab {
    flex: 1;
    text-align: center;
    padding: 12px 0 8px 0;
    cursor: pointer;
    font-size: 1.1rem;
    background: none;
    border: none;
    outline: none;
    color: #444;
    border-bottom: 2px solid transparent;
    transition: color 0.2s, border-bottom 0.2s;
}
.meditation-tab.selected {
    color: #007bff;
    border-bottom: 2.5px solid #007bff;
    font-weight: 600;
}
.meditation-tab:not(:last-child) {
    border-right: 1.5px solid #e0e0e0;
}

/* Buttons */
.stButton > button {
    border-radius: 999px !important;
    background: #009245 !important;
    color: #fff !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 0.7em 2.5em !important;
    box-shadow: none !important;
    transition: background 0.2s, border 0.2s;
    min-width: 180px;
}
.stButton > button:hover, .stButton > button:active {
    background: #f8c42c !important;
    color: #23233a !important;
    border: 3px solid #f8c42c !important;
}

/* Selected button: add border in text color (dunkler Rand) */
.stButton > button.selected,
.stButton > button[aria-pressed="true"],
.stButton > button[style*='border: 3px solid #23233a'] {
    border: 3px solid #23233a !important;
    color: #fff !important;
}

:root {
  --primary-color: #009245 !important;
}
</style>
"""

def inject_meditation_css():
        st.markdown(MEDITATION_CSS, unsafe_allow_html=True)
        st.markdown('''
<div class="meditation-bg-svg">
<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="200" viewBox="0 0 414 198" preserveAspectRatio="none">
    <g>
        <path d="M1.681,786.1s137.4-128.75,294.973-84.552,220.989-280.56,220.989-280.56v605.319H-8.888Z" transform="translate(-20.721 -630.787)" fill="#009245" opacity="0.16"/>
        <path d="M1.681,786.1s137.4-128.75,294.973-84.552,220.989-280.56,220.989-280.56v605.319H-8.888Z" transform="translate(-24.289 -602.249)" fill="#009245"/>
    </g>
</svg>
</div>
''', unsafe_allow_html=True)
