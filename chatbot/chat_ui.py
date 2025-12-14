import streamlit as st
from ollama._types import ResponseError

from storage.profile_manager import save_state_for_current_user
from llm_utils import get_llm, get_qa
from .chat_css import inject_chat_css


# ---------- helpers for multi-chat sessions ----------

# add multi-chat support in session_state
def _ensure_chat_sessions() -> None:
    """Ensure we have a multi-chat structure in session_state.

    chat_sessions: {
        chat_id: {"title": str, "history": list[(speaker, message)]}
    }
    current_chat_id: active chat.
    """
    sessions = st.session_state.get("chat_sessions")

    if not sessions:
        sessions = {}
        old_history = st.session_state.get("chat_history", [])
        first_id = "chat_1"
        sessions[first_id] = {
            "title": "Chat 1",
            "history": list(old_history),
        }
        st.session_state["chat_sessions"] = sessions
        st.session_state["current_chat_id"] = first_id

    # Ensure current_chat_id is valid
    current_id = st.session_state.get("current_chat_id")
    if current_id not in sessions:
        current_id = next(iter(sessions))
        st.session_state["current_chat_id"] = current_id

    # Alias chat_history to the current session's history (for existing code)
    st.session_state.chat_history = st.session_state["chat_sessions"][current_id][
        "history"
    ]

# accessing or updating the active chat's data in a multi-chat interface
def _get_current_session():
    sessions = st.session_state["chat_sessions"]
    current_id = st.session_state["current_chat_id"]
    return current_id, sessions[current_id]


# ---------- helpers using chat_history alias ----------


def _build_history_text(max_turns: int = 6) -> str:
    history = st.session_state.get("chat_history", [])
    if not history:
        return ""
    recent = history[-max_turns * 2 :]
    lines = []
    for speaker, msg in recent:
        role = "User" if speaker == "user" else "Coach"
        lines.append(f"{role}: {msg}")
    return "\n".join(lines)


def _build_health_context(profile: dict) -> str:
    """Build safety rules from profile: diseases, allergies, limitations."""
    health_issues = (profile.get("health_issues") or "").strip()
    allergies = (profile.get("allergies") or "").strip()
    text = (health_issues + " " + allergies).lower()

    rules = []

    if health_issues:
        rules.append(
            f"The user has these health conditions or limitations: {health_issues}."
        )

    if "diabetes" in text:
        rules.append(
            "Treat the user as having diabetes for all meal and recipe suggestions: "
            "avoid added sugar, sugary drinks, sweets and white flour. "
            "Prefer high-fiber carbohydrates and balanced meals. "
            "If you suggest cookies, cake or desserts, they must be clearly sugar-free "
            "and you must say so. Do not recommend syrups or fruit juice as 'healthy' sweeteners."
        )

    if "high blood pressure" in text or "hypertension" in text:
        rules.append(
            "For high blood pressure: keep meals low in salt, avoid very salty processed foods "
            "(chips, instant noodles, cured meats, ready-made sauces) and prefer heart-friendly "
            "foods like vegetables, fruits, whole grains, unsalted nuts, olive oil and fish."
        )

    if "heart disease" in text or "heart condition" in text:
        rules.append(
            "The user has a heart condition: only suggest moderate-intensity exercise. "
            "No HIIT, no sprints, no maximal effort intervals. "
            "Prefer steady, comfortable activities such as walking or gentle cycling. "
            "Always mention that they should follow their doctor's advice."
        )

    if "joint" in text or "knee" in text:
        rules.append(
            "The user has joint problems: avoid high-impact exercises like running, jumping "
            "and deep heavy squats. Prefer low-impact options such as walking on flat ground, "
            "cycling, swimming, chair squats, wall push-ups, light band exercises and gentle mobility work."
        )

    if "asthma" in text or "lung" in text:
        rules.append(
            "The user has asthma or lung issues: avoid very intense, breathless intervals and sprints. "
            "Recommend gradual warm-ups and give enough rest between efforts."
        )

    # Physical limitations / handicap
    if "broken arm" in text:
        rules.append(
            "The user has a broken arm or strong limitation in one arm: "
            "avoid exercises that load that arm (push-ups, heavy pressing, pull-ups). "
            "Prefer lower-body and core exercises and safe cardio."
        )

    if "broken leg" in text:
        rules.append(
            "The user has a broken leg or strong limitation in one leg: "
            "avoid standing and impact exercises on that leg. "
            "Prefer seated upper-body work, core work and safe, doctor-approved rehab."
        )

    if "wheelchair" in text or "severe mobility limitation" in text:
        rules.append(
            "The user uses a wheelchair or has severe mobility limitation: "
            "focus on seated or lying exercises, upper-body strength, core stability, "
            "and gentle range-of-motion work. Do not suggest walking, running, jumping or standing balance drills."
        )

    if allergies:
        rules.append(
            f"The user is allergic or intolerant to: {allergies}. "
            "Never include these ingredients or very similar products in any recipe or suggestion. "
            "Do not include peanuts if they are allergic to peanuts; do not include tree nuts if they are allergic "
            "to tree nuts, and so on. Always propose safe alternative ingredients."
        )

    if not rules:
        return ""

    return "Health and safety context:\n" + "\n".join(f"- {r}" for r in rules) + "\n"


