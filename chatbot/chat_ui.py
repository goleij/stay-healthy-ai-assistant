# chat_ui.py
import os
import time
import hashlib
import io
import wave
import requests
import re

import streamlit as st
from typing import Iterator, Tuple, Optional

# --- Imports ---
try:
    from ollama._types import ResponseError  # type: ignore
except Exception:
    class ResponseError(Exception):
        pass

# profile state saver
try:
    from storage.profile_manager import save_state_for_current_user  # type: ignore
except Exception:
    def save_state_for_current_user() -> None:
        return

# llm helpers
try:
    from llm_utils import get_llm, get_qa, list_local_models  # type: ignore
except Exception:
    def list_local_models() -> list[str]:
        models = os.getenv("LOCAL_MODELS_LIST")
        if models:
            return [m.strip() for m in models.split(",") if m.strip()]
        return ["local-default-model"]

    class _DummyLLM:
        def __init__(self, name: str):
            self.name = name

        def stream(self, prompt: str) -> Iterator[str]:
            yield f"(dummy reply for model {self.name})"

    def get_llm(name: str):
        return _DummyLLM(name)

    def get_qa(name: str):
        def qa_call(payload: dict):
            return {"result": f"(dummy QA result for {name})"}
        return qa_call


# ---------------------------
# Voice imports 
# ---------------------------
try:
    from components.silence_recorder.silence_recorder import (  # type: ignore
        silence_recorder,
        decode_component_audio,
    )
except Exception as e:
    st.error(f"❌ Voice component import failed: {e}")
    raise

try:
    from stt_whisper import transcribe_webm_bytes  # type: ignore
except Exception as e:
    st.error(f"❌ STT import failed: {e}")
    raise

# local CSS injector
try:
    from .chat_css import inject_chat_css  # type: ignore
except Exception:
    def inject_chat_css():
        return


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


def tts_speak(text: str) -> Tuple[bytes, str, float]:
    speak_url = os.getenv("CHAT_TTS_URL", "http://tts_server:5005/speak")
    t0 = time.time()
    # ✅ same as chatbot.py: timeout=180
    r = requests.post(speak_url, json={"text": text}, timeout=180)
    dt = time.time() - t0
    r.raise_for_status()
    content_type = (r.headers.get("content-type") or "").strip()
    return r.content, content_type, dt


def collect_stream_to_text(token_iter: Iterator[str]) -> str:
    out = ""
    for token in token_iter:
        if token is None:
            continue
        out += str(token)
    return out.strip()




