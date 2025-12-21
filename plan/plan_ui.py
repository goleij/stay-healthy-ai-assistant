import streamlit as st
from ollama._types import ResponseError
import wave
import contextlib
import tempfile
import os

from storage.profile_manager import save_state_for_current_user
from llm_utils import get_llm
from .plan_generator import (
    make_day_prompt,
    normalize_meal_macros,
    sanitize_allergy_meals,
)
from .plan_css import inject_plan_css, inject_plan_toggle_css

from audio.recipe_parser import extract_meal_item, split_meals
from audio.recipe_llm import generate_recipe_steps
from audio.tts_coqui import speak
from audio.music_mixer import mix_tts_with_music


# ------------------- KONSTANTEN -------------------
INTENSITY_MUSIC = {
    "low": "assets/music/low.mp3",
    "medium": "assets/music/medium.mp3",
    "high": "assets/music/high.mp3",
}


# --------------------------------------------------
def concat_wavs(wav_paths: list[str]) -> str:
    """Fügt mehrere WAV-Dateien zu einer einzigen zusammen."""
    if not wav_paths:
        return None

    with contextlib.closing(wave.open(wav_paths[0], "rb")) as first:
        params = first.getparams()

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    output.close()

    with wave.open(output.name, "wb") as out:
        out.setparams(params)
        for path in wav_paths:
            with wave.open(path, "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))

    return output.name


# --------------------------------------------------
def _build_workout_schedule(workout_days: int, total_days: int = 7):
    schedule = [False] * total_days
    step = total_days / float(workout_days or 1)
    cur = 0.0
    for _ in range(workout_days):
        schedule[int(cur)] = True
        cur += step
    return schedule


# --------------------------------------------------
def split_plan_into_diet_and_workout(plan_text: str):
    diet, workout = [], []
    mode = None
    for line in plan_text.splitlines():
        lower = line.lower()
        if line.startswith("### Day "):
            diet.append(line)
            workout.append(line)
            mode = None
        elif "meals" in lower:
            diet.append(line)
            mode = "diet"
        elif "workout" in lower:
            workout.append(line)
            mode = "workout"
        elif mode in (None, "diet"):
            diet.append(line)
        else:
            workout.append(line)
    return "\n".join(diet), "\n".join(workout)


# --------------------------------------------------
def _render_plan_by_day(markdown_text: str, label: str):
    if not markdown_text.strip():
        return

    days = []
    current, buf = None, []

    for line in markdown_text.splitlines():
        if line.startswith("### Day "):
            if current:
                days.append((current, "\n".join(buf)))
            current, buf = line.replace("### ", ""), []
        else:
            buf.append(line)

    if current:
        days.append((current, "\n".join(buf)))

    for day_idx, (day_title, day_body) in enumerate(days):
        with st.expander(day_title, expanded=(day_idx == 0)):
            meals = split_meals(day_body)

            for meal_name, meal_block in meals.items():
                st.markdown(f"### {meal_name}")
                st.markdown(meal_block)

                btn_key = f"btn_play_{label}_{day_idx}_{meal_name}"

                if st.button("Voice Mode", key=btn_key):
                    with st.spinner("Voice Mode wird erstellt und vertont …"):
                        meal_item = extract_meal_item(meal_block)

                        steps = generate_recipe_steps(
                            model_name=st.session_state["model_name"],
                            meal_item=meal_item,
                        )

                        if not steps:
                            st.error("Voice Mode konnte nicht generiert werden.")
                            return

                        intensity = st.session_state.get("intensity", "medium")
                        music_path = INTENSITY_MUSIC[intensity]

                        wav_files = []
                        temp_files = []

                        for step in steps:
                            tts_wav = speak(step)
                            temp_files.append(tts_wav)

                            mixed = mix_tts_with_music(
                                tts_wav_path=tts_wav,
                                music_path=music_path,
                                music_gain_db=-22 if intensity == "low" else -18,
                            )

                            wav_files.append(mixed)
                            temp_files.append(mixed)

                        final_audio = concat_wavs(wav_files)

                    if final_audio:
                        st.success("🔊 Audio bereit")
                        st.audio(final_audio, autoplay=True)

                        # 🧹 Cleanup (SEHR WICHTIG)
                        for f in temp_files:
                            try:
                                os.remove(f)
                            except:
                                pass


# --------------------------------------------------
def render_plan_tab(model_name: str):
    st.session_state["model_name"] = model_name

    inject_plan_css()
    st.subheader("Your personalized fitness & diet plan")

    # -------- Intensität (User Choice) --------
    if "intensity" not in st.session_state:
        st.session_state["intensity"] = "medium"

    INTENSITY_LABELS = {
        "Low (Stretch / Mobility)": "low",
        "Medium (Strength)": "medium",
        "High (HIIT / Cardio)": "high",
    }

    label = st.select_slider(
        "Workout-Intensität",
        options=list(INTENSITY_LABELS.keys()),
        value="Medium (Strength)",
    )

    st.session_state["intensity"] = INTENSITY_LABELS[label]

    # -----------------------------------------
    profile = st.session_state.get("profile")
    if not profile:
        st.warning("No profile found.")
        return

    days = [f"Day {i}" for i in range(1, 8)]
    schedule = _build_workout_schedule(profile.get("workout_days", 3))

    try:
        if st.session_state.get("plan_text") is None:
            llm = get_llm(model_name)
            parts = []

            with st.spinner("Generating plan..."):
                for i, d in enumerate(days):
                    prompt = make_day_prompt(profile, d, schedule[i])
                    chunks = []
                    for c in llm.stream(prompt):
                        chunks.append(c)
                    parts.append(
                        f"### {d}\n{normalize_meal_macros(''.join(chunks))}"
                    )

            full = sanitize_allergy_meals(
                "\n".join(parts),
                profile.get("allergies", ""),
            )
            st.session_state.plan_text = full
            save_state_for_current_user()

        diet, workout = split_plan_into_diet_and_workout(
            st.session_state.plan_text
        )

        inject_plan_toggle_css()

        view = st.radio(
            "View",
            ["Meals", "Workout"],
            horizontal=True,
            label_visibility="collapsed",
        )

        # -------- Musik beim Wechsel zu Workout --------
        if "last_view" not in st.session_state:
            st.session_state.last_view = None

        if st.session_state.last_view != view and view == "Workout":
            intensity = st.session_state.get("intensity", "medium")
            st.audio(INTENSITY_MUSIC[intensity], autoplay=True)

        st.session_state.last_view = view
        # ----------------------------------------------

        if view == "Meals":
            _render_plan_by_day(diet, "Meals")
        else:
            _render_plan_by_day(workout, "Workout")

    except ResponseError:
        st.error("Model not found.")
    except Exception as e:
        st.error(str(e))