def _get_last_coach_message() -> str | None:
    history = st.session_state.get("chat_history", [])
    for speaker, msg in reversed(history):
        if speaker == "coach":
            return msg
    return None


def _get_last_user_message() -> str | None:
    history = st.session_state.get("chat_history", [])
    for speaker, msg in reversed(history):
        if speaker == "user":
            return msg
    return None

# show recipe tools (save, shopping list) based on last messages
def _should_show_recipe_tools(last_user: str | None, last_coach: str | None) -> bool:
    if not last_coach:
        return False
    
    combined = ((last_user or "") + "\n" + last_coach).lower()

    keywords = [
        "recipe",
        "recipie",
        "recepie",
        "meal",
        "breakfast",
        "lunch",
        "dinner",
        "snack",
        "dessert",
        "shopping list",
        "ingredients",
        "meal plan",
        "dish",
        "cook",
        "cookie",
        "biscuit",
    ]

    if any(kw in combined for kw in keywords):
        return True

    lines = [ln.strip() for ln in last_coach.splitlines() if ln.strip()]
    bullet_like = [
        ln
        for ln in lines
        if ln[0:1] in ("-", "*", "•") or (len(ln) > 2 and ln[:2].isdigit())
    ]

    if len(bullet_like) >= 3:
        return True

    return False


def _extract_recipe_title(text: str) -> str:
    if not text:
        return "Recipe shopping list"

    first_line = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            first_line = stripped
            break

    if not first_line:
        return "Recipe shopping list"

    while first_line and first_line[0] in "#*-•":
        first_line = first_line[1:].strip()

    if ":" in first_line:
        lower = first_line.lower()
        if " for " in lower:
            after_for = first_line.split("for", 1)[1]
            title = after_for.split(":", 1)[0].strip()
        else:
            title = first_line.split(":", 1)[1].strip()
    else:
        title = first_line.strip()

    return title or "Recipe shopping list"


# ---------- main UI ----------


