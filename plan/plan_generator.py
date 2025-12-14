# plan/plan_generator.py
import re


def make_day_prompt(
    profile: dict,
    day_label: str,
    is_workout_day: bool,
    lang_code: str = "en",
) -> str:
    """
    Build the full LLM prompt for one specific day (meals + workout).

    The function is intentionally self-contained because it is called 7 times
    (once per day) from the UI.
    """

    goal = profile.get("goal", "Stay fit / Healthy")
    gender = profile.get("gender", "person")
    weight = profile.get("weight")
    height = profile.get("height")
    activity = profile.get("activity", "Moderate")
    diet = profile.get("diet", "No preference")
    age = profile.get("age")
    workout_days = profile.get("workout_days", 3)
    intensity = profile.get("intensity", "Medium")

    allergies = (profile.get("allergies") or "").strip()

    # Lists from onboarding
    health_conditions_raw = profile.get("health_conditions", []) or []
    limitations_raw = profile.get("limitations", []) or []

    health_conditions = [h.lower() for h in health_conditions_raw]
    limitations = [l.lower() for l in limitations_raw]

    has_diabetes = any("diabetes" in h for h in health_conditions)
    has_high_bp = any("blood pressure" in h for h in health_conditions)
    has_heart_disease = any("heart" in h for h in health_conditions)

    has_broken_arm = any("broken arm" in l for l in limitations)
    has_broken_leg = any("broken leg" in l for l in limitations)
    is_wheelchair_user = any("wheelchair" in l for l in limitations)

    # If user explicitly said "No significant limitation", ignore fuzzy matches
    if any("no significant" in l for l in limitations) and not (
        has_broken_arm or has_broken_leg or is_wheelchair_user
    ):
        has_broken_arm = has_broken_leg = is_wheelchair_user = False

    # ------------------------------------------------------------------
    # Labels (always English in the visible plan)
    # ------------------------------------------------------------------
    meals_label = "Meals"
    breakfast_label = "Breakfast"
    lunch_label = "Lunch"
    dinner_label = "Dinner"
    snacks_label = "Snack(s)"
    workout_heading = "Workout / Movement"
    warmup_heading = "Warm-up"
    workout_block_heading = "Workout"
    cooldown_heading = "Cool-down"
    health_heading = "Health summary & safety"
    important_heading = "Important notes"
    language_rule = "- Use only English (no other languages) in all headings and text.\n"

    # ------------------------------------------------------------------
    # Goal-related text
    # ------------------------------------------------------------------
    change_text = ""
    if profile.get("target_change") and goal in ["Lose weight", "Gain muscle"]:
        direction = "lose" if goal == "Lose weight" else "gain"
        change_text = f"They want to {direction} about {profile['target_change']} kg. "

    # ------------------------------------------------------------------
    # Health / limitation notes (only rendered as a section on Day 1)
    # ------------------------------------------------------------------
    condition_notes = []

    if has_diabetes:
        condition_notes.append("Use low-sugar, high-fiber meals (for diabetes).")
    if has_high_bp:
        condition_notes.append(
            "Use low-salt meals and avoid very salty processed foods (for high blood pressure)."
        )
    if has_heart_disease:
        condition_notes.append(
            "Avoid maximal-intensity exercise; training must stay at a comfortable, talk-friendly intensity."
        )

    if has_broken_arm:
        condition_notes.append(
            "Avoid exercises that load the injured arm (no push-ups, planks on hands or heavy pressing)."
        )
    if has_broken_leg:
        condition_notes.append(
            "Avoid exercises that load the injured leg (no squats, lunges, long walks or step-ups)."
        )
    if is_wheelchair_user:
        condition_notes.append(
            "Exercises must be wheelchair-friendly (seated upper-body and core; no walking or standing work)."
        )

    if age:
        if age >= 80:
            condition_notes.append(
                "Keep all movement very gentle, focus on balance and stability, and avoid fast changes of direction."
            )
        elif age >= 70:
            condition_notes.append(
                "Keep training low-impact and controlled; avoid heavy loads and fast changes of direction."
            )

    health_bullets_text = ""
    if condition_notes:
        health_bullets_text = "\n".join(f"- {n}" for n in condition_notes)

    show_health = day_label == "Day 1"

    # ------------------------------------------------------------------
    # Workout volume profile (uses age + intensity + heart condition)
    # ------------------------------------------------------------------
    intensity = (intensity or "Medium").capitalize()
    if intensity == "Light":
        move_profile = "gentle"
    elif intensity == "Intense":
        move_profile = "sporty"
    else:
        move_profile = "regular"

    # Safety caps for very old age or heart disease
    if age and age >= 80:
        move_profile = "very_gentle"
    elif age and age >= 70 and move_profile == "sporty":
        move_profile = "gentle"
    if has_heart_disease and move_profile == "sporty":
        move_profile = "gentle"

    if move_profile == "very_gentle":
        exercise_rule = "2–3 very simple exercises."
        sets_rule = (
            "Each exercise: 1–2 very easy sets of 8–10 reps OR 1–3 minutes of slow movement."
        )
        intensity_rule = (
            "All movements must be very gentle; the user should be able to talk comfortably at all times."
        )
    elif move_profile == "gentle":
        exercise_rule = "2–4 simple, low-impact exercises."
        sets_rule = (
            "Each exercise: 2 easy sets of 8–12 reps OR 2–5 minutes of light movement."
        )
        intensity_rule = (
            "Overall intensity should feel light to moderate, never all-out or breathless."
        )
    elif move_profile == "sporty":
        exercise_rule = "4–6 basic exercises."
        sets_rule = (
            "Each exercise: 3 sets of 10–15 reps OR 5–10 minutes of continuous work."
        )
        intensity_rule = (
            "Session should feel clearly challenging but still safe for a beginner; no maximal lifting or dangerous jumps."
        )
    else:  # regular
        exercise_rule = "3–5 basic exercises."
        sets_rule = (
            "Each exercise: 2–3 sets of 8–12 reps OR 5–8 minutes of light to moderate work."
        )
        intensity_rule = (
            "Intensity should feel like a solid beginner workout, not maximal effort."
        )

    # ------------------------------------------------------------------
    # Allowed movement patterns (adapted to limitations)
    # ------------------------------------------------------------------
    if is_wheelchair_user:
        allowed_moves = (
            "Use only seated or wheelchair-friendly upper-body and core movements "
            "such as seated band rows, seated shoulder presses with light weights, "
            "seated biceps curls, triceps extensions, torso rotations and seated core holds. "
            "Do NOT include squats, lunges, step-ups, walking, jogging or any leg exercise that requires standing."
        )
    elif has_broken_leg:
        allowed_moves = (
            "Focus on seated or lying upper-body and core movements only (for example: seated rows with a band, "
            "wall or table push-ups as tolerated, biceps curls, light shoulder presses and floor-based core work). "
            "Do NOT include squats, lunges, step-ups, long walks or any exercise that loads the injured leg."
        )
    elif has_broken_arm:
        allowed_moves = (
            "Use only lower-body and core movements that do not load the injured arm, such as: "
            "squats to a chair, step-ups, heel raises, gentle hip hinges, bridges and simple core holds where the "
            "injured arm can rest safely. Do NOT use push-ups, planks on hands, heavy rows or any exercise that "
            "has to bear weight on the injured arm."
        )
    else:
        if move_profile in ("very_gentle", "gentle"):
            allowed_moves = (
                "Use joint-friendly moves like: chair squats, wall push-ups, step-ups on a low step, "
                "slow marching in place, easy band rows, bridges and simple stretches."
            )
        elif move_profile == "sporty":
            allowed_moves = (
                "Use slightly more challenging but still safe moves like: deeper squats, lunges, step-ups, "
                "hip hinges, push-ups on a bench, rows, planks and short brisk walking intervals. "
                "No maximal lifting or risky jumps."
            )
        else:  # regular
            allowed_moves = (
                "Use basic bodyweight moves like: squats, lunges, glute bridges, incline push-ups, rows with bands, "
                "planks, brisk walking and simple stretches."
            )

    # ---- extra injury-specific rules for the workout section ----
    injury_rules_extra = ""
    warmup_note = ""
    if has_broken_arm:
        injury_rules_extra = (
            "- Because the arm is broken, you must NOT include any exercise that uses the arms, shoulders or hands. "
            "This means: no push-ups, wall push-ups, planks (on hands or elbows), rows, presses, curls, "
            "triceps work, band exercises, arm circles, shoulder rotations or any movement where the hands "
            "support bodyweight or move a load.\n"
            "- All exercises must use only legs and/or core while the injured arm rests safely.\n"
        )
        warmup_note = (
            " Warm-up movements must use only legs and trunk; do NOT add arm or shoulder movements."
        )
    elif has_broken_leg and not is_wheelchair_user:
        injury_rules_extra = (
            "- Because the leg is injured, you must NOT include squats, lunges, step-ups, jumps, long walks, marching "
            "or any movement that loads the injured leg. Use only seated or lying upper-body and core work.\n"
        )
        warmup_note = (
            " Do the warm-up seated or lying and do not load the injured leg in any way."
        )
    elif is_wheelchair_user:
        injury_rules_extra = (
            "- The user is a wheelchair user: all exercises must be done seated in the chair or in a safe seated position. "
            "Do NOT include walking, standing, squats, lunges, step-ups, jumps or floor transfers.\n"
        )
        warmup_note = " Do the warm-up fully seated in the wheelchair or on a stable chair."

    # ------------------------------------------------------------------
    # Workout / rest day explanation used inside the prompt
    # ------------------------------------------------------------------
    if intensity == "Light":
        intensity_phrase = "a gentle, low-intensity session"
    elif intensity == "Intense":
        intensity_phrase = "a higher-intensity beginner session"
    else:
        intensity_phrase = "a moderate-intensity beginner session"

    if is_workout_day:
        workout_context = (
            f"- Today IS a main workout day (one of {workout_days} workout days this week). "
            f"Create {intensity_phrase} and you MUST include the section '## {workout_heading}' exactly once.\n"
        )
    else:
        workout_context = (
            f"- Today IS a rest day. Do NOT create any section called '## {workout_heading}'. "
            "You may briefly remind the user to walk a bit and stretch, but no structured workout.\n"
        )

    # ------------------------------------------------------------------
    # Day index + variety themes for food
    # ------------------------------------------------------------------
    day_index = 1
    try:
        parts = day_label.split()
        if len(parts) >= 2 and parts[1].isdigit():
            day_index = int(parts[1])
    except Exception:
        day_index = 1

    day_themes = [
        {
            "breakfast": "warm, high-fiber bowl (oatmeal / porridge with fruit and nuts)",
            "lunch": "light plate with lean poultry or tofu and vegetables",
            "dinner": "simple fish or plant-protein dinner with roasted vegetables",
        },
        {
            "breakfast": "yogurt or quark bowl with fruit and seeds (no oatmeal)",
            "lunch": "whole-grain wrap or sandwich with lean protein and salad",
            "dinner": "stir-fry with rice or quinoa",
        },
        {
            "breakfast": "egg-based breakfast with some vegetables",
            "lunch": "hearty salad bowl with beans or lentils",
            "dinner": "baked or grilled poultry with potatoes or sweet potatoes",
        },
        {
            "breakfast": "smoothie-based breakfast with protein and fruit",
            "lunch": "soup or stew with vegetables and legumes",
            "dinner": "pasta-style dish with high-fiber pasta and a light sauce",
        },
        {
            "breakfast": "savory toast or bread-based breakfast with healthy toppings",
            "lunch": "grain bowl (quinoa, bulgur, etc.) with mixed vegetables and protein",
            "dinner": "fish or seafood dinner or similar vegetarian alternative",
        },
        {
            "breakfast": "muesli or granola-style breakfast with milk or yogurt",
            "lunch": "mixed plate with small portions of several items (mezze / tapas style)",
            "dinner": "lean red meat or meat-alternative with plenty of vegetables",
        },
        {
            "breakfast": "weekend-style breakfast such as protein pancakes or baked oats",
            "lunch": "simple, quick lunch such as an omelet with salad or baked potatoes",
            "dinner": "comfort-style but balanced casserole with vegetables",
        },
    ]

    idx = max(1, min(day_index, 7)) - 1
    theme = day_themes[idx]

    variety_instructions = f"""
Variety rules for this specific day:
- Breakfast theme today: {theme['breakfast']}.
- Lunch theme today: {theme['lunch']}.
- Dinner theme today: {theme['dinner']}.
- Across the 7 days, keep meals obviously different: do not repeat identical dishes.
- Rotate protein sources (eggs, yogurt, poultry, fish, legumes, tofu, etc.) and carbs (oats, bread, rice, potatoes, pasta, quinoa, etc.).
- Snacks today should be different from other days of the week.
"""

    # ------------------------------------------------------------------
    # Context info for the model (not shown in the visible plan)
    # ------------------------------------------------------------------
    context_info = f"""
Context for the model (do NOT repeat this text in the visible plan):
- Goal: {goal}. {change_text}
- Age: {age}
- Gender: {gender}
- Weight/height: {weight} kg, {height} cm
- Activity level: {activity}
- Planned weekly workouts: {workout_days}
- Health conditions (raw list): {health_conditions_raw}
- Limitations / injuries (raw list): {limitations_raw}
- Allergies (forbidden ingredients): {allergies or "none"}
- Move profile: {move_profile}
- Workout volume rule: {exercise_rule} {sets_rule}
- Intensity rule: {intensity_rule}
- Allowed exercise types: {allowed_moves}
- Never invent limitations that are not listed above and never mention wheelchairs if they are not in the profile.
"""

    # ------------------------------------------------------------------
    # Sections that only appear on some days
    # ------------------------------------------------------------------
    if show_health:
        health_section = f"""
## {health_heading}
Write 3–5 very short bullet points based on these hints:

{health_bullets_text or "- No special health restrictions today."}
"""
    else:
        health_section = f"Do NOT create a section named `{health_heading}` for this day.\n"

    if day_label == "Day 1":
        important_notes_section = f"""
## {important_heading}
- Add 3–4 short bullet points (hydration, listening to your body, stopping on pain, sleep, etc.)."""
    else:
        important_notes_section = f"Do NOT create a section named `{important_heading}` for this day.\n"

    if is_workout_day:
        workout_section = f"""
## {workout_heading}
This section must come AFTER Meals.

Start with this one sentence:
**You can do this workout any time you like — for example, around 11:00.**

### {warmup_heading}
- 2–5 minutes of simple movements (list 2–3 specific movements).{warmup_note}

### {workout_block_heading}
- Follow these safety rules exactly:
  - {exercise_rule}
  - {sets_rule}
  - {intensity_rule}
  - Only use movements from this style: {allowed_moves}
{injury_rules_extra}- Very important variety rules:
  - Do NOT use the exact same combination of these three exercises as the full workout:
    "Sit-to-stand from a chair", "Standing heel raises", "Short walk on flat ground".
  - If you use one of these exercises, you must also add 2–4 different exercises so that the workout is not identical every day.
  - Across the 7 days, vary the exercises (for example: some days wall push-ups, other days band rows, step-ups, hip hinges, bridges, side steps, etc.), and on this day at least half of the exercises must be different from the previous workout day.
  - Do NOT explain rules.  
  - Do NOT mention 'safety rules', 'sets rules', or variety rules.  
  - Just list the final exercises.
- Now list each exercise on its own bullet line with sets × reps OR minutes and a short rest time.

### {cooldown_heading}
- 3–10 minutes of easy walking or stretching (list 2–3 stretches).
"""
    else:
        workout_section = ""

    # ------------------------------------------------------------------
    # Final prompt
    # ------------------------------------------------------------------
    prompt = f"""
You are a professional fitness and nutrition coach.

Create a 1-day plan for **{day_label}** in clean markdown.

Global rules:
- Do NOT describe who the user is (no age, gender, weight in the text).
- No long paragraphs; use headings and bullet lists.
- Talk directly to "you", never to "people aged X" or "for those 70+".
- Never mention wheelchairs or broken limbs unless they appear in the profile limitations.
{language_rule}{workout_context}- The full 7-day plan must be varied; for this day follow the variety rules below.

{variety_instructions}

{health_section}

## {meals_label}
For each meal you MUST use EXACTLY this structure (no extra bullets, no sub-bullets):

### {breakfast_label}
- Item: short description with grams AND approximate calories at the end in parentheses, like "(~350 kcal)"
- Macros: Protein X g, Carbs X g, Fat X g

### {lunch_label}
- Item: short description with grams AND approximate calories at the end in parentheses, like "(~500 kcal)"
- Macros: Protein X g, Carbs X g, Fat X g

### {dinner_label}
- Item: short description with grams AND approximate calories at the end in parentheses, like "(~600 kcal)"
- Macros: Protein X g, Carbs X g, Fat X g

### {snacks_label}
- Item: short description with grams AND approximate calories at the end in parentheses, like "(~150–250 kcal)"
- Macros: Protein X g, Carbs X g, Fat X g

Meal rules:
- Respect diet preference: {diet}.
- Allergy rule (strict): the following ingredients are completely forbidden and must NEVER appear in any meal or snack: {allergies or "none"}.
- If the allergy list contains a word (for example "chicken"), do not use this ingredient in any form (meat, broth, stock, gravy, processed products, etc.).
- When writing each dish, mentally check that none of the allergy words appear in the ingredients.
- If diabetes is present: no sugar or sugary drinks; only clearly sugar-free desserts.
- If high blood pressure is present: low-salt meals, no very salty processed food.
- If joint, heart or mobility issues are present: prefer anti-inflammatory and heart-safe foods.
- Keep meals realistic and simple to cook at home.
- Show calories exactly once per meal, inside the Item line in parentheses.
- Always provide approximate numeric macros for every meal and every snack.
- The Item bullet MUST be a single bullet starting with "Item:" and MUST NOT contain the text "Macros:" anywhere.
- The Macros bullet MUST be a separate bullet on the next line, starting with "- Macros:" and containing Protein, Carbs and Fat in one line.
- Do NOT write macros after the Item in the same bullet (for example, "... (~500 kcal). Macros: ..." is forbidden).
- Do NOT use nested lists or sub-bullets under any Item or Macros line.
- Never write separate lines that start with only "Protein:", "Carbs:" or "Fat:".
- The words "leftover" and "leftovers" (in any form or case) are forbidden and must never appear.
- Do NOT use vague phrases like "last night's dinner", "yesterday's meal", "depends on what you choose" or "not provided".
- Every meal and snack must be a fully specified dish by itself (with its own ingredients, grams and calories).

{workout_section}

{important_notes_section}

{context_info}
"""
    return prompt


