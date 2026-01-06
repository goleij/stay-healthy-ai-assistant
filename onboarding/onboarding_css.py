# onboarding/onboarding_css.py
import streamlit as st


def inject_onboarding_css() -> None:
    """Styles for the onboarding (multistep) form + loading screen."""
    st.markdown(
        """
        <style>
        
        
        .loading-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #23233C;          /* <-- gewünschte Farbe */
            text-align: center;
            margin-bottom: 20px;
            line-height: 1.3;
        }
        
        @media (max-width: 480px) {
            .loading-title {
                font-size: 1.1rem;
                margin-bottom: 16px;
            }
        }

        
        /* Wrapper for onboarding page */
        .onboarding-wrapper {
            max-width: 480px;
            margin: 0 auto;
            padding-bottom: 2.5rem;
        }

        .onboarding-wrapper h1 {
            font-size: 2rem;
            margin-bottom: 0.25rem;
        }

        .onboarding-wrapper p {
            font-size: 0.9rem;
        }

        /* Full-width inputs inside onboarding */
        .onboarding-wrapper [data-testid="stTextInput"] input,
        .onboarding-wrapper [data-testid="stSlider"],
        .onboarding-wrapper textarea {
            width: 100%;
        }

        /* Back / Next row (desktop default) */
        .onboarding-wrapper [data-testid="stHorizontalBlock"] {
            margin-top: 1rem;
            gap: 0.5rem;
        }

        .onboarding-wrapper [data-testid="stHorizontalBlock"] .stButton > button {
            width: 100%;
            border-radius: 999px;
            padding: 0.35rem 0.6rem;
            font-size: 0.9rem;
        }

        /* Keep Back / Next on one row on small screens */
        @media (max-width: 600px) {
            .onboarding-wrapper [data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
            }

            .onboarding-wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                flex: 1 1 0 !important;
                width: 50% !important;
            }
        }

        /* ---------- Loading screen (step 11) ---------- */
        .loading-overlay {
            position: fixed;
            inset: 0;
            background: #ffffff;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .loading-title {
            font-size: 28px;
            font-weight: 600;
            color: #333333;
            margin-bottom: 32px;
        }

        .circle-outer {
            width: 240px;
            height: 240px;
            border-radius: 50%;
            border: 2px dashed #a0d6a7;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
        }

        .circle-mid {
            width: 170px;
            height: 170px;
            border-radius: 50%;
            border: 2px dashed #d2ead5;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .circle-inner {
            width: 115px;
            height: 115px;
            border-radius: 50%;
            background: #f7f7f7;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            font-weight: 600;
            color: #444444;
        }

        .loading-subtitle {
            font-size: 16px;
            color: #666666;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