def render_chat_tab(model_name: str):
    inject_chat_css()
    _ensure_chat_sessions()

    sessions = st.session_state["chat_sessions"]
    current_id, current_session = _get_current_session()

    col_left, col_right = st.columns([1.1, 3])

    # ----- left column: chat list -----
    with col_left:
        st.markdown('<div class="chat-sidebar-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chat-sidebar-title">Your chats</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="chat-sidebar-subtitle">'
            "Switch between conversations or start a new one."
            "</div>",
            unsafe_allow_html=True,
        )

        if st.button(" New chat"):
            new_index = len(sessions) + 1
            new_id = f"chat_{new_index}"
            sessions[new_id] = {"title": f"Chat {new_index}", "history": []}
            st.session_state["current_chat_id"] = new_id
            st.session_state.chat_history = sessions[new_id]["history"]
            save_state_for_current_user()
            st.rerun()

        st.markdown('<div class="chat-sidebar-list">', unsafe_allow_html=True)
        for chat_id, data in sessions.items():
            title = data.get("title") or chat_id
            if len(title) > 32:
                title = title[:29] + "..."
            is_selected = chat_id == current_id
            prefix = "▶  " if is_selected else "💬  "
            button_label = f"{prefix}{title}"
            if st.button(button_label, key=f"select_{chat_id}"):
                st.session_state["current_chat_id"] = chat_id
                st.session_state.chat_history = sessions[chat_id]["history"]
                save_state_for_current_user()
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ----- right column: active chat -----
    with col_right:
        st.markdown('<div class="chat-main-card">', unsafe_allow_html=True)

        st.markdown(
            '<div class="chat-main-header">🤖 <span>Your AI Fitness Coach Chatbot</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="chat-main-description">'
            "Ask me anything about your plan, workouts, or health-friendly recipes!"
            "</div>",
            unsafe_allow_html=True,
        )

        if st.button(" Clear this chat"):
            st.session_state.chat_history.clear()
            save_state_for_current_user()
            st.success("Current chat has been reset.")
            st.rerun()

        if st.session_state.chat_history:
            for speaker, message in st.session_state.chat_history:
                if speaker == "user":
                    st.markdown(f"**🧍 You:** {message}")
                else:
                    st.markdown(f"**🏋️ Coach:** {message}")

        last_coach = _get_last_coach_message()
        last_user = _get_last_user_message()
        if last_coach and _should_show_recipe_tools(last_user, last_coach):
            st.markdown("**Last coach message tools:**")
            tools_col1, tools_col2 = st.columns(2)

            with tools_col1:
                if st.button("💾 Save as recipe"):
                    recipes = st.session_state.get("saved_recipes", [])
                    recipes.append(last_coach)
                    st.session_state["saved_recipes"] = recipes
                    save_state_for_current_user()
                    st.success("Saved to your recipes in the profile page.")

            with tools_col2:
                if st.button("🛒 Create shopping list from last answer"):
                    try:
                        llm = get_llm(model_name)
                        prompt = (
                            "Answer in English.\n\n"
                            "You are a nutrition assistant. Based on the following recipe or meal plan, "
                            "extract a clean shopping list. Group ingredients by category if reasonable "
                            "(for example: Vegetables, Fruits, Proteins, Dairy, Grains, Other). "
                            "Use bullet points and include approximate amounts if they are present.\n\n"
                            f"TEXT:\n{last_coach}\n\n"
                            "Now output ONLY the shopping list in markdown."
                        )
                        with st.spinner("🛒 Generating shopping list..."):
                            shopping_text = st.write_stream(llm.stream(prompt))

                        recipe_title = _extract_recipe_title(last_coach)
                        st.session_state["last_recipe_shopping_title"] = recipe_title
                        st.session_state["last_shopping_list"] = shopping_text

                        save_state_for_current_user()
                        st.success("Shopping list saved.")
                    except ResponseError:
                        st.error(
                            f"❌ Model '{model_name}' not found. Run: `ollama pull {model_name}` or pick another."
                        )
                    except Exception as e:
                        st.error(f"Unexpected error while creating shopping list: {e}")

        use_rag = st.toggle(
            "Use knowledge base (RAG)",
            value=False,
            help="Turn on to answer using your prepared data.",
        )

        user_input = st.text_input("Type your question here 👇")

        if st.button("Send "):
            text = user_input.strip()
            if not text:
                st.markdown("</div>", unsafe_allow_html=True)
                return

            profile = st.session_state.get("profile", {})
            language_instruction = "Answer in English."

            lower_input = text.lower()
            recipe_keywords = [
                "recipe",
                "recipie",
                "recepie",
                "meal",
                "breakfast",
                "lunch",
                "dinner",
                "snack",
                "dessert",
                "cookies",
                "cookie",
                "biscuit",
            ]
            wants_recipe = any(kw in lower_input for kw in recipe_keywords)

            profile_context = (
                f"The user is a {profile.get('age', 'unknown-age')} year old "
                f"{profile.get('gender', 'person')} weighing {profile.get('weight')} kg, "
                f"height {profile.get('height')} cm. "
                f"Main goal: {profile.get('goal')}, target change: {profile.get('target_change', 0)} kg. "
                f"Activity level: {profile.get('activity')}, diet preference: {profile.get('diet')}. "
                f"They want to work out about {profile.get('workout_days', 3)} days per week.\n"
            )

            health_context = _build_health_context(profile)
            history_text = _build_history_text(max_turns=6)

            system_instructions = (
                "You are an expert fitness and nutrition coach. "
                "Use the profile information and health context to give safe, personalized advice. "
                "When the user asks for meals or recipes, always adapt them to their diet preference, "
                "health conditions, allergies and physical limitations. "
                "For exercise questions, always respect joint, heart, lung and mobility limitations. "
                "Be concise and precise. This is general information, not medical advice. "
            )

            if wants_recipe:
                system_instructions += (
                    "The next user message is a DIRECT request for a recipe. "
                    "You MUST immediately provide exactly ONE concrete recipe adapted to their "
                    "health context and diet preference. "
                    "Your answer MUST be structured as:\n"
                    "- A level-3 markdown heading with the recipe name.\n"
                    "- A bullet list of ingredients with exact amounts.\n"
                    "- A numbered list of clear, step-by-step instructions.\n"
                    "Do NOT ask the user any questions. "
                    "Do NOT suggest alternatives instead of giving the recipe. "
                    "Do NOT start with motivational text or long explanations before the recipe. "
                    "You may add ONE short tip sentence at the very end if helpful.\n"
                    "Make sure the recipe name, the ingredients list and the instructions are strictly consistent. "
                    "If the recipe name or user request mentions a key ingredient (for example: apple, banana, "
                    "chicken, chocolate, etc.), that ingredient must appear as a real ingredient in the list and be "
                    "used in the instructions, unless it conflicts with allergies or health rules. "
                    "If you must omit a requested ingredient for safety reasons, clearly explain that it is omitted "
                    "and choose a different recipe name that does not mention it. "
                    "Never mention an ingredient in the title that is not present in the ingredients list.\n"
                )
            else:
                system_instructions += (
                    "If the question is very unclear or self-contradictory and not obviously about a recipe, "
                    "you may ask 1–2 short clarifying questions instead of guessing. "
                )

            system_instructions += language_instruction + "\n"

            full_prompt = system_instructions + "\n" + profile_context + health_context

            if history_text:
                full_prompt += f"\nConversation so far:\n{history_text}\n"

            if wants_recipe:
                full_prompt += (
                    "\nThe user request below is a direct request for a RECIPE. "
                    "Respond exactly with one recipe in the format described above.\n"
                )

            full_prompt += f"\nUser: {text}\nCoach:"

            try:
                if use_rag:
                    qa = get_qa(model_name)
                    with st.spinner(" Coach is thinking with knowledge base..."):
                        answer = qa({"query": full_prompt})["result"]
                else:
                    llm = get_llm(model_name)
                    with st.spinner("🏃 Streaming..."):
                        answer = st.write_stream(llm.stream(full_prompt))

                    if wants_recipe:
                        requested_keywords = []
                        for kw in [
                            "apple",
                            "banana",
                            "chicken",
                            "beef",
                            "fish",
                            "salmon",
                            "chocolate",
                        ]:
                            if kw in lower_input:
                                requested_keywords.append(kw)

                        for kw in requested_keywords:
                            if kw not in str(answer).lower():
                                fix_prompt = (
                                    f"{language_instruction}\n\n"
                                    "You previously generated the following recipe:\n\n"
                                    f"{answer}\n\n"
                                    f"The original user request explicitly mentioned '{kw}', but this ingredient "
                                    "does not appear in the ingredients list. "
                                    "Rewrite the recipe so that this ingredient is included as a real ingredient and "
                                    "used in the instructions, unless it is unsafe because of the health context "
                                    "(allergies or medical rules). "
                                    "If you must omit it for safety, clearly say so and choose a different recipe name "
                                    "that does not mention it. "
                                    "Output only the corrected recipe in markdown, using the same structure "
                                    "as before (heading, ingredients list, numbered steps)."
                                )
                                with st.spinner("🔁 Fixing recipe for consistency..."):
                                    answer = st.write_stream(llm.stream(fix_prompt))
                                break

            except ResponseError:
                st.error(
                    f"❌ Model '{model_name}' not found. Run: `ollama pull {model_name}` or pick another."
                )
                st.markdown("</div>", unsafe_allow_html=True)
                return
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            st.session_state.chat_history.append(("user", text))
            st.session_state.chat_history.append(("coach", answer))

            # Rename chat based on first message if still generic
            if not current_session.get("title") or current_session["title"].startswith(
                "Chat "
            ):
                
                snippet = text.strip().split("\n", 1)[0]
                if len(snippet) > 32:
                    snippet = snippet[:29] + "..."
                current_session["title"] = snippet

            save_state_for_current_user()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
