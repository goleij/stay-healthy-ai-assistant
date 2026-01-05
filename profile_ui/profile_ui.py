# File: angewandte-generative-ki/profile_ui/profile_ui.py
import base64
import json
import os
import streamlit as st
from .profile_css import inject_profile_css

# Try project-wide storage manager; fallback for development/IDE.
try:
    from storage.profile_manager import save_state_for_current_user  # type: ignore
except Exception:
    def save_state_for_current_user() -> None:
        """Fallback: save profile locally as .profile_backup.json (dev)."""
        try:
            p = st.session_state.get("profile", {})
            path = os.path.join(os.getcwd(), ".profile_backup.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(p, f, ensure_ascii=False, indent=2)
            st.session_state["_profile_backup_path"] = path
        except Exception:
            pass


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
            label_visibility="collapsed",
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
    """
    Render personal info using CSS classes from profile_css.py.
    Desktop: 3 columns; Mobile: 2 columns (CSS handles sizes).
    """
    st.subheader("Personal information")

    weight = _format_value(profile.get("weight"), " kg")
    height = _format_value(profile.get("height"), " cm")
    age = _format_value(profile.get("age"), " years")
    gender = _format_value(profile.get("gender"))
    activity = _format_value(profile.get("activity"))
    workouts = _format_value(profile.get("workout_days"))

    grid_html = f"""
    <div class="personal-info-grid">
      <div class="personal-info-item">
        <div class="personal-info-label">Weight</div>
        <div class="personal-info-value">{weight}</div>
      </div>
      <div class="personal-info-item">
        <div class="personal-info-label">Height</div>
        <div class="personal-info-value">{height}</div>
      </div>
      <div class="personal-info-item">
        <div class="personal-info-label">Age</div>
        <div class="personal-info-value">{age}</div>
      </div>
      <div class="personal-info-item">
        <div class="personal-info-label">Gender</div>
        <div class="personal-info-value">{gender}</div>
      </div>
      <div class="personal-info-item">
        <div class="personal-info-label">Activity level</div>
        <div class="personal-info-value">{activity}</div>
      </div>
      <div class="personal-info-item">
        <div class="personal-info-label">Workouts per week</div>
        <div class="personal-info-value">{workouts}</div>
      </div>
    </div>
    """

    st.markdown(grid_html, unsafe_allow_html=True)

    st.write("")
    st.write("**Goal:**", _format_value(profile.get("goal")))
    st.write("**Diet preference:**", _format_value(profile.get("diet")))
    email = profile.get("email") or st.session_state.get("auth_email") or ""
    st.write("**Email:**", _format_value(email))

    with st.expander("Edit personal information"):
        _render_edit_personal_form(profile)


def _render_health_section(profile: dict) -> None:
    st.subheader("Restrictions & health")

    allergies = profile.get("allergies") or ""
    conditions = profile.get("health_conditions") or []
    limitations = profile.get("limitations") or []

    if not allergies and not conditions and not limitations:
        st.write("No health restrictions saved.")
    else:
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

    with st.expander("Edit restrictions & health"):
        _render_edit_health_form(profile)


def _render_edit_personal_form(profile: dict) -> None:
    with st.form("edit_personal_form"):
        name = st.text_input("Name", value=profile.get("name", ""))

        col1, col2 = st.columns(2)
        with col1:
            weight_str = st.text_input(
                "Weight (kg)",
                value=str(profile.get("weight", "")),
            )
        with col2:
            age_str = st.text_input(
                "Age",
                value=str(profile.get("age", "")),
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
                age = int(age_str)
            except ValueError:
                errors.append("Age must be an integer.")
                age = profile.get("age")

            if errors:
                st.error(" / ".join(errors))
                return

            profile["name"] = name.strip() or profile.get("name", "")
            profile["weight"] = float(weight) if weight is not None else None
            profile["age"] = int(age) if age is not None else None

            st.session_state["profile"] = profile
            save_state_for_current_user()
            st.success("Personal information updated.")
            st.rerun()


def _render_edit_health_form(profile: dict) -> None:
    with st.form("edit_health_form"):
        st.subheader("Any limits, allergies or health conditions?")

        allergies = st.text_area(
            "Allergies (optional)",
            value=profile.get("allergies", ""),
            placeholder="e.g. peanuts, lactose, gluten...",
        )

        health_condition_options = ["Diabetes", "High blood pressure", "Heart disease"]
        existing_health = profile.get("health_conditions", []) or []
        health_conditions = st.multiselect(
            "Health conditions (optional)",
            health_condition_options,
            default=existing_health,
        )

        handicap_options = [
            "No significant limitation",
            "Broken arm",
            "Broken leg",
            "Wheelchair user / severe mobility limitation",
        ]
        existing_limits = profile.get("limitations", []) or []
        limitations = st.multiselect(
            "Physical limitations / handicap (optional)",
            handicap_options,
            default=existing_limits,
        )

        submitted = st.form_submit_button("Save changes")
        if submitted:
            profile["allergies"] = (allergies or "").strip()
            profile["health_conditions"] = health_conditions
            profile["limitations"] = limitations
            clean_limits = [l for l in limitations if l != "No significant limitation"]
            profile["health_issues"] = ", ".join(health_conditions + clean_limits)

            st.session_state["profile"] = profile
            save_state_for_current_user()
            st.success("Health information updated.")
            st.rerun()


def render_profile_page() -> None:
    inject_profile_css()

    profile = st.session_state.get("profile")
    if not profile:
        st.info("No profile found yet. Please fill in the form first.")
        if st.button("Go to form"):
            st.session_state.page = "form"
            st.session_state.onboarding_step = 0
            st.rerun()
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

    # wrapper can stay (CSS no longer depends on it)
    st.markdown('<div class="profile-area">', unsafe_allow_html=True)

    _render_avatar_section(profile)
    st.write("---")
    _render_personal_info(profile)
    st.write("---")
    _render_health_section(profile)

    st.markdown("</div>", unsafe_allow_html=True)
