# landing/landing_css.py
import streamlit as st

LANDING_CSS = """
<style>
.landing-root {
    width: 100%;
    padding-top: 1.2rem;          /* small space from very top */
    padding-bottom: 3rem;
    background: radial-gradient(
        circle at top
    );
}


.landing-title {
    font-size: 32px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
}

.landing-subtitle {
    font-size: 15px;
    color: #64748b;
    margin-bottom: 24px;
}

.landing-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 24px;
}

.landing-badge {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 999px;
    background: #ecfeff;
    color: #0f766e;
    border: 1px solid #a5f3fc;
}

.landing-button-row {
    display: flex;
    gap: 10px;
    margin-top: 8px;
}

button.landing-primary {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #ffffff;
    border-radius: 999px;
    border: none;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 14px;
}

button.landing-primary:hover {
    background: linear-gradient(135deg, #16a34a, #15803d);
}

button.landing-secondary {
    background: #f8fafc;
    color: #0f172a;
    border-radius: 999px;
    border: 1px solid #e2e8f0;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 14px;
}

button.landing-secondary:hover {
    background: #e2e8f0;
}

.landing-small {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 10px;
}
</style>
"""


def inject_landing_css() -> None:
    st.markdown(LANDING_CSS, unsafe_allow_html=True)