def normalize_meal_macros(text: str) -> str:
    """Post-process the model's markdown so that all meals follow the strict 'Item / Macros' format."""
    # Remove leftover / leftovers
    text = re.sub(r"\b[Ll]eftover[s]?\s*", "", text)

    lines = text.splitlines()
    out = []
    i = 0

    # First pass: fix inline "Item + Macros" bullets and collect broken macros scattered on extra lines.
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        # Case: "- Item ... (~500 kcal). Macros: Protein ..."
        # Split into two proper bullets: one Item bullet and one Macros bullet.
        if stripped.startswith("- ") and "Macros:" in stripped:
            before, after = stripped.split("Macros:", 1)
            before = before.rstrip().rstrip(".")
            out.append(before)
            macros_text = after.strip(" .")
            if macros_text:
                out.append(f"{indent}- Macros: {macros_text}")
            i += 1
            continue

        # Case: an Item bullet followed by nested Protein/Carbs/Fat lines
        if stripped.startswith("- ") and ("Item:" in stripped or "kcal" in stripped):
            out.append(line)

            j = i + 1
            protein = carbs = fat = None

            # Collect macros from subsequent lines that mention Protein/Carbs/Fat.
            while j < len(lines):
                s2 = lines[j].lstrip()

                if (s2.startswith(("-", "*", "•"))
                        and any(k in s2 for k in ["Protein", "Carbs", "Fat"])):
                    m = re.search(r"Protein[^0-9]*([\d]+ ?g?)", s2, re.I)
                    if m:
                        protein = m.group(1)
                    m = re.search(r"Carbs?[^0-9]*([\d]+ ?g?)", s2, re.I)
                    if m:
                        carbs = m.group(1)
                    m = re.search(r"Fat[^0-9]*([\d]+ ?g?)", s2, re.I)
                    if m:
                        fat = m.group(1)
                    j += 1
                    continue

                elif s2.startswith(("Protein", "Carbs", "Fat")):
                    m = re.search(r"Protein[^0-9]*([\d]+ ?g?)", s2, re.I)
                    if m:
                        protein = m.group(1)
                    m = re.search(r"Carbs?[^0-9]*([\d]+ ?g?)", s2, re.I)
                    if m:
                        carbs = m.group(1)
                    m = re.search(r"Fat[^0-9]*([\d]+ ?g?)", s2, re.I)
                    if m:
                        fat = m.group(1)
                    j += 1
                    continue
                else:
                    break

            # If we found any macro numbers, synthesize a clean single "- Macros: ..." bullet.
            if protein or carbs or fat:
                parts = []
                if protein:
                    parts.append(f"Protein {protein}")
                if carbs:
                    parts.append(f"Carbs {carbs}")
                if fat:
                    parts.append(f"Fat {fat}")
                out.append(f"{indent}- Macros: {', '.join(parts)}")

            i = j
            continue

        # Remove orphan bullets that are only Protein/Carbs/Fat without an Item.
        if stripped.startswith(("-", "*", "•")) and any(
            stripped.lstrip("-*• ").startswith(pfx)
            for pfx in ["Protein", "Carbs", "Fat"]
        ):
            i += 1
            continue

        # Default: keep the line as-is.
        out.append(line)
        i += 1

    # Second pass: remove empty bullets and duplicate Macros lines
    cleaned = []
    last_macros_norm = None

    for line in out:
        s = line.strip()

        # skip completely empty lines
        if not s:
            continue
        # skip bullets that only contain "-" / "*" / "•"
        if s in ("-", "*", "•"):
            continue

        # merge duplicate consecutive Macros bullets
        s_l = s.lstrip()
        if s_l.lower().startswith("- macros:"):
            norm = re.sub(r"\s+", "", s_l.lower())
            if norm == last_macros_norm:
                continue
            last_macros_norm = norm
        else:
            last_macros_norm = None

        cleaned.append(line)

    return "\n".join(cleaned)


