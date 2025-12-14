# landing/landing_ui.py
import streamlit as st
from .landing_css import inject_landing_css


def show_landing_page() -> None:
    inject_landing_css()

    # wrapper
    st.markdown('<div class="landing-root">', unsafe_allow_html=True)
    st.markdown('<div class="landing-card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="landing-title">Stay Healthy AI</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="landing-subtitle">'
        "Your personal AI coach for workouts, nutrition and healthy habits."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-badges">', unsafe_allow_html=True)
    st.markdown('<span class="landing-badge">7-day smart plans</span>', unsafe_allow_html=True)
    st.markdown('<span class="landing-badge">Health-aware recipes</span>', unsafe_allow_html=True)
    st.markdown('<span class="landing-badge">Chat with your coach</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(
            "- Answer a few quick questions about your body and goals.\n"
            "- Get a safe 7-day plan adapted to your health conditions.\n"
            "- Ask your coach for workouts, meals and shopping lists."
        )

    with col2:
        st.write("")

    # Buttons row
    col_primary, col_secondary = st.columns([1.3, 1])

    with col_primary:
        primary = st.button(
            "Get started – create account",
            key="landing_signup",
            help="Go to sign up",
        )
    with col_secondary:
        secondary = st.button(
            "I already have an account",
            key="landing_login",
            help="Go to login",
        )

    if primary:
        st.session_state["auth_stage"] = "auth"
        st.session_state["auth_view"] = "signup"
        st.rerun()

    if secondary:
        st.session_state["auth_stage"] = "auth"
        st.session_state["auth_view"] = "login"
        st.rerun()



    st.markdown("</div></div>", unsafe_allow_html=True)
