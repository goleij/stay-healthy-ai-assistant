# components/silence_component_test.py
import os
import time
import requests
import streamlit as st
import hashlib
import wave
import io
from ollama._types import ResponseError

from components.silence_recorder.silence_recorder import (
    silence_recorder,
    decode_component_audio,
)

from stt_whisper import transcribe_webm_bytes
from llm_utils import get_llm


# ---------------------------
# Helpers
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
            if rate <= 0:
                return 0.0
            return frames / float(rate)
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


def build_context(messages, max_turns: int = 4) -> str:
    recent = messages[-max_turns * 2 :]
    lines = []
    for m in recent:
        role = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def collect_stream_to_text(token_iter) -> str:
    out = ""
    for token in token_iter:
        if token is None:
            continue
        out += str(token)
    return out.strip()


# ---------------------------
# Page
# ---------------------------
st.set_page_config(page_title="Voice Mode Test (Timed)", layout="wide")
st.title("🎙️ Voice Mode Test (Timed Recording → STT → LLM → TTS)")

with st.sidebar:
    st.subheader("Settings")
    model_name = st.text_input("Ollama model", value="gemma2:2b")
    max_record_s = st.slider("Max record time (seconds)", 2, 30, 10, 1)
    tts_max_chars = st.slider("TTS max chars (speed)", 80, 500, 220, 10)
    auto_start = st.toggle("Auto start (may fail in browser)", value=False)

max_record_ms = int(max_record_s * 1000)

st.caption(
    f"Mode: **timed** (records up to {max_record_s}s, then sends one segment). "
    f"Answer is kept short, and TTS is limited to {tts_max_chars} chars. "
    f"**Audio-first UI**: audio appears before text."
)

# ---------------------------
# Session state
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "tts_by_msg" not in st.session_state:
    st.session_state.tts_by_msg = {}

if "restart_nonce" not in st.session_state:
    st.session_state.restart_nonce = 0

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = ""

if "mic_paused" not in st.session_state:
    st.session_state.mic_paused = False

if "resume_after_ms" not in st.session_state:
    st.session_state.resume_after_ms = 0


# ---------------------------
# Recorder
# ---------------------------
st.subheader("Recorder")

result = silence_recorder(
    silence_to_end_ms=900,
    min_speech_ms=120,
    threshold_db=-45,
    auto_start=auto_start,
    max_record_ms=max_record_ms,
    restart_nonce=st.session_state.restart_nonce,
    keep_listening_ui=True,

    mic_paused=st.session_state.mic_paused,
    resume_after_ms=st.session_state.resume_after_ms,

    key="silence_recorder",
)

st.divider()


# ---------------------------
# Chat UI (AUDIO FIRST)
# ---------------------------
st.subheader("Chat")

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        if m["role"] == "assistant":
            tts_item = st.session_state.tts_by_msg.get(i)
            if tts_item:
                audio_bytes, fmt, meta = tts_item
                st.audio(audio_bytes, format=fmt, autoplay=True)
                if meta:
                    st.caption(meta)

            if (m.get("content") or "").strip():
                st.write(m["content"])
        else:
            st.write(m["content"])


# ---------------------------
# Handle RESUME event from JS
# ---------------------------
if result and result.get("event") == "resume":
    # JS says: "TTS playback time passed, resume mic + next recording"
    st.session_state.mic_paused = False
    st.session_state.resume_after_ms = 0
    st.session_state.restart_nonce += 1
    st.rerun()


# ---------------------------
# Main pipeline: SEGMENT
# ---------------------------
if result and result.get("event") == "segment":
    audio_bytes, _ = decode_component_audio(result)

    audio_hash = hashlib.sha1(audio_bytes).hexdigest() if audio_bytes else ""
    if (not audio_hash) or (audio_hash == st.session_state.last_audio_hash):
        st.stop()
    st.session_state.last_audio_hash = audio_hash

    # ---- STT ----
    try:
        user_text = transcribe_webm_bytes(audio_bytes)
    except Exception as e:
        st.error(f"STT error: {e}")
        st.session_state.restart_nonce += 1
        st.rerun()

    user_text = (user_text or "").strip()
    if len(user_text) < 2:
        st.session_state.restart_nonce += 1
        st.rerun()

    st.session_state.messages.append({"role": "user", "content": user_text})

    # assistant placeholder in chat history
    st.session_state.messages.append({"role": "assistant", "content": "Answering your question..."})
    assistant_index = len(st.session_state.messages) - 1

    # ---- LLM ----
    context = build_context(st.session_state.messages)
    prompt = f"""
You are a voice assistant.
Rules:
- Answer in English.
- Keep it VERY short: maximum 2 sentences.
- No lists. No long recipes. No extra details.
- If user asks for many things, answer only the most important part.

Conversation:
{context}
Assistant:
""".strip()

    try:
        llm = get_llm(model_name)
        reply = collect_stream_to_text(llm.stream(prompt))
    except ResponseError:
        st.session_state.messages[assistant_index]["content"] = ""
        st.error(f"Model '{model_name}' not found. Run: ollama pull {model_name}")
        st.session_state.restart_nonce += 1
        st.rerun()
    except Exception as e:
        st.session_state.messages[assistant_index]["content"] = ""
        st.error(f"LLM error: {e}")
        st.session_state.restart_nonce += 1
        st.rerun()

    reply = (reply or "").strip()
    if not reply:
        st.session_state.messages[assistant_index]["content"] = ""
        st.session_state.restart_nonce += 1
        st.rerun()

    reply_for_display = shorten_for_tts(reply, max_chars=max(120, int(tts_max_chars)))
    tts_text = shorten_for_tts(reply_for_display, max_chars=int(tts_max_chars))

    # ---- TTS ----
    try:
        audio_bytes2, content_type2, dt2 = tts_speak(tts_text)
    except Exception:
        audio_bytes2 = b""
        content_type2 = ""
        dt2 = 0.0

    # update assistant text after audio is ready
    st.session_state.messages[assistant_index]["content"] = reply_for_display

    if audio_bytes2:
        fmt2 = sniff_audio_format(audio_bytes2)
        dur = wav_duration_seconds(audio_bytes2)
        meta = f"{content_type2} (took {dt2:.1f}s) | tts_chars={len(tts_text)}"
        st.session_state.tts_by_msg[assistant_index] = (audio_bytes2, fmt2, meta)

        # ✅ MUTE mic and tell JS when to resume
        st.session_state.mic_paused = True
        st.session_state.resume_after_ms = int((max(0.0, dur) + 0.35) * 1000)

        # IMPORTANT: do NOT restart now. JS will send "resume"
        st.rerun()
    else:
        st.session_state.tts_by_msg[assistant_index] = (b"", "audio/wav", "TTS error (no audio).")
        st.session_state.restart_nonce += 1
        st.rerun()
