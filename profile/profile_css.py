# profile/profile_css.py
import streamlit as st

PROFILE_CSS = """
<style>
/* Hide uploaded file row for the avatar uploader */
[data-testid="stFileUploader"] div[data-testid="stFileUploaderFile"] {
    display: none;
}

/* Avatar circle with image */
.profile-avatar-circle {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid #e5e7eb;
    background: #f9fafb;
    display: flex;
    align-items: center;
    justify-content: center;
}
.profile-avatar-circle img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* Empty avatar placeholder */
.profile-avatar-empty {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    border: 1px dashed #d1d5db;
    background: #f9fafb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #6b7280;
    text-align: center;
    padding: 8px;
}
</style>
"""


def inject_profile_css() -> None:
    """Inject custom CSS for the profile page."""
    st.markdown(PROFILE_CSS, unsafe_allow_html=True)
