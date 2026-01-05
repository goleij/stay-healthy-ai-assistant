import streamlit as st
from pathlib import Path
from .landing_css import inject_landing_css


def show_landing_page() -> None:
    inject_landing_css()

    img_path = Path(__file__).resolve().parents[1] / "Logo.png"
    if not img_path.exists():
        img_path = Path("Logo.png")

    st.image(str(img_path), width=200)

    badges = [
        "Personalized Health – Training made for you.",
        "Balanced Lifestyle – Nutrition, meditation, and recovery.",
        "Smart Support – Recipes and guidance tailored to your goals.",
    ]

    badges_html = (
        '<div class="landing-badges">'
        + "".join(f'<span class="landing-badge">{b}</span>' for b in badges)
        + "</div>"
    )
    st.markdown(badges_html, unsafe_allow_html=True)

    primary = st.button(
        "Get started – create account",
        key="landing_signup",
        use_container_width=True,
    )

    secondary = st.button(
        "I already have an account",
        key="landing_login",
        use_container_width=True,
    )

    if primary:
        st.session_state["auth_stage"] = "auth"
        st.session_state["auth_view"] = "signup"
        st.rerun()

    if secondary:
        st.session_state["auth_stage"] = "auth"
        st.session_state["auth_view"] = "login"
        st.rerun()