def sanitize_allergy_meals(text: str, allergies: str) -> str:
    """
    Post-process LLM output so that allergy ingredients do NOT appear
    inside the visible Meals section. Only the part starting from
    "## Meals" is modified.
    """
    if not allergies or not allergies.strip():
        return text

    marker = "## Meals"
    idx = text.find(marker)
    if idx == -1:
        prefix = ""
        body = text
    else:
        prefix = text[:idx]
        body = text[idx:]

    # Build a list of allergy tokens from the free-text field
    raw_tokens = re.split(r"[;,/]| and | AND ", allergies)
    tokens = [t.strip().lower() for t in raw_tokens if t.strip()]

    if not tokens:
        return text

    def replacement_for(word: str) -> str:
        w = word.lower()
        if w in {"chicken", "poultry"}:
            return "tofu"
        if w in {"fish", "salmon", "tuna"}:
            return "tofu"
        if w in {"egg", "eggs"}:
            return "chickpea scramble"
        if w in {
            "nut",
            "nuts",
            "walnut",
            "walnuts",
            "almond",
            "almonds",
            "hazelnut",
            "hazelnuts",
            "peanut",
            "peanuts",
        }:
            return "seeds"
        # generic safe wording
        return "allergy-safe alternative"

    body_clean = body
    for word in tokens:
        repl = replacement_for(word)
        # singular
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        body_clean = pattern.sub(repl, body_clean)
        # simple plural
        pattern_plural = re.compile(rf"\b{re.escape(word)}s\b", re.IGNORECASE)
        body_clean = pattern_plural.sub(repl + "s", body_clean)

    return prefix + body_clean