def _sanitize_chat_title(t: str, max_words: int = 3) -> str:
    t = (t or "").strip()
    t = re.sub(r"[^\w\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""
    words = t.split()
    words = words[:max_words]
    return " ".join(w.replace("-", " ").title().replace(" ", "-") for w in words)

def generate_chat_title_llm(model_name: str, user_text: str) -> str:
    llm = get_llm(model_name)
    prompt = (
        "Return a short chat title in English, 2-3 words.\n"
        "No quotes, no punctuation, no emojis.\n"
        "Use Title Case.\n"
        f"User message: {user_text}\n"
        "Title:"
    )
    raw = collect_stream_to_text(llm.stream(prompt))
    return _sanitize_chat_title(raw, max_words=3)




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
        rules.append("Treat the user as having diabetes for all meal and recipe suggestions: avoid added sugar.")
    if allergies:
        rules.append(f"The user is allergic or intolerant to: {allergies}. Never include these ingredients.")
    if not rules:
        return ""
    return "Health and safety context:\n" + "\n".join(f"- {r}" for r in rules) + "\n"


def _get_last_coach_message() -> Optional[str]:
    history = st.session_state.get("chat_history", [])
    for speaker, msg in reversed(history):
        if speaker == "coach":
            return msg
    return None


def _get_last_user_message() -> Optional[str]:
    history = st.session_state.get("chat_history", [])
    for speaker, msg in reversed(history):
        if speaker == "user":
            return msg
    return None


# ---------------------------
# Recipe tools helpers 
# ---------------------------
def _should_show_recipe_tools(last_user: Optional[str], last_coach: Optional[str]) -> bool:
    if not last_user:
        return False

    user = (last_user or "").lower()

    user_keywords = [
        "recipe", "recipie", "recepie",
        "meal", "breakfast", "lunch", "dinner", "snack", "dessert",
        "ingredients", "shopping list", "meal plan",
        "cook", "bake", "cookies", "cookie", "biscuit"
    ]

    return any(kw in user for kw in user_keywords)



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



def strip_amounts_from_shopping_list(md: str) -> str:
    if not md:
        return md

    lines = md.splitlines()
    out = []
    for line in lines:
        s = line.strip()

        if not s:
            out.append(line)
            continue

        if s.startswith("#") or s.endswith(":"):
            out.append(line)
            continue

        if s.startswith(("-", "*", "•")):
            item = s.lstrip("-*•").strip()

            item = re.sub(r"\([^)]*\)", "", item)

            item = re.sub(r"\b\d+([./]\d+)?\b", "", item)

            units = [
                "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon", "teaspoons",
                "g", "gram", "grams", "kg", "ml", "l", "oz", "lb", "pound", "pounds",
                "slice", "slices", "clove", "cloves", "piece", "pieces"
            ]
            item = re.sub(r"\b(" + "|".join(units) + r")\b", "", item, flags=re.IGNORECASE)

            item = re.sub(r"\s{2,}", " ", item).strip(" -–—:")

            if item:
                out.append(f"- {item}")
            else:
                out.append("-")

        else:
            out.append(line)

    return "\n".join(out).strip()




# ---------- main UI ----------
def render_chat_tab(passed_model_name: Optional[str] = None):
    inject_chat_css()

    st.markdown('<div class="chat-main-header"></div>', unsafe_allow_html=True)

    _ensure_chat_sessions()
    sessions = st.session_state["chat_sessions"]
    current_id, current_session = _get_current_session()
    st.session_state.setdefault("input_nonce_by_chat", {})
    st.session_state.input_nonce_by_chat.setdefault(current_id, 0)


    # per-chat voice state initialization
    st.session_state.setdefault("voice_mode", False)
    st.session_state.setdefault("restart_nonce_by_chat", {})
    st.session_state.restart_nonce_by_chat.setdefault(current_id, 0)
    st.session_state.setdefault("last_audio_hash_by_chat", {})
    st.session_state.last_audio_hash_by_chat.setdefault(current_id, "")
    st.session_state.setdefault("coach_audio_by_chat", {})
    st.session_state.coach_audio_by_chat.setdefault(current_id, {})
    st.session_state.setdefault("mic_paused_by_chat", {})
    st.session_state.mic_paused_by_chat.setdefault(current_id, False)
    st.session_state.setdefault("resume_after_ms_by_chat", {})
    st.session_state.resume_after_ms_by_chat.setdefault(current_id, 0)

    coach_audio_map = st.session_state.coach_audio_by_chat[current_id]

    col_left, col_right = st.columns([1.1, 3])

    # left column: chat list
    with col_left:
        st.markdown("### Ask me about your plan, workouts, or recipes!")
        st.markdown("### Your chats")
        st.caption("Switch between conversations or start a new one.")
        if st.button("New chat", key="chat_new"):
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
            st.session_state.input_nonce_by_chat.setdefault(new_id, 0)
            st.session_state.input_nonce_by_chat[new_id] += 1

            save_state_for_current_user()
            st.rerun()

        for chat_id, data in sessions.items():
            title = data.get("title") or chat_id
            if len(title) > 32:
                title = title[:29] + "..."
            is_selected = chat_id == current_id
            prefix = "▶  " if is_selected else " "
            if st.button(f"{prefix}{title}", key=f"select_{chat_id}"):
                st.session_state["current_chat_id"] = chat_id
                st.session_state.chat_history = sessions[chat_id]["history"]
                save_state_for_current_user()
                st.rerun()

    # right column: chat UI
    with col_right:
        # model selection
        try:
            available_models = list_local_models()
        except Exception as e:
            st.error(f"Error listing models: {e}")
            available_models = []

        if not available_models:
            st.error("No local models found. Make sure your model list is configured.")
            return

        default_model = passed_model_name or st.session_state.get("model_name") or available_models[0]
        if default_model not in available_models:
            default_model = available_models[0]

        model_name = st.selectbox(
            "Choose a model:",
            available_models,
            index=available_models.index(default_model),
            key="model_select_chat",
        )
        st.session_state["model_name"] = model_name

        st.write("")
        st.session_state.voice_mode = st.toggle(
            "Voice mode",
            value=bool(st.session_state.voice_mode),
            key=f"voice_mode_{current_id}",
        )

        tts_max_chars = 220
        if st.button("Clear this chat", key=f"chat_clear_{current_id}"):
            st.session_state.chat_history.clear()
            st.session_state.coach_audio_by_chat[current_id] = {}
            st.session_state.last_audio_hash_by_chat[current_id] = ""
            st.session_state.mic_paused_by_chat[current_id] = False
            st.session_state.resume_after_ms_by_chat[current_id] = 0
            st.session_state.restart_nonce_by_chat[current_id] += 1
            st.session_state.input_nonce_by_chat[current_id] += 1

            save_state_for_current_user()
            st.rerun()

        # render history
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

        # ---------------------------
        # Recipe tools 
        # ---------------------------
        last_coach = _get_last_coach_message()
        last_user = _get_last_user_message()

        if last_coach and _should_show_recipe_tools(last_user, last_coach):
            tools_col1, tools_col2 = st.columns(2)

            with tools_col1:
                if st.button(" Save as recipe", key=f"save_recipe_{current_id}"):
                    recipes = st.session_state.get("saved_recipes", [])
                    recipes.append(last_coach)
                    st.session_state["saved_recipes"] = recipes
                    save_state_for_current_user()
                    st.success("Saved to your recipes in the profile page.")

            with tools_col2:
                if st.button(" Create shopping list", key=f"shop_list_{current_id}"):
                    try:
                        llm = get_llm(model_name)
                        prompt = (
                            "Answer in English.\n\n"
                            "You are a nutrition assistant. Based on the following recipe or meal plan, "
                            "extract a clean shopping list.\n\n"

                            "RULES (VERY IMPORTANT):\n"
                            "- ONLY list ingredient NAMES.\n"
                            "- DO NOT include quantities, measurements, units, or numbers of any kind.\n"
                            "- DO NOT include cups, grams, tablespoons, teaspoons, ml, or counts.\n"
                            "- Remove any amounts even if they appear in the recipe.\n"
                            "- Group ingredients by category if reasonable "
                            "(Vegetables, Fruits, Proteins, Dairy, Grains, Other).\n"
                            "- Use bullet points only.\n\n"

                            f"TEXT:\n{last_coach}\n\n"
                            "Output ONLY the shopping list in markdown."
                        )

                        with st.spinner("🛒 Generating shopping list..."):
                            shopping_text_raw = collect_stream_to_text(llm.stream(prompt))

                        shopping_text = strip_amounts_from_shopping_list(shopping_text_raw)



                        recipe_title = _extract_recipe_title(last_coach)
                        st.session_state["last_recipe_shopping_title"] = recipe_title
                        st.session_state["last_shopping_list"] = shopping_text
                        save_state_for_current_user()

                        st.success("Shopping list saved.")
                        st.markdown(shopping_text)

                    except ResponseError:
                        st.error(f"❌ Model '{model_name}' not found. Run: `ollama pull {model_name}`.")
                    except Exception as e:
                        st.error(f"Unexpected error while creating shopping list: {e}")

        #AFTER recipe tools comes use_rag
        use_rag = st.toggle(
            "Use knowledge base (RAG)",
            value=False,
            help="Turn on to answer using your prepared data.",
            key=f"use_rag_{current_id}",
        )


        # ---------------------------
        #  Voice recorder 
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

        # resume
        if st.session_state.voice_mode and voice_result and voice_result.get("event") == "resume":
            st.session_state.mic_paused_by_chat[current_id] = False
            st.session_state.resume_after_ms_by_chat[current_id] = 0
            st.session_state.restart_nonce_by_chat[current_id] += 1
            save_state_for_current_user()
            st.rerun()

        # segment
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

            st.session_state.chat_history.append(("user", user_text))
            st.session_state.chat_history.append(("coach", "Answering your question..."))
            assistant_idx = len(st.session_state.chat_history) - 1

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
                meta = f"{content_type2} (took {dt2:.1f}s) | tts_chars={len(tts_text)}"
                coach_audio_map[assistant_idx] = (audio_bytes2, fmt2, meta)
                st.session_state.mic_paused_by_chat[current_id] = False
                st.session_state.resume_after_ms_by_chat[current_id] = 0
            else:
                coach_audio_map[assistant_idx] = (b"", "audio/wav", "TTS error (no audio).")
                st.session_state.mic_paused_by_chat[current_id] = False
                st.session_state.resume_after_ms_by_chat[current_id] = 0
                st.session_state.restart_nonce_by_chat[current_id] += 1

            if not current_session.get("title") or current_session["title"].startswith("Chat "):
                try:
                    title = generate_chat_title_llm(model_name, user_text)
                except Exception:
                    title = ""
                current_session["title"] = title or _sanitize_chat_title(user_text, max_words=3) or "New Chat"





            save_state_for_current_user()
            st.rerun()

        # ---------------------------
        # Text mode
        # ---------------------------
        if not st.session_state.voice_mode:
            input_key = f"chat_input_{current_id}_{st.session_state.input_nonce_by_chat[current_id]}"
            user_input = st.text_input("Type your question here", key=input_key)

            if st.button("Send", key=f"chat_send_{current_id}"):
                text = (user_input or "").strip()
                if not text:
                    st.stop()

                st.session_state.input_nonce_by_chat[current_id] += 1

                profile = st.session_state.get("profile", {})
                language_instruction = "Answer in English."
                lower_input = text.lower()

                recipe_keywords = [
                    "recipe", "meal", "breakfast", "lunch", "dinner", "snack", "dessert",
                    "cookies", "cookie", "biscuit",
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
                    "When the user asks for meals or recipes, adapt them ONLY to the user's explicitly stated "
                    "health conditions and allergies. "
                    "Do NOT introduce additional dietary restrictions unless explicitly requested "
                    "(e.g. gluten-free, dairy-free, keto). "
                    "IMPORTANT DIABETES RULES: "
                    "If the user has diabetes, NEVER include added sugar, honey, syrup, or regular sugar, "
                    "even as optional ingredients. "
                    "For diabetes, NEVER use all-purpose flour or white flour. "
                    "Use low-glycemic alternatives such as almond flour, coconut flour, or oat fiber. "
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
                        "STRICT RULE: If diabetes is present, the recipe name MUST include "
                        "'Sugar-Free' or 'Low-Glycemic'. "
                        "Do NOT include optional sugar or refined flour in any form.\n"

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
                            answer = collect_stream_to_text(llm.stream(full_prompt))
                except ResponseError:
                    st.error(f"❌ Model '{model_name}' not found. Run: `ollama pull {model_name}`.")
                    st.stop()
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    st.stop()

                st.session_state.chat_history.append(("user", text))
                st.session_state.chat_history.append(("coach", answer))

                if not current_session.get("title") or current_session["title"].startswith("Chat "):
                    try:
                        title = generate_chat_title_llm(model_name, text)
                    except Exception:
                        title = ""
                    current_session["title"] = title or _sanitize_chat_title(text, max_words=3) or "New Chat"

                save_state_for_current_user()
                st.rerun()
