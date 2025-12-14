from __future__ import annotations

from typing import Optional

import streamlit as st

from .meditation_css import inject_meditation_css
from .meditation_logic import (
    MeditationConfig,
    create_meditation_audio,
    delete_meditation,
    generate_meditation_text,
    list_saved_meditations,
    load_meditation,
    save_meditation,
)


def _init_state() -> None:
    state = st.session_state
    state.setdefault("med_category", "Mindfulness")
    state.setdefault("med_length", "medium")
    state.setdefault("med_ambient", "forest")
    state.setdefault("med_music_db", -20)
    state.setdefault("med_text", "")
    state.setdefault("med_audio", None)
    state.setdefault("med_last_error", None)
    state.setdefault("med_title", "")


def _category_selector() -> None:
    st.markdown("#### Style")

    cols = st.columns(4)
    labels = ["Mindfulness", "Breathing", "Body Scan", "Sleep"]

    for col, label in zip(cols, labels):
        with col:
            is_selected = st.session_state.med_category == label
            button_label = f"✅ {label}" if is_selected else label
            if st.button(button_label, use_container_width=True, key=f"cat_{label}"):
                st.session_state.med_category = label


def _length_selector() -> None:
    st.markdown("#### Length")
    st.radio(
        "",
        ("short", "medium", "long"),
        index=("short", "medium", "long").index(st.session_state.med_length),
        key="med_length",
        horizontal=True,
        label_visibility="collapsed",
    )


def _ambient_selector() -> None:
    st.markdown("#### Ambient Style")
    st.radio(
        "",
        ("waves", "forest", "rain", "none"),
        index=("waves", "forest", "rain", "none").index(st.session_state.med_ambient),
        key="med_ambient",
        horizontal=True,
        label_visibility="collapsed",
    )


def _sidebar_nav() -> str:
    with st.sidebar:
        st.markdown("## 🧘 Meditation Studio")
        choice = st.radio(
            "",
            ("New Meditation", "Saved Meditations"),
            label_visibility="collapsed",
        )
    return choice


def _render_new_meditation() -> None:
    st.markdown("### Create a new guided meditation")

    col_left, col_right = st.columns(2)

    with col_left:
        _category_selector()
        _length_selector()

    with col_right:
        _ambient_selector()
        st.markdown("Music volume (background vs. voice)")
        st.slider(
            "",
            min_value=-30,
            max_value=5,
            value=st.session_state.med_music_db,
            step=1,
            key="med_music_db",
            label_visibility="collapsed",
        )

    if st.button("✨ Generate Meditation", type="primary"):
        cfg = MeditationConfig(
            category=st.session_state.med_category,
            length=st.session_state.med_length,
            ambient_style=st.session_state.med_ambient,
            music_volume_db=st.session_state.med_music_db,
        )

        text = generate_meditation_text(cfg.category, cfg.length)
        st.session_state.med_text = text
        st.session_state.med_last_error = None

        with st.spinner("Creating audio with your cloned voice…"):
            audio_bytes, err = create_meditation_audio(
                text,
                cfg.ambient_style,
                cfg.music_volume_db,
            )
        st.session_state.med_audio = audio_bytes
        st.session_state.med_last_error = err

        st.success("Meditation created!")

    if st.session_state.med_last_error:
        st.warning(st.session_state.med_last_error)

    if st.session_state.med_text:
        st.markdown("#### 📝 Meditation Text")
        st.text_area(
            "",
            value=st.session_state.med_text,
            height=260,
            label_visibility="collapsed",
        )

    if st.session_state.med_audio:
        st.markdown("#### 🔊 Preview Audio")
        st.audio(st.session_state.med_audio, format="audio/wav")

    st.markdown("---")
    st.markdown("#### Save this meditation")

    st.text_input(
        "Give your meditation a title",
        key="med_title",
        placeholder="e.g., Evening Forest Calm",
    )

    if st.button("💾 Save Meditation"):
        if not st.session_state.med_text:
            st.error("Please generate a meditation before saving.")
        elif not st.session_state.med_title.strip():
            st.error("Please enter a title.")
        else:
            cfg = MeditationConfig(
                category=st.session_state.med_category,
                length=st.session_state.med_length,
                ambient_style=st.session_state.med_ambient,
                music_volume_db=st.session_state.med_music_db,
            )
            save_meditation(
                st.session_state.med_title.strip(),
                cfg,
                st.session_state.med_text,
                st.session_state.med_audio,
            )
            st.success("Meditation saved.")


def _render_saved_meditations() -> None:
    st.markdown("### Saved Meditations")

    items = list_saved_meditations()
    if not items:
        st.info("No meditations saved yet. Create one on the *New Meditation* page.")
        return

    for item in items:
        slug = item["slug"]
        with st.expander(f'{item["title"]} — {item["category"]}, {item["length"]}'):
            text, audio = load_meditation(slug)
            st.markdown("**Text**")
            st.text_area(
                "",
                value=text,
                height=220,
                label_visibility="collapsed",
            )
            if audio:
                st.markdown("**Audio**")
                st.audio(audio, format="audio/wav")

            cols = st.columns(2)
            with cols[0]:
                if st.button("Load into editor", key=f"load_{slug}"):
                    st.session_state.med_text = text
                    st.session_state.med_audio = audio
                    st.session_state.med_category = item["category"]
                    st.session_state.med_length = item["length"]
                    st.session_state.med_ambient = item.get("ambient_style", "forest")
                    st.session_state.med_title = item["title"]
                    st.success("Loaded into the editor on the *New Meditation* page.")
            with cols[1]:
                if st.button("🗑 Delete", key=f"del_{slug}"):
                    delete_meditation(slug)
                    st.experimental_rerun()


def render_meditation_page() -> None:
    inject_meditation_css()
    _init_state()

    page = _sidebar_nav()

    if page == "New Meditation":
        _render_new_meditation()
    else:
        _render_saved_meditations()
