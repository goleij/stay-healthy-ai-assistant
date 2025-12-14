# plan/plan_ui.py


import streamlit as st
from ollama._types import ResponseError

from storage.profile_manager import save_state_for_current_user
from llm_utils import get_llm
from .plan_generator import (
    make_day_prompt,
    normalize_meal_macros,
    sanitize_allergy_meals,
)
from .plan_css import inject_plan_css, inject_plan_toggle_css


def render_shopping_list_clean(shopping_text: str) -> None:
    """Render a shopping list grouped by category with emojis."""
    if not shopping_text:
        st.info("No shopping list available yet.")
        return

    st.subheader("🛒 Shopping list")

    lines_raw = []
    for line in shopping_text.splitlines():
        if line.strip().startswith("```"):
            continue
        if "shopping list" in line.lower():
            continue
        lines_raw.append(line)
    text_no_fence = "\n".join(lines_raw)

    categories: dict[str, list[str]] = {}
    current_cat = "Other"

    for raw in text_no_fence.splitlines():
        line = raw.strip()
        if not line:
            continue

        line = line.lstrip("*-•").strip()
        plain = line.replace("**", "").strip()

        if plain.endswith(":"):
            cat_name = plain[:-1].strip() or "Other"
            current_cat = cat_name
            categories.setdefault(current_cat, [])
        else:
            lower_cat = current_cat.lower()
            if "note" in lower_cat:
                continue
            categories.setdefault(current_cat, []).append(line)

    cleaned_categories: dict[str, list[str]] = {}
    for name, items in categories.items():
        if not name:
            continue
        lower_name = name.lower()
        if "note" in lower_name:
            continue
        filtered = [it for it in items if it.strip()]
        if filtered:
            cleaned_categories[name] = filtered

    if not cleaned_categories:
        st.info("Shopping list is empty.")
        return

    emoji_map = {
        "fruit": "🍎",
        "fruits": "🍎",
        "vegetable": "🥦",
        "vegetables": "🥦",
        "veggies": "🥦",
        "produce": "🥦",
        "protein": "🍗",
        "proteins": "🍗",
        "meat": "🍖",
        "dairy": "🧀",
        "grain": "🌾",
        "grains": "🌾",
        "snack": "🥨",
        "snacks": "🥨",
        "other": "🛒",
    }

    def category_emoji(name: str) -> str:
        name_lower = name.lower()
        for key, emo in emoji_map.items():
            if key in name_lower:
                return emo
        return "🛒"

    cols = st.columns(2)
    idx = 0
    for cat_name, items in cleaned_categories.items():
        display_name = "Vegetables" if cat_name.lower() == "produce" else cat_name
        col = cols[idx % 2]
        idx += 1

        with col:
            emo = category_emoji(display_name)
            st.markdown(f"#### {emo} {display_name}")
            for item in items:
                st.markdown(
                    f'<div class="shopping-item">{item}</div>',
                    unsafe_allow_html=True,
                )


def _build_workout_schedule(workout_days: int, total_days: int = 7):
    """Return list[bool] of length total_days: True = workout day."""
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


