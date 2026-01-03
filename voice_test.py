import io
import math
import queue
import threading
import wave
from dataclasses import dataclass

import numpy as np
import streamlit as st
import webrtcvad
from av.audio.resampler import AudioResampler
from streamlit_webrtc import (
    webrtc_streamer,
    WebRtcMode,
    RTCConfiguration,
    AudioProcessorBase,
)

# Global queues/stats (thread-safe)
UTTER_Q: "queue.Queue[bytes]" = queue.Queue(maxsize=10)
STATS_LOCK = threading.Lock()

@dataclass
class Stats:
    last_dbfs: float = -120.0
    in_speech: bool = False
    speech_ms: int = 0
    silence_ms: int = 0

STATS = Stats()


def pcm16_to_wav_bytes(pcm16: bytes, sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16)
    return buf.getvalue()


def rms_dbfs(pcm16: bytes) -> float:
    a = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
    if a.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(a * a)) + 1e-9)
    return 20.0 * math.log10(rms / 32768.0 + 1e-12)


class VADAudioProcessor(AudioProcessorBase):
    def __init__(self, vad_mode: int, silence_ms_end: int, start_ms_min: int, energy_gate_dbfs: float):
        self.vad = webrtcvad.Vad(int(vad_mode))
        self.silence_ms_end = int(silence_ms_end)
        self.start_ms_min = int(start_ms_min)
        self.energy_gate_dbfs = float(energy_gate_dbfs)

        self.resampler = AudioResampler(format="s16", layout="mono", rate=16000)
        self.frame_ms = 20
        self.bytes_per_frame = int(16000 * (self.frame_ms / 1000.0) * 2)

        self.buf = bytearray()
        self.in_speech = False
        self.speech_ms = 0
        self.silence_ms = 0

    def _push_chunk(self, chunk: bytes):
        db = rms_dbfs(chunk)
        vad_speech = self.vad.is_speech(chunk, 16000)
        energy_ok = db >= self.energy_gate_dbfs
        is_voice = bool(vad_speech and energy_ok)

        with STATS_LOCK:
            STATS.last_dbfs = db
            STATS.in_speech = self.in_speech
            STATS.speech_ms = self.speech_ms
            STATS.silence_ms = self.silence_ms

        if is_voice:
            if not self.in_speech:
                self.in_speech = True
                self.speech_ms = 0
                self.silence_ms = 0

            self.buf.extend(chunk)
            self.speech_ms += self.frame_ms
            self.silence_ms = 0
            return

        # silence
        if self.in_speech:
            self.buf.extend(chunk)
            self.silence_ms += self.frame_ms

            if self.speech_ms >= self.start_ms_min and self.silence_ms >= self.silence_ms_end:
                utter = bytes(self.buf)
                self.buf.clear()
                self.in_speech = False
                self.speech_ms = 0
                self.silence_ms = 0

                wav_bytes = pcm16_to_wav_bytes(utter, 16000)
                try:
                    UTTER_Q.put_nowait(wav_bytes)
                except queue.Full:
                    pass

    def recv_audio(self, frame):
        af = self.resampler.resample(frame)
        pcm = af.to_ndarray()
        if pcm.ndim > 1:
            pcm = pcm.reshape(-1)
        pcm_bytes = pcm.tobytes()

        step = self.bytes_per_frame
        for i in range(0, len(pcm_bytes), step):
            chunk = pcm_bytes[i : i + step]
            if len(chunk) == step:
                self._push_chunk(chunk)

        return frame  # unchanged


st.set_page_config(page_title="End-of-Speech Test", layout="wide")
st.title("End-of-Speech (Silence) Test")
st.caption("Speak, then pause. The app should detect end-of-speech and output an utterance.")

col_cfg, col_live = st.columns([1.1, 2.2], gap="large")

with col_cfg:
    st.subheader("Settings")
    vad_mode = st.slider("VAD aggressiveness (0..3)", 0, 3, 2)
    silence_ms_end = st.slider("Silence to end (ms)", 300, 2000, 900, step=50)
    start_ms_min = st.slider("Minimum speech before allowing end (ms)", 60, 600, 120, step=20)
    energy_gate = st.slider("Energy gate (dBFS)", -70, -20, -45, step=1)

    st.divider()
    show_debug = st.toggle("Show debug metrics", value=True)

with col_live:
    st.subheader("Live")

    rtc_config = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

    webrtc_streamer(
        key="eos_webrtc",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=rtc_config,
        media_stream_constraints={"audio": True, "video": False},
        audio_processor_factory=lambda: VADAudioProcessor(
            vad_mode=vad_mode,
            silence_ms_end=silence_ms_end,
            start_ms_min=start_ms_min,
            energy_gate_dbfs=energy_gate,
        ),
    )

    status = st.empty()
    dbg = st.empty()

    # Auto refresh to pull queue results
    st.experimental_set_query_params(_refresh="1")
    st_autorefresh = st.experimental_rerun  # fallback placeholder (keeps file compatible)
    # We will simply rely on normal Streamlit reruns via widget; if you want periodic refresh,
    # you can install streamlit-autorefresh and use it here.

    if show_debug:
        with STATS_LOCK:
            dbg.write(
                f"last_dbfs={STATS.last_dbfs:.1f} | in_speech={STATS.in_speech} | "
                f"speech_ms={STATS.speech_ms} | silence_ms={STATS.silence_ms}"
            )

    try:
        wav_bytes = UTTER_Q.get_nowait()
        status.success("End-of-speech detected.")
        st.audio(wav_bytes)
    except queue.Empty:
        status.info("Click Start in the WebRTC widget, speak, then pause.")
