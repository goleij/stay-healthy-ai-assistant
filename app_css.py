import streamlit as st


def inject_sidebar_css() -> None:
    """Compact, mobile-friendly sidebar buttons."""
    st.markdown(
        """
        <style>
        /* Sidebar background */
        [data-testid="stSidebar"] {
            background-color: #f7f9fc;
        }

        /* Sidebar buttons */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            border-radius: 999px;
            padding: 0.35rem 0.6rem;
            margin: 0.2rem 0;
            font-size: 0.9rem;
            border: 1px solid #e0e4f0;
            background-color: #ffffff;
        }

        /* Extra compact on small screens */
        @media (max-width: 600px) {
            [data-testid="stSidebar"] .stButton > button {
                padding: 0.25rem 0.4rem;
                font-size: 0.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