def split_plan_into_diet_and_workout(plan_text: str) -> tuple[str, str]:
    """
    Split full 7-day plan markdown into:

    - diet_text: Day X + health summary + Meals/Breakfast/Lunch/Dinner/Snacks
    - workout_text: Day X + Workout / Movement + Important notes
    """
    if not plan_text:
        return "", ""

    diet_lines: list[str] = []
    workout_lines: list[str] = []

    mode = None  # None, "health", "meals", "workout"

    for line in plan_text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()

        # Day headings go into both
        if stripped.startswith("### Day "):
            diet_lines.append(line)
            workout_lines.append(line)
            mode = None
            continue

        # Detect headings
        if "health summary" in lower:
            diet_lines.append(line)
            mode = "health"
            continue

        if stripped.lower().startswith("meals"):
            diet_lines.append(line)
            mode = "meals"
            continue

        if "workout" in lower and "movement" in lower:
            workout_lines.append(line)
            mode = "workout"
            continue

        if "important notes" in lower:
            workout_lines.append(line)
            mode = "workout"
            continue

        # Empty line -> keep spacing in whichever views are active
        if not stripped:
            if mode in (None, "health", "meals"):
                diet_lines.append(line)
            if mode in (None, "workout"):
                workout_lines.append(line)
            continue

        # Content lines
        if mode in ("meals", "health", None):
            diet_lines.append(line)
        elif mode == "workout":
            workout_lines.append(line)

    # Add "Rest day" for days without workout content
    lines = workout_lines
    new_workout_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if not line.strip().startswith("### Day "):
            new_workout_lines.append(line)
            i += 1
            continue

        # Day header
        new_workout_lines.append(line)
        j = i + 1
        has_content = False

        # Look ahead until next "### Day ..."
        while j < len(lines) and not lines[j].strip().startswith("### Day "):
            if lines[j].strip():
                has_content = True
            j += 1

        if not has_content:
            new_workout_lines.append("")
            new_workout_lines.append(
                "Rest day – no structured workout planned. "
                "Focus on recovery, easy walking, and gentle stretching."
            )
            new_workout_lines.append("")
        else:
            for k in range(i + 1, j):
                new_workout_lines.append(lines[k])

        i = j

    return "\n".join(diet_lines).strip(), "\n".join(new_workout_lines).strip()


def _render_plan_by_day(markdown_text: str, label: str) -> None:
    """Render a 7-day markdown plan as expanders per day."""
    if not markdown_text or not markdown_text.strip():
        st.markdown(f"_No {label.lower()} details found in the plan._")
        return

    lines = markdown_text.splitlines()
    days: list[tuple[str, str]] = []

    current_day_title = None
    buffer: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### Day "):
            if current_day_title is not None:
                days.append((current_day_title, "\n".join(buffer).strip()))
            current_day_title = stripped.replace("### ", "").strip()
            buffer = []
        else:
            buffer.append(line)

    if current_day_title is not None:
        days.append((current_day_title, "\n".join(buffer).strip()))

    if not days:
        st.markdown(markdown_text)
        return

    for idx, (day_title, day_body) in enumerate(days):
        with st.expander(day_title, expanded=(idx == 0)):
            st.markdown(day_body or "_No content for this day._")


