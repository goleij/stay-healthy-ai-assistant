# auth/auth_ui.py
import streamlit as st
from storage.profile_manager import (
    load_state_for_user,
    ensure_session_defaults,
    load_users,

)
from .auth_logic import signup_user, login_user
from .auth_css import inject_auth_css


def show_auth_page():
    """Render login/signup page."""
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"

    view = st.session_state.auth_view

    # Inject CSS for auth page
    inject_auth_css()


    # ---------- LOGIN VIEW ---------- #
    if view == "login":
        st.subheader("Welcome!")

        with st.form("login_form"):
            identifier = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            ok, msg, username = login_user(identifier, password)
            if ok:
                st.success(msg)
                st.session_state.authenticated = True
                st.session_state.username = username

                # Load or init state for this user
                ensure_session_defaults()
                load_state_for_user(username)

                #  get email from users.json and keep it in session only
                users = load_users()
                email = users.get(username, {}).get("email", "")
                st.session_state["auth_email"] = email


                st.rerun()
            else:
                st.error(msg)

        st.markdown("---")

        st.write("Don't have an account?")
        if st.button("Create a new account"):
            st.session_state.auth_view = "signup"
            st.rerun()


    # ---------- SIGNUP VIEW ---------- #
    elif view == "signup":
        st.subheader("Create Account")

        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign up")

        if submitted:
            # Check password confirmation
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                ok, msg = signup_user(username, email, password)
                if ok:
                    st.success(msg)
                    st.session_state.auth_view = "login"
                    st.info("Please log in with your new account.")
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        if st.button("Back to login"):
            st.session_state.auth_view = "login"
            st.rerun()
