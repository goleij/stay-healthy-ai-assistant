# components/silence_recorder/silence_recorder.py
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import streamlit.components.v1 as components

_FRONTEND_DIR = (Path(__file__).parent / "frontend").resolve()
_silence_recorder = components.declare_component(
    "silence_recorder",
    path=str(_FRONTEND_DIR),
)

def silence_recorder(
    silence_to_end_ms: int = 900,
    min_speech_ms: int = 120,
    threshold_db: int = -45,
    auto_start: bool = False,
    max_record_ms: Optional[int] = None,
    restart_nonce: int = 0,
    keep_listening_ui: bool = True,
    mic_paused: bool = False,
    resume_after_ms: int = 0,
    key: Optional[str] = None,
):
    args = dict(
        silenceToEndMs=int(silence_to_end_ms),
        minSpeechMs=int(min_speech_ms),
        thresholdDb=float(threshold_db),
        autoStart=bool(auto_start),
        restartNonce=int(restart_nonce),
        keepListeningUi=bool(keep_listening_ui),
        micPaused=bool(mic_paused),
        maxRecordMs=int(max_record_ms or 0),          
        resumeAfterMs=int(resume_after_ms or 0),     
    )

    return _silence_recorder(**args, default=None, key=key)


def decode_component_audio(result: Optional[Dict[str, Any]]) -> Tuple[bytes, str]:
    if not result:
        return b"", ""
    audio_b64 = result.get("audio_b64")
    if not audio_b64:
        return b"", ""
    mime = str(result.get("mime") or "")
    b64 = audio_b64.split(",", 1)[-1]
    return base64.b64decode(b64), mime
