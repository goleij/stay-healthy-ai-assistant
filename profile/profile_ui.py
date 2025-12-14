# profile/profile_ui.py
import base64
import streamlit as st
from storage.profile_manager import save_state_for_current_user
from .profile_css import inject_profile_css


def _format_value(value, suffix: str = "") -> str:
    if value is None or value == "":
        return "–"
    if suffix:
        return f"{value}{suffix}"
    return str(value)


def _get_avatar_bytes_from_profile(profile: dict) -> bytes | None:
    avatar_b64 = profile.get("avatar_b64")
    if not avatar_b64:
        return None
    try:
        return base64.b64decode(avatar_b64)
    except Exception:
        return None


def _set_avatar_bytes_in_profile(profile: dict, data: bytes | None) -> None:
    if data is None:
        profile["avatar_b64"] = None
    else:
        profile["avatar_b64"] = base64.b64encode(data).decode("utf-8")


def _render_avatar_section(profile: dict) -> None:
    avatar_bytes: bytes | None = _get_avatar_bytes_from_profile(profile)

    cols = st.columns([1, 2])

    # right: uploader + remove button
    with cols[1]:
        uploaded = st.file_uploader(
            "Upload picture",
            type=["jpg", "jpeg", "png"],
            key="profile_avatar_uploader",
        )

        remove_clicked = False
        if avatar_bytes:
            remove_clicked = st.button("Remove picture")

        if uploaded is not None:
            data = uploaded.read()
            _set_avatar_bytes_in_profile(profile, data)
            st.session_state["profile"] = profile
            save_state_for_current_user()
            st.success("Profile picture updated.")
            avatar_bytes = data

        if remove_clicked:
            _set_avatar_bytes_in_profile(profile, None)
            st.session_state["profile"] = profile
            save_state_for_current_user()
            st.success("Profile picture removed.")
            avatar_bytes = None

    # left: avatar circle
    with cols[0]:
        if avatar_bytes:
            img_b64 = base64.b64encode(avatar_bytes).decode("utf-8")
            st.markdown(
                f"""
                <div class="profile-avatar-circle">
                    <img src="data:image/png;base64,{img_b64}" />
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="profile-avatar-empty">
                    Upload picture
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_personal_info(profile: dict) -> None:
    st.subheader("Personal information")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Weight", _format_value(profile.get("weight"), " kg"))
        st.metric("Height", _format_value(profile.get("height"), " cm"))
    with col2:
        st.metric("Age", _format_value(profile.get("age"), " years"))
        st.metric("Gender", _format_value(profile.get("gender")))
    with col3:
        st.metric("Activity level", _format_value(profile.get("activity")))
        st.metric("Workouts per week", _format_value(profile.get("workout_days")))

    st.write("")
    st.write("**Goal:**", _format_value(profile.get("goal")))
    st.write("**Diet preference:**", _format_value(profile.get("diet")))
    st.write("**Email:**", _format_value(profile.get("email", "")))

    with st.expander("Edit personal information"):
        _render_edit_personal_form(profile)


def _render_health_section(profile: dict) -> None:
    st.subheader("Restrictions & health")

    allergies = profile.get("allergies") or ""
    conditions = profile.get("health_conditions") or []
    limitations = profile.get("limitations") or []

    if not allergies and not conditions and not limitations:
        st.write("No health restrictions saved.")
        return

    if allergies:
        st.markdown("**Allergies / intolerances:**")
        st.write(allergies)

    if conditions:
        st.markdown("**Health conditions:**")
        for c in conditions:
            st.write(f"- {c}")

    if limitations:
        st.markdown("**Physical limitations / handicap:**")
        for l in limitations:
            st.write(f"- {l}")


def _render_edit_personal_form(profile: dict) -> None:
    with st.form("edit_personal_form"):
        name = st.text_input("Name", value=profile.get("name", ""))

        col1, col2, col3 = st.columns(3)
        with col1:
            weight_str = st.text_input(
                "Weight (kg)",
                value=str(profile.get("weight", "")),
            )
        with col2:
            height_str = st.text_input(
                "Height (cm)",
                value=str(profile.get("height", "")),
            )
        with col3:
            age_str = st.text_input(
                "Age",
                value=str(profile.get("age", "")),
            )

        gender = st.selectbox(
            "Gender",
            options=["Male", "Female", "Other"],
            index=["Male", "Female", "Other"].index(
                profile.get("gender", "Male")
            )
            if profile.get("gender", "Male") in ["Male", "Female", "Other"]
            else 0,
        )

        submitted = st.form_submit_button("Save changes")

        if submitted:
            errors = []

            try:
                weight = float(weight_str.replace(",", "."))
            except ValueError:
                errors.append("Weight must be a number.")
                weight = profile.get("weight")

            try:
                height = float(height_str.replace(",", "."))
            except ValueError:
                errors.append("Height must be a number.")
                height = profile.get("height")

            try:
                age = int(age_str)
            except ValueError:
                errors.append("Age must be an integer.")
                age = profile.get("age")

            if errors:
                st.error(" / ".join(errors))
                return

            profile["name"] = name.strip() or profile.get("name", "")
            profile["weight"] = float(weight) if weight is not None else None
            profile["height"] = float(height) if height is not None else None
            profile["age"] = int(age) if age is not None else None
            profile["gender"] = gender

            st.session_state["profile"] = profile
            save_state_for_current_user()
            st.success("Personal information updated.")
            st.rerun()


def render_profile_page() -> None:
    inject_profile_css()

    profile = st.session_state.get("profile")
    if not profile:
        st.info("No profile found yet. Please fill in the form first.")
        if st.button("Go to form"):
            st.session_state.page = "form"
        return

    # autofill email from auth session keys if missing
    if not profile.get("email"):
        auth_email = (
            st.session_state.get("auth_email")
            or st.session_state.get("user_email")
            or st.session_state.get("email")
        )
        if auth_email:
            profile["email"] = auth_email
            st.session_state["profile"] = profile
            save_state_for_current_user()

    name = profile.get("name") or "Profile"
    st.header(name)

    _render_avatar_section(profile)
    st.write("---")
    _render_personal_info(profile)
    st.write("---")
    _render_health_section(profile)