def render_plan_tab(model_name: str) -> None:
    """Render the 7-day fitness & diet plan and weekly shopping list."""
    inject_plan_css()
    st.subheader(" Your personalized fitness & diet plan")

    profile = st.session_state.get("profile", {})
    if not profile:
        st.warning("No profile found. Please go back and fill the form.")
        if st.button("Go to form"):
            st.session_state.page = "form"
            st.rerun()
        return

    language_instruction = "Answer entirely in English. Use clear and simple English."
    days = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
    workout_days = profile.get("workout_days", 3)
    workout_schedule = _build_workout_schedule(workout_days, total_days=len(days))

    try:
        # Generate plan if missing
        if st.session_state.get("plan_text") is None:
            llm = get_llm(model_name)
            st.session_state.plan_text = ""
            plan_parts: list[str] = []

            with st.spinner(" Generating your personalized 7-day plan..."):
                for i, d in enumerate(days):
                    st.markdown(f"### {d}")
                    is_workout_day = workout_schedule[i]
                    base_prompt = make_day_prompt(profile, d, is_workout_day)
                    prompt = language_instruction + "\n\n" + base_prompt

                    day_placeholder = st.empty()
                    chunks: list[str] = []

                    for chunk in llm.stream(prompt):
                        chunks.append(chunk)
                        partial = "".join(chunks)
                        day_placeholder.markdown(partial)

                    raw_text = "".join(chunks)
                    clean_text = normalize_meal_macros(raw_text)
                    plan_parts.append(f"### {d}\n{clean_text}\n")

            # Join all days and apply allergy sanitization once on the full plan
            full_plan = "\n".join(plan_parts)
            allergies = profile.get("allergies", "")
            full_plan = sanitize_allergy_meals(full_plan, allergies)

            st.session_state.plan_text = full_plan
            save_state_for_current_user()

        else:
            # We already have a plan -> optionally re-sanitize for current allergies
            plan_text = st.session_state.get("plan_text", "")
            allergies = profile.get("allergies", "")
            if allergies:
                plan_text = sanitize_allergy_meals(plan_text, allergies)
                st.session_state.plan_text = plan_text

            diet_text, workout_text = split_plan_into_diet_and_workout(plan_text)

            inject_plan_toggle_css()

            if "plan_view" not in st.session_state:
                st.session_state["plan_view"] = "Meals"

            view = st.radio(
                "Plan view",
                ["Meals", "Workout"],
                horizontal=True,
                key="plan_view",
                label_visibility="collapsed",
            )

            if view == "Meals":
                _render_plan_by_day(diet_text, "Meals")
            else:
                _render_plan_by_day(workout_text, "Workout")

    except ResponseError:
        st.error(
            f"❌ Model '{model_name}' not found on Ollama. "
            f"Open a terminal and run: `ollama pull {model_name}`."
        )
    except Exception as e:
        st.error(f"Unexpected error: {e}")

    # Shopping list generation – only when Meals view is active
    if (
            st.session_state.get("plan_text")
            and st.session_state.get("plan_view") == "Meals"
    ):
        if st.button("🛒 Generate weekly shopping list"):
            try:
                llm = get_llm(model_name)

                profile = st.session_state.get("profile", {})
                allergies = (profile.get("allergies") or "").strip()

                # Use only the Meals part of the plan for the shopping list
                full_plan = st.session_state.plan_text
                idx = full_plan.find("## Meals")
                if idx != -1:
                    plan_for_list = full_plan[idx:]
                else:
                    plan_for_list = full_plan

                if allergies:
                    allergy_rule = (
                        "The user is allergic to the following ingredients: "
                        f"{allergies}. These allergy words must NOT appear "
                        "anywhere in the shopping list, not even as 'X-free'. "
                        "If a meal already avoids these ingredients, just list "
                        "what is written; do not invent special 'X-free' products."
                    )
                else:
                    allergy_rule = ""

                prompt = (
                    "Answer in English. Use clear bullet points.\n\n"
                    "You are a nutrition assistant. Based on the following 7-day "
                    "meal plan in markdown, create a consolidated shopping list "
                    "for all meals.\n\n"
                    "VERY IMPORTANT RULES:\n"
                    "- Build the shopping list ONLY from ingredients that are "
                    "explicitly mentioned in the Meals section of the plan.\n"
                    "- Do NOT add any new ingredient, brand or product that is "
                    "not present in the meals text.\n"
                    "- If something is not written in the meals (for example "
                    "special protein powders, supplements, etc.), do NOT add it.\n"
                    "- You may group repeated ingredients together and sum their "
                    "amounts, but the ingredient names themselves must come from "
                    "the plan.\n\n"
                    "Group the items into logical categories (Vegetables, Fruits, "
                    "Proteins, Dairy, Grains, Other).\n\n"
                    f"{allergy_rule}\n\n"
                    f"PLAN (Meals only):\n{plan_for_list}\n\n"
                    "Now output ONLY the shopping list in markdown."
                )

                with st.spinner("🛒 Generating shopping list for the week..."):
                    chunks: list[str] = []
                    for chunk in llm.stream(prompt):
                        chunks.append(chunk)
                    shopping_text = "".join(chunks).strip()

                st.session_state["weekly_shopping_list"] = shopping_text
                save_state_for_current_user()
            except ResponseError:
                st.error(
                    f"❌ Model '{model_name}' not found on Ollama. "
                    f"Open a terminal and run: `ollama pull {model_name}`."
                )
            except Exception as e:
                st.error(f"Unexpected error while creating shopping list: {e}")

        shopping_text = st.session_state.get("weekly_shopping_list")
        if shopping_text:
            render_shopping_list_clean(shopping_text)

    # Reset button
    if st.button("🔁 Start over (new plan)"):
        st.session_state.page = "form"
        st.session_state.profile = {}
        st.session_state.plan_text = None
        st.session_state.chat_history = []
        st.session_state.pop("weekly_shopping_list", None)
        save_state_for_current_user()
        st.rerun()

