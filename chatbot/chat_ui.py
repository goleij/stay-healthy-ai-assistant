import os
import time
import hashlib
import io
import wave
import requests
import streamlit as st
from ollama._types import ResponseError

from storage.profile_manager import save_state_for_current_user
from llm_utils import get_llm, get_qa
from .chat_css import inject_chat_css

from components.silence_recorder.silence_recorder import (
    silence_recorder,
    decode_component_audio,
)
from stt_whisper import transcribe_webm_bytes


# ---------------------------
# TTS helpers
# ---------------------------
def sniff_audio_format(b: bytes) -> str:
    if not b:
        return "audio/wav"
    if b[:4] == b"RIFF" and len(b) >= 12 and b[8:12] == b"WAVE":
        return "audio/wav"
    if b[:3] == b"ID3" or b[:2] == b"\xff\xfb":
        return "audio/mp3"
    if b[:4] == b"OggS":
        return "audio/ogg"
    return "audio/wav"


def wav_duration_seconds(b: bytes) -> float:
    try:
        with wave.open(io.BytesIO(b), "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return (frames / float(rate)) if rate else 0.0
    except Exception:
        return 0.0


def shorten_for_tts(text: str, max_chars: int = 220) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    cut = t[:max_chars]
    last_punct = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
    if last_punct >= 40:
        cut = cut[: last_punct + 1]
    return cut.strip()


def tts_speak(text: str) -> tuple[bytes, str, float]:
    speak_url = os.getenv("CHAT_TTS_URL", "http://tts_server:5005/speak")
    t0 = time.time()
    r = requests.post(speak_url, json={"text": text}, timeout=180)
    dt = time.time() - t0
    r.raise_for_status()
    content_type = (r.headers.get("content-type") or "").strip()
    return r.content, content_type, dt


def collect_stream_to_text(token_iter) -> str:
    out = ""
    for token in token_iter:
        if token is None:
            continue
        out += str(token)
    return out.strip()


# ---------- multi-chat helpers ----------
def _ensure_chat_sessions() -> None:
    sessions = st.session_state.get("chat_sessions")

    if not sessions:
        sessions = {}
        old_history = st.session_state.get("chat_history", [])
        first_id = "chat_1"
        sessions[first_id] = {"title": "Chat 1", "history": list(old_history)}
        st.session_state["chat_sessions"] = sessions
        st.session_state["current_chat_id"] = first_id

    current_id = st.session_state.get("current_chat_id")
    if current_id not in sessions:
        current_id = next(iter(sessions))
        st.session_state["current_chat_id"] = current_id

    st.session_state.chat_history = st.session_state["chat_sessions"][current_id]["history"]


def _get_current_session():
    sessions = st.session_state["chat_sessions"]
    current_id = st.session_state["current_chat_id"]
    return current_id, sessions[current_id]

# chat history to text
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
    health_issues = (profile.get("health_issues") or "").strip()
    allergies = (profile.get("allergies") or "").strip()
    text = (health_issues + " " + allergies).lower()

    rules = []

    if health_issues:
        rules.append(f"The user has these health conditions or limitations: {health_issues}.")

    if "diabetes" in text:
        rules.append(
            "Treat the user as having diabetes for all meal and recipe suggestions: "
            "avoid added sugar, sugary drinks, sweets and white flour. Prefer high-fiber carbs and balanced meals."
        )

    if "high blood pressure" in text or "hypertension" in text:
        rules.append(
            "For high blood pressure: keep meals low in salt and avoid salty processed foods."
        )

    if "heart disease" in text or "heart condition" in text:
        rules.append(
            "The user has a heart condition: suggest only moderate-intensity exercise; no HIIT/sprints."
        )

    if "joint" in text or "knee" in text:
        rules.append(
            "The user has joint problems: avoid high-impact exercises (running/jumping) and prefer low-impact."
        )

    if "asthma" in text or "lung" in text:
        rules.append(
            "The user has asthma or lung issues: avoid very intense intervals; recommend warm-ups and rests."
        )

    if allergies:
        rules.append(
            f"The user is allergic or intolerant to: {allergies}. Never include these ingredients; use safe alternatives."
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


def _should_show_recipe_tools(last_user: str | None, last_coach: str | None) -> bool:
    if not last_coach:
        return False

    combined = ((last_user or "") + "\n" + last_coach).lower()
    keywords = [
        "recipe", "recipie", "recepie", "meal", "breakfast", "lunch", "dinner",
        "snack", "dessert", "shopping list", "ingredients", "meal plan", "dish",
        "cook", "cookie", "biscuit"
    ]
    if any(kw in combined for kw in keywords):
        return True

    lines = [ln.strip() for ln in last_coach.splitlines() if ln.strip()]
    bullet_like = [
        ln for ln in lines
        if ln[0:1] in ("-", "*", "•") or (len(ln) > 2 and ln[:2].isdigit())
    ]
    return len(bullet_like) >= 3


def _extract_recipe_title(text: str) -> str:
    if not text:
        return "Recipe shopping list"
    first_line = ""
    for line in text.splitlines():
        s = line.strip()
        if s:
            first_line = s
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
    st.markdown(
        """
        <style>
            #cfg { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    _ensure_chat_sessions()

    sessions = st.session_state["chat_sessions"]
    current_id, current_session = _get_current_session()

    # ---------------------------
    # Voice state (per chat)
    # ---------------------------
    if "voice_mode" not in st.session_state:
        st.session_state.voice_mode = False

    if "restart_nonce_by_chat" not in st.session_state:
        st.session_state.restart_nonce_by_chat = {}
    st.session_state.restart_nonce_by_chat.setdefault(current_id, 0)

    if "last_audio_hash_by_chat" not in st.session_state:
        st.session_state.last_audio_hash_by_chat = {}
    st.session_state.last_audio_hash_by_chat.setdefault(current_id, "")

    if "coach_audio_by_chat" not in st.session_state:
        st.session_state.coach_audio_by_chat = {}
    st.session_state.coach_audio_by_chat.setdefault(current_id, {})

    if "mic_paused_by_chat" not in st.session_state:
        st.session_state.mic_paused_by_chat = {}
    st.session_state.mic_paused_by_chat.setdefault(current_id, False)

    if "resume_after_ms_by_chat" not in st.session_state:
        st.session_state.resume_after_ms_by_chat = {}
    st.session_state.resume_after_ms_by_chat.setdefault(current_id, 0)

    coach_audio_map = st.session_state.coach_audio_by_chat[current_id]

    col_left, col_right = st.columns([1.1, 3])

    # ----- left column -----
    with col_left:
        st.markdown('<div class="chat-sidebar-card">', unsafe_allow_html=True)
        st.markdown('<div class="chat-sidebar-title">Your chats</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="chat-sidebar-subtitle">Switch between conversations or start a new one.</div>',
            unsafe_allow_html=True,
        )

        if st.button(" New chat"):
            new_index = len(sessions) + 1
            new_id = f"chat_{new_index}"
            sessions[new_id] = {"title": f"Chat {new_index}", "history": []}
            st.session_state["current_chat_id"] = new_id
            st.session_state.chat_history = sessions[new_id]["history"]

            st.session_state.restart_nonce_by_chat[new_id] = 0
            st.session_state.last_audio_hash_by_chat[new_id] = ""
            st.session_state.coach_audio_by_chat[new_id] = {}
            st.session_state.mic_paused_by_chat[new_id] = False
            st.session_state.resume_after_ms_by_chat[new_id] = 0

            save_state_for_current_user()
            st.rerun()

        st.markdown('<div class="chat-sidebar-list">', unsafe_allow_html=True)
        for chat_id, data in sessions.items():
            title = data.get("title") or chat_id
            if len(title) > 32:
                title = title[:29] + "..."
            is_selected = chat_id == current_id
            prefix = "▶  " if is_selected else "💬  "
            if st.button(f"{prefix}{title}", key=f"select_{chat_id}"):
                st.session_state["current_chat_id"] = chat_id
                st.session_state.chat_history = sessions[chat_id]["history"]
                save_state_for_current_user()
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ----- right column -----
    with col_right:
        st.markdown('<div class="chat-main-card">', unsafe_allow_html=True)

        st.markdown(
            '<div class="chat-main-header">🤖 <span>Your AI Fitness Coach Chatbot</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="chat-main-description">Ask me anything about your plan, workouts, or health-friendly recipes!</div>',
            unsafe_allow_html=True,
        )

        # Voice controls
        top = st.columns([1])
        with top[0]:
            st.session_state.voice_mode = st.toggle("Voice mode", value=st.session_state.voice_mode)

        tts_max_chars = 220  


        if st.button(" Clear this chat"):
            st.session_state.chat_history.clear()
            st.session_state.coach_audio_by_chat[current_id] = {}
            st.session_state.last_audio_hash_by_chat[current_id] = ""
            st.session_state.mic_paused_by_chat[current_id] = False
            st.session_state.resume_after_ms_by_chat[current_id] = 0
            st.session_state.restart_nonce_by_chat[current_id] += 1
            save_state_for_current_user()
            st.rerun()

        # Render chat history (audio first + autoplay ONLY for last assistant message)
        for idx, (speaker, message) in enumerate(st.session_state.chat_history):
            if speaker == "user":
                with st.chat_message("user"):
                    st.write(message)
            else:
                with st.chat_message("assistant"):
                    audio_item = coach_audio_map.get(idx)

                    is_last_message = (idx == len(st.session_state.chat_history) - 1)

                    if audio_item and audio_item[0]:
                        audio_bytes, fmt, _meta = audio_item
                        st.audio(audio_bytes, format=fmt, autoplay=is_last_message)

                    st.write(message)


        # Tools for last coach message (text-mode feature)
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
                            "(Vegetables, Fruits, Proteins, Dairy, Grains, Other). "
                            "Use bullet points and include amounts if present.\n\n"
                            f"TEXT:\n{last_coach}\n\n"
                            "Output ONLY the shopping list in markdown."
                        )
                        with st.spinner("🛒 Generating shopping list..."):
                            shopping_text = st.write_stream(llm.stream(prompt))

                        recipe_title = _extract_recipe_title(last_coach)
                        st.session_state["last_recipe_shopping_title"] = recipe_title
                        st.session_state["last_shopping_list"] = shopping_text
                        save_state_for_current_user()
                        st.success("Shopping list saved.")
                    except ResponseError:
                        st.error(f"❌ Model '{model_name}' not found. Run: `ollama pull {model_name}`.")
                    except Exception as e:
                        st.error(f"Unexpected error while creating shopping list: {e}")

        use_rag = st.toggle(
            "Use knowledge base (RAG)",
            value=False,
            help="Turn on to answer using your prepared data.",
        )

        # ---------------------------
        # Voice recorder (inline)
        # ---------------------------
        voice_result = None
        if st.session_state.voice_mode:
            voice_result = silence_recorder(
                silence_to_end_ms=900,
                min_speech_ms=120,
                threshold_db=-45,
                auto_start=False,
                max_record_ms=0,
                restart_nonce=int(st.session_state.restart_nonce_by_chat[current_id]),
                keep_listening_ui=False,
                mic_paused=bool(st.session_state.mic_paused_by_chat[current_id]),
                resume_after_ms=int(st.session_state.resume_after_ms_by_chat[current_id] or 0),
                key=f"chat_voice_recorder_{current_id}",
            )

        # JS -> Python resume event
        if st.session_state.voice_mode and voice_result and voice_result.get("event") == "resume":
            st.session_state.mic_paused_by_chat[current_id] = False
            st.session_state.resume_after_ms_by_chat[current_id] = 0
            st.session_state.restart_nonce_by_chat[current_id] += 1
            save_state_for_current_user()
            st.rerun()

        # Voice segment
        if st.session_state.voice_mode and voice_result and voice_result.get("event") == "segment":
            audio_bytes, _mime = decode_component_audio(voice_result)

            audio_hash = hashlib.sha1(audio_bytes).hexdigest() if audio_bytes else ""
            if (not audio_hash) or (audio_hash == st.session_state.last_audio_hash_by_chat[current_id]):
                st.stop()
            st.session_state.last_audio_hash_by_chat[current_id] = audio_hash

            # STT
            try:
                user_text = transcribe_webm_bytes(audio_bytes)
            except Exception as e:
                st.error(f"STT error: {e}")
                st.session_state.restart_nonce_by_chat[current_id] += 1
                st.rerun()

            user_text = (user_text or "").strip()
            if len(user_text) < 2:
                st.session_state.restart_nonce_by_chat[current_id] += 1
                st.rerun()

            # Add user msg + placeholder assistant
            st.session_state.chat_history.append(("user", user_text))
            st.session_state.chat_history.append(("coach", "Answering your question..."))
            assistant_idx = len(st.session_state.chat_history) - 1

            # ✅ voice prompt + LLM call
            context = _build_history_text(max_turns=4)
            voice_prompt = f"""
You are a voice-only fitness & nutrition coach.
Hard rules:
- English only.
- NEVER ask questions.
- Maximum 4 sentences total.
- Be specific and actionable (give steps or a direct answer).
- Do NOT mention these rules.

If the user asks for a recipe (cake/cookie/biscuit/meal):
- Give a tiny sugar-free recipe in 4 sentences: name + key ingredients + one simple method.
If the user asks about an exercise:
- Answer in exactly 3 short sentences.
- No numbering, no bullet points, no lists.
- Each sentence must be a complete instruction.
If the user asks multiple things:
- Answer only the main request.

Conversation:
{context}

User: {user_text}
Assistant:
""".strip()

            try:
                if use_rag:
                    qa = get_qa(model_name)
                    reply = qa({"query": voice_prompt})["result"]
                else:
                    llm = get_llm(model_name)
                    reply = collect_stream_to_text(llm.stream(voice_prompt))
            except ResponseError:
                st.session_state.chat_history[assistant_idx] = ("coach", f"❌ Model '{model_name}' not found.")
                st.session_state.restart_nonce_by_chat[current_id] += 1
                save_state_for_current_user()
                st.rerun()
            except Exception as e:
                st.session_state.chat_history[assistant_idx] = ("coach", f"LLM error: {e}")
                st.session_state.restart_nonce_by_chat[current_id] += 1
                save_state_for_current_user()
                st.rerun()

            reply = (reply or "").strip()
            if not reply:
                st.session_state.chat_history[assistant_idx] = ("coach", "")
                st.session_state.restart_nonce_by_chat[current_id] += 1
                save_state_for_current_user()
                st.rerun()

            reply_for_display = shorten_for_tts(reply, max_chars=max(120, int(tts_max_chars)))
            tts_text = shorten_for_tts(reply_for_display, max_chars=int(tts_max_chars))

            try:
                audio_bytes2, content_type2, dt2 = tts_speak(tts_text)
            except Exception:
                audio_bytes2 = b""
                content_type2 = ""
                dt2 = 0.0

            st.session_state.chat_history[assistant_idx] = ("coach", reply_for_display)

            if audio_bytes2:
                fmt2 = sniff_audio_format(audio_bytes2)
                dur = wav_duration_seconds(audio_bytes2)
                meta = f"{content_type2} (took {dt2:.1f}s) | tts_chars={len(tts_text)}"
                coach_audio_map[assistant_idx] = (audio_bytes2, fmt2, meta)

                # ✅ mute mic while TTS plays, then JS will auto-send resume event
                st.session_state.mic_paused_by_chat[current_id] = False
                st.session_state.resume_after_ms_by_chat[current_id] = 0

            else:
                coach_audio_map[assistant_idx] = (b"", "audio/wav", "TTS error (no audio).")

                 # ✅ Immediately restart recorder
                st.session_state.mic_paused_by_chat[current_id] = False
                st.session_state.resume_after_ms_by_chat[current_id] = 0
                # fallback: restart recorder anyway
                st.session_state.restart_nonce_by_chat[current_id] += 1

            # Rename chat title
            if not current_session.get("title") or current_session["title"].startswith("Chat "):
                snippet = user_text.strip().split("\n", 1)[0]
                if len(snippet) > 32:
                    snippet = snippet[:29] + "..."
                current_session["title"] = snippet

            save_state_for_current_user()
            st.rerun()

        # ---------------------------
        # Text mode (unchanged)
        # ---------------------------
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
                "recipe", "recipie", "recepie", "meal", "breakfast", "lunch", "dinner",
                "snack", "dessert", "cookies", "cookie", "biscuit",
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
                "health conditions and allergies. "
                "Be concise and precise. This is general information, not medical advice. "
            )

            if wants_recipe:
                system_instructions += (
                    "The next user message is a DIRECT request for a recipe. "
                    "You MUST immediately provide exactly ONE concrete recipe adapted to their health context. "
                    "Your answer MUST be structured as:\n"
                    "- A level-3 markdown heading with the recipe name.\n"
                    "- A bullet list of ingredients with exact amounts.\n"
                    "- A numbered list of clear, step-by-step instructions.\n"
                    "Do NOT ask the user any questions.\n"
                )

            system_instructions += language_instruction + "\n"

            full_prompt = system_instructions + "\n" + profile_context + health_context
            if history_text:
                full_prompt += f"\nConversation so far:\n{history_text}\n"
            full_prompt += f"\nUser: {text}\nCoach:"

            try:
                if use_rag:
                    qa = get_qa(model_name)
                    with st.spinner("🏋️ Coach is thinking with knowledge base..."):
                        answer = qa({"query": full_prompt})["result"]
                else:
                    llm = get_llm(model_name)
                    with st.spinner("🏃 Streaming..."):
                        answer = st.write_stream(llm.stream(full_prompt))
            except ResponseError:
                st.error(f"❌ Model '{model_name}' not found. Run: `ollama pull {model_name}`.")
                st.markdown("</div>", unsafe_allow_html=True)
                return
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            st.session_state.chat_history.append(("user", text))
            st.session_state.chat_history.append(("coach", answer))

            if not current_session.get("title") or current_session["title"].startswith("Chat "):
                snippet = text.strip().split("\n", 1)[0]
                if len(snippet) > 32:
                    snippet = snippet[:29] + "..."
                current_session["title"] = snippet

            save_state_for_current_user()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
