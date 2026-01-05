# onboarding/onboarding_ui.py

import streamlit as st
from ollama._types import ResponseError

from storage.profile_manager import save_state_for_current_user
from plan.plan_css import inject_plan_css
from .onboarding_css import inject_onboarding_css
from llm_utils import get_llm
from plan.plan_generator import (
    make_day_prompt,
    normalize_meal_macros,
    sanitize_allergy_meals,
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

# initialize session state for onboarding
def _init_onboarding_state() -> None:
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 0
    if "profile_draft" not in st.session_state:
        st.session_state.profile_draft = {}


# build a workout schedule distributing workout days evenly
def _build_workout_schedule(workout_days: int, total_days: int = 7):
    workout_days = max(0, min(workout_days, total_days))
    schedule = [False] * total_days

    if workout_days == 0:
        return schedule
    if workout_days == total_days:
        return [True] * total_days

    step = total_days / float(workout_days)
    indices = []
    current = 0.0

    for _ in range(workout_days):
        idx = int(current)
        if idx >= total_days:
            idx = total_days - 1
        indices.append(idx)
        current += step

    for idx in sorted(set(indices)):
        schedule[idx] = True

    return schedule


# navigation buttons for onboarding steps
def _nav_buttons(step_back: int, step_next: int, back_key: str, next_key: str) -> None:
    col_back, col_next = st.columns(2)
    with col_back:
        back_clicked = st.button("Back", key=back_key)
    with col_next:
        next_clicked = st.button("Next", key=next_key)

    if back_clicked:
        st.session_state.onboarding_step = step_back
        st.rerun()

    if next_clicked:
        st.session_state.onboarding_step = step_next
        st.rerun()


# render progress bar for onboarding steps
def _render_step_progress(step: int) -> None:
    total_questions = 10
    if step < 1 or step > total_questions:
        return
    percent = int(step / total_questions * 100)

    st.markdown(
        f"""
        <div style="
            width: 100%;
            background: #f2f2f2;
            height: 6px;
            border-radius: 999px;
            overflow: hidden;
            margin: 8px 0 24px 0;
        ">
            <div style="
                width: {percent}%;
                height: 100%;
                background: #009245;
            "></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# Loading overlay + plan generation (step 11)
# -------------------------------------------------------------------
def _render_loading_and_generate() -> None:
    profile = st.session_state.get("profile")
    if not profile:
        st.warning("No profile found. Please fill the form again.")
        if st.button("Back to start"):
            st.session_state.onboarding_step = 0
            st.rerun()
        return

    # HTML for full-screen overlay (CSS is now in onboarding_css.py)
    st.markdown(
        """
        <div class="loading-overlay">
          <div class="loading-title">We select an individual plan for you...</div>
          <div class="circle-outer">
            <div class="circle-mid">
              <div class="circle-inner">50%</div>
            </div>
          </div>
          <div class="loading-subtitle">Your plan is going to be ready...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # If plan already exists, jump directly to plan page
    if st.session_state.get("plan_text"):
        st.session_state.page = "main"
        st.session_state["main_view"] = "plan"
        save_state_for_current_user()
        st.rerun()
        return

    # Generate plan only once
    try:
        model_name = st.session_state.get("model_name") or "gemma2:2b"
        llm = get_llm(model_name)

        language_instruction = (
            "Answer entirely in English. Use clear and simple English."
        )
        days = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]

        workout_days = profile.get("workout_days", 3)
        workout_schedule = _build_workout_schedule(workout_days, total_days=len(days))

        plan_parts = []

        with st.spinner("Generating your personalized 7-day plan..."):
            for i, d in enumerate(days):
                is_workout = workout_schedule[i]
                base_prompt = make_day_prompt(profile, d, is_workout)
                prompt = language_instruction + "\n\n" + base_prompt

                chunks = []
                for chunk in llm.stream(prompt):
                    chunks.append(chunk)

                raw_text = "".join(chunks)

                allergies = profile.get("allergies", "")
                raw_text = sanitize_allergy_meals(raw_text, allergies)

                clean_text = normalize_meal_macros(raw_text)
                plan_parts.append(f"### {d}\n{clean_text}\n")

        st.session_state.plan_text = "\n".join(plan_parts)
        save_state_for_current_user()

        # After generation, go to main plan page
        st.session_state.page = "main"
        st.session_state["main_view"] = "plan"
        st.rerun()

    except ResponseError:
        st.error(
            f"❌ Model '{model_name}' not found on Ollama. "
            f"Open a terminal and run: `ollama pull {model_name}`."
        )
    except Exception as e:
        st.error(f"Unexpected error while generating plan: {e}")


# -------------------------------------------------------------------
# Public entry: onboarding wizard
# -------------------------------------------------------------------
def render_user_form() -> None:
    inject_plan_css()
    inject_onboarding_css()
    _init_onboarding_state()

    step = st.session_state.onboarding_step
    draft = st.session_state.profile_draft

    # STEP 11 is handled separately (no wrapper, full-screen overlay)
    if step == 11:
        _render_loading_and_generate()
        return

    # For steps 0–10 we show the normal card wrapper
    st.markdown('<div class="onboarding-wrapper">', unsafe_allow_html=True)
    st.write("")
    _render_step_progress(step)

    # ---------- STEP 0 ----------
    if step == 0:
        st.subheader("Welcome!")
        st.write(
            "We will ask you a few short questions about your body and goals "
            "so we can create a personalized 7-day plan."
        )
        if st.button("Start", key="step0_start"):
            st.session_state.onboarding_step = 1
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 1 ----------
    if step == 1:
        st.subheader("What is your name?")
        name = st.text_input("Name", value=draft.get("name", ""))

        if name.strip():
            draft["name"] = name.strip()
            st.session_state.profile_draft = draft

        _nav_buttons(0, 2, "step1_back", "step1_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 2 ----------
    if step == 2:
        st.subheader("What is your gender?")
        options = ["Male", "Female", "Prefer not to say"]
        gender = st.radio(
            "Gender",
            options,
            index=options.index(draft.get("gender", "Prefer not to say"))
            if draft.get("gender") in options
            else options.index("Prefer not to say"),
        )

        draft["gender"] = gender
        st.session_state.profile_draft = draft

        _nav_buttons(1, 3, "step2_back", "step2_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 3 ----------
    if step == 3:
        st.subheader("How old are you?")
        age = st.number_input(
            "Age",
            min_value=12,
            max_value=100,
            value=int(draft.get("age", 30)),
        )

        draft["age"] = int(age)
        st.session_state.profile_draft = draft

        _nav_buttons(2, 4, "step3_back", "step3_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 4 ----------
    if step == 4:
        st.subheader("What is your current weight?")
        weight = st.slider(
            "Weight (kg)", 40, 150, int(draft.get("weight", 70))
        )

        draft["weight"] = int(weight)
        st.session_state.profile_draft = draft

        _nav_buttons(3, 5, "step4_back", "step4_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 5 ----------
    if step == 5:
        st.subheader("How tall are you?")
        height = st.slider(
            "Height (cm)", 140, 210, int(draft.get("height", 170))
        )

        draft["height"] = int(height)
        st.session_state.profile_draft = draft

        _nav_buttons(4, 6, "step5_back", "step5_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 6 ----------
    if step == 6:
        st.subheader("Any limits, allergies or health conditions?")

        allergies = st.text_area(
            "Allergies (optional)",
            value=draft.get("allergies", ""),
            placeholder="e.g. peanuts, lactose, gluten...",
        )

        health_condition_options = ["Diabetes", "High blood pressure", "Heart disease"]
        existing_health = draft.get("health_conditions", [])
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
        existing_limits = draft.get("limitations", [])
        limitations = st.multiselect(
            "Physical limitations / handicap (optional)",
            handicap_options,
            default=existing_limits,
        )

        draft["allergies"] = allergies
        draft["health_conditions"] = health_conditions
        draft["limitations"] = limitations
        draft["health_issues"] = ", ".join(health_conditions + limitations)
        st.session_state.profile_draft = draft

        _nav_buttons(5, 7, "step6_back", "step6_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 7 ----------
    if step == 7:
        st.subheader("How fit are you?")
        labels = ["Not athletic", "Neutral", "Athletic"]

        fitness_choice = st.radio(
            "Choose the option that fits you best:",
            labels,
            index=labels.index(draft.get("fitness_level", "Neutral")),
        )

        mapping = {
            "Not athletic": "Low",
            "Neutral": "Moderate",
            "Athletic": "High",
        }

        draft["fitness_level"] = fitness_choice
        draft["activity"] = mapping[fitness_choice]
        st.session_state.profile_draft = draft

        _nav_buttons(6, 8, "step7_back", "step7_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 8 ----------
    if step == 8:
        st.subheader("How many days do you want to practice?")
        workout_days = st.slider(
            "Training days per week",
            1,
            7,
            int(draft.get("workout_days", 3)),
        )

        draft["workout_days"] = int(workout_days)
        st.session_state.profile_draft = draft

        _nav_buttons(7, 9, "step8_back", "step8_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 9 ----------
    if step == 9:
        st.subheader("How intense should your training be?")
        options = ["Light", "Medium", "Intense"]

        intensity = st.radio(
            "Training intensity",
            options,
            index=options.index(draft.get("intensity", "Medium")),
        )

        draft["intensity"] = intensity
        st.session_state.profile_draft = draft

        _nav_buttons(8, 10, "step9_back", "step9_next")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ---------- STEP 10 ----------
    if step == 10:
        st.subheader("What is your main goal?")
        options = ["Lose weight", "Gain muscle", "Stay fit / Healthy"]

        goal = st.radio(
            "Goal",
            options,
            index=options.index(draft.get("goal", "Stay fit / Healthy")),
        )

        if goal in ["Lose weight", "Gain muscle"]:
            direction = "lose" if goal == "Lose weight" else "gain (muscle)"
            target = st.slider(
                f"How many kilograms do you want to {direction}?",
                1,
                40,
                int(draft.get("target_change", 5)),
            )
        else:
            target = 0

        draft["goal"] = goal
        draft["target_change"] = int(target)
        st.session_state.profile_draft = draft

        col_back, col_next = st.columns(2)

        with col_back:
            if st.button("Back", key="step10_back"):
                st.session_state.onboarding_step = 9
                st.rerun()

        with col_next:
            if st.button("Continue", key="step10_finish"):
                health_conds = draft.get("health_conditions", [])
                limits = draft.get("limitations", [])
                fallback = ", ".join(health_conds + limits)

                profile = {
                    "name": draft.get("name", ""),
                    "gender": draft.get("gender", "Prefer not to say"),
                    "age": draft.get("age", 30),
                    "height": draft.get("height", 170),
                    "weight": draft.get("weight", 70),
                    "goal": draft.get("goal", "Stay fit / Healthy"),
                    "target_change": draft.get("target_change", 0),
                    "activity": draft.get("activity", "Moderate"),
                    "fitness_level": draft.get("fitness_level", "Neutral"),
                    "workout_days": draft.get("workout_days", 3),
                    "intensity": draft.get("intensity", "Medium"),
                    "diet": draft.get("diet", "No preference"),
                    "allergies": draft.get("allergies", ""),
                    "health_conditions": health_conds,
                    "limitations": limits,
                    "health_issues": draft.get("health_issues", fallback),
                }

                st.session_state.profile = profile
                st.session_state.plan_text = None
                st.session_state.chat_history = []
                st.session_state["profile_completed"] = True

                save_state_for_current_user()

                # Go to loading screen
                st.session_state.onboarding_step = 11
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Fallback safety
    st.session_state.onboarding_step = 0
    st.markdown("</div>", unsafe_allow_html=True)
