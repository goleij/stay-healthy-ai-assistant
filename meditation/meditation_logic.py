"""
meditation_logic.py
===================

Logik für die Meditationserstellung, Textgenerierung, Audio-Mix und Persistenz.

Dieses Modul bietet Funktionen zur Generierung von Meditationstexten, zur Erzeugung und Mischung von Audio (TTS + Ambient),
sowie zum Speichern und Laden von Meditationen.
"""
from __future__ import annotations

import io
import json
import math
import os
import random
import textwrap
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import requests

try:  # Optional dependency for real ambient loops
    from pydub import AudioSegment
except Exception:  # noqa: BLE001
    AudioSegment = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# FastAPI-Server für XTTS (läuft bei dir in voice_clone_server)

VOICE_CLONE_URL = os.getenv(
    "VOICE_CLONE_URL",
    "http://127.0.0.1:5005/synthesize_meditation",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "meditation_data"
AMBIENT_DIR = Path(__file__).resolve().parent / "ambient"
AMBIENT_LIBRARY = {
    "waves": AMBIENT_DIR / "ocean_waves.mp3",
    "forest": AMBIENT_DIR / "birds_in_forest.mp3",
    "rain": AMBIENT_DIR / "summer_rain.mp3",
}
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class MeditationConfig:
    """
    Konfigurationsdaten für eine Meditation.

    Attributes:
        category: Kategorie der Meditation (z.B. "Mindfulness", "Breathing", ...)
        length: Länge der Meditation ("short", "medium", "long")
        ambient_style: Ambient-Stil ("waves", "forest", "rain", "none")
        music_volume_db: Lautstärke des Hintergrunds in dB (-30 bis +5 typisch)
    """
    category: str
    length: str
    ambient_style: str
    music_volume_db: int


# ---------------------------------------------------------------------------
# TEXT GENERATION (template-basiert, lokal, kein LLM nötig)
# ---------------------------------------------------------------------------

_INTRO_TEMPLATES: Dict[str, List[str]] = {
    "Mindfulness": [
        "Take a slow deep breath in through your nose, and gently exhale through your mouth.",
        "Let your eyes soften or close, and notice the gentle rhythm of your breathing.",
        "Allow yourself to arrive fully in this moment, leaving the rest of the day outside the room.",
    ],
    "Breathing": [
        "Begin by noticing the natural flow of your breath.",
        "Place one hand on your belly and one on your chest, simply feeling each inhale and exhale.",
        "Let your breath be your anchor, a simple point of focus you can always return to.",
    ],
    "Body Scan": [
        "Find a comfortable position, either sitting or lying down.",
        "Allow your body to be supported by the surface beneath you.",
        "Take a slow breath, and as you exhale, imagine your whole body softening just a little.",
    ],
    "Sleep": [
        "Get as comfortable as you can, allowing your body to sink into the mattress.",
        "Let your eyes gently close and give yourself permission to rest.",
        "There is nothing you need to do right now, nowhere you need to be, except here.",
    ],
}

_BODY_TEMPLATES: Dict[str, List[str]] = {
    "Mindfulness": [
        "Notice the sensations of your breath at the tip of your nose, in your chest, or in your belly. There is no need to control it, simply observe.",
        "If thoughts appear, acknowledge them kindly, as if saying hello to a passing cloud, and then gently return your attention to the breath.",
        "Become aware of sounds around you, near and far. See if you can listen without judging, just receiving each sound as it comes and goes.",
        "Bring your attention to the feeling of your body sitting or lying here, the contact points, the weight, the temperature of the air on your skin.",
    ],
    "Breathing": [
        "Breathe in through your nose for a count of four, hold very softly for a count of two, and then exhale through your mouth for a count of six.",
        "If counting feels stressful, simply return to following the sensation of the breath moving in and out of your body.",
        "Imagine that each inhale brings in calm, clear energy, and each exhale releases tension, worry, and fatigue.",
        "Notice if your shoulders or jaw are holding on to any tightness, and invite them to soften on your next out-breath.",
    ],
    "Body Scan": [
        "Bring your attention down to your feet. Notice any sensations in your toes, soles, and heels. If you like, gently invite them to relax.",
        "Let your awareness travel slowly up through your legs, knees, and thighs. Notice areas of warmth, coolness, tension, or ease.",
        "Move your attention into your belly, chest, and back. Sense the rise and fall of each breath, and any subtle movements underneath.",
        "Allow your awareness to rest on your shoulders, neck, and face. Soften your forehead, unclench your jaw, and let your tongue rest gently in your mouth.",
    ],
    "Sleep": [
        "With each exhale, imagine your body becoming heavier, as if you are sinking into a soft, supportive cloud.",
        "Picture a warm, gentle light beginning at your feet and slowly travelling up your body, relaxing every muscle it touches.",
        "If thoughts appear, let them drift by like leaves floating down a quiet stream, without needing to follow any of them.",
        "Allow your breath to become slow and effortless, as if your body is breathing itself.",
    ],
}

_OUTRO_TEMPLATES: Dict[str, List[str]] = {
    "Mindfulness": [
        "Take one more slow breath in and out, and silently thank yourself for taking this time to pause.",
        "When you are ready, gently wiggle your fingers and toes, and slowly open your eyes.",
    ],
    "Breathing": [
        "Release the counting and allow your breath to return to its natural rhythm.",
        "Notice any sense of calm or clarity that is present, even if it is very subtle.",
    ],
    "Body Scan": [
        "Take a moment to sense your whole body again as one field of sensations.",
        "If you are ready to end, deepen your breath, gently move your body, and slowly open your eyes.",
    ],
    "Sleep": [
        "You can allow your attention to fade whenever it feels right, drifting into rest whenever you are ready.",
        "There is nothing to do now but to keep breathing softly and let sleep come in its own time.",
    ],
}

_LENGTH_MULTIPLIER = {
    "short": 1,
    "medium": 2,
    "long": 3,
}


def _pick_sentences(pool: List[str], count: int) -> List[str]:
    """
    Wählt eine bestimmte Anzahl Sätze aus einer Liste aus, ggf. mit Wiederholung.
    Die Reihenfolge ist zufällig.
    """
    if count <= 0:
        return []
    if len(pool) <= count:
        repeats = (count + len(pool) - 1) // len(pool)
        extended = pool * repeats
        random.shuffle(extended)
        return extended[:count]
    return random.sample(pool, count)


def generate_meditation_text(category: str, length: str) -> str:
    """
    Baut einen mehrabschnittigen Meditationstext zusammen.

    Args:
        category: Kategorie der Meditation (z.B. "Mindfulness")
        length: Länge der Meditation ("short", "medium", "long")

    Returns:
        Ein String mit Leerzeile zwischen Absätzen.
    """
    cat = category if category in _INTRO_TEMPLATES else "Mindfulness"
    length_key = length if length in _LENGTH_MULTIPLIER else "medium"
    mult = _LENGTH_MULTIPLIER[length_key]

    intro = random.choice(_INTRO_TEMPLATES[cat])

    body_count = 2 * mult  # 2/4/6 Body-Sätze
    body_sentences = _pick_sentences(_BODY_TEMPLATES[cat], body_count)

    outro_count = 1 if mult == 1 else 2
    outro_sentences = _pick_sentences(_OUTRO_TEMPLATES[cat], outro_count)

    paragraphs: List[str] = []
    paragraphs.append(intro)

    # Body in kleine Absätze gruppieren (2–3 Sätze)
    group_size = 2
    for i in range(0, len(body_sentences), group_size):
        chunk = " ".join(body_sentences[i : i + group_size])
        paragraphs.append(chunk)

    paragraphs.append(" ".join(outro_sentences))

    wrapped = [
        textwrap.fill(p, width=90, break_long_words=False) for p in paragraphs
    ]
    return "\n\n".join(wrapped)


# ---------------------------------------------------------------------------
# AUDIO: XTTS-Server + synthetische Ambient-Musik
# ---------------------------------------------------------------------------

def _call_voice_clone_server(text: str) -> bytes:
    """
    Ruft den lokalen XTTS-Server auf und gibt WAV-Bytes zurück.
    Erwartet FastAPI-Endpoint bei VOICE_CLONE_URL, der audio/wav liefert.

    Args:
        text: Der zu sprechende Text.

    Returns:
        WAV-Bytes (16-bit PCM)
    """
    resp = requests.post(
        VOICE_CLONE_URL,
        json={"text": text, "language": "en"},
        timeout=500,
    )
    resp.raise_for_status()
    return resp.content


def _generate_ambient_noise(
    style: str,
    num_samples: int,
    sample_rate: int,
) -> np.ndarray:
    """
    Erzeugt ein einfaches Ambient-Signal (float32 in [-1, 1]).
    Verschiedene Styles = verschiedene "Färbung" des Rauschens.

    Args:
        style: Ambient-Stil ("waves", "forest", "rain", ...)
        num_samples: Anzahl der Samples
        sample_rate: Abtastrate

    Returns:
        Array mit Audiodaten (float32)
    """
    noise = np.random.normal(0.0, 0.3, size=num_samples).astype(np.float32)
    t = np.linspace(0.0, num_samples / sample_rate, num_samples, endpoint=False)

    style = (style or "waves").lower()
    if style == "waves":
        # Langsame Lautstärke-Wellen
        env = 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * t)
        ambient = noise * env
    elif style == "forest":
        # Etwas mehr mittlere Frequenzen
        smooth = np.convolve(noise, np.ones(400) / 400, mode="same")
        ambient = 0.5 * noise + 0.7 * smooth
    elif style == "rain":
        # Helleres Rauschen
        smooth = np.convolve(noise, np.ones(80) / 80, mode="same")
        ambient = noise - 0.7 * smooth
    else:
        ambient = noise

    ambient = np.clip(ambient, -0.8, 0.8)
    return ambient


def _load_ambient_file(style: str, sample_rate: int) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Lädt eine Ambient-Datei aus dem ./ambient Ordner und gibt float32-Samples [-1,1] zurück.
    Fällt auf None zurück, wenn Datei fehlt oder pydub nicht installiert ist.

    Args:
        style: Ambient-Stil
        sample_rate: Ziel-Abtastrate

    Returns:
        (Samples als float32, Warnung oder None)
    """
    if AudioSegment is None:
        return None, "pydub not installed; using synthetic ambient."

    path = AMBIENT_LIBRARY.get(style)
    if not path or not path.exists():
        return None, f"No ambient file found for style '{style}'."

    audio = AudioSegment.from_file(path)
    if audio.channels > 1:
        audio = audio.set_channels(1)
    if audio.frame_rate != sample_rate:
        audio = audio.set_frame_rate(sample_rate)

    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    max_val = float(2 ** (8 * audio.sample_width - 1)) or 1.0
    samples = samples / max_val
    return samples, None


def _build_ambient_track(
    style: str,
    num_samples: int,
    sample_rate: int,
) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Versucht reale Ambient-Loops zu nutzen, fällt sonst auf synthetisches Rauschen zurück.

    Args:
        style: Ambient-Stil
        num_samples: Anzahl der Samples
        sample_rate: Abtastrate

    Returns:
        (Samples als float32, Warnung oder None)
    """
    style_key = (style or "waves").lower()

    file_audio, warning = _load_ambient_file(style_key, sample_rate)
    if file_audio is not None and file_audio.size > 0:
        if file_audio.shape[0] < num_samples:
            repeats = math.ceil(num_samples / file_audio.shape[0])
            file_audio = np.tile(file_audio, repeats)
        start = 0
        if file_audio.shape[0] > num_samples:
            start = random.randint(0, file_audio.shape[0] - num_samples)
        ambient = file_audio[start : start + num_samples]
        return ambient.astype(np.float32), warning

    ambient = _generate_ambient_noise(style_key, num_samples, sample_rate)
    return ambient, warning


def _mix_voice_and_ambient(
    voice_wav: bytes,
    ambient_style: str,
    music_volume_db: int,
) -> Tuple[bytes, Optional[str]]:
    """
    Mischt TTS-Stimme mit Ambient-Noise und gibt neue WAV-Bytes zurück.
    Nur stdlib + numpy.

    Args:
        voice_wav: WAV-Bytes der Stimme
        ambient_style: Ambient-Stil
        music_volume_db: Lautstärke des Hintergrunds in dB

    Returns:
        (Gemischte WAV-Bytes, Warnung oder None)
    """
    voice_buf = io.BytesIO(voice_wav)
    with wave.open(voice_buf, "rb") as vf:
        n_channels = vf.getnchannels()
        sampwidth = vf.getsampwidth()
        framerate = vf.getframerate()
        n_frames = vf.getnframes()
        raw_voice = vf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError("Expected 16-bit PCM WAV from voice clone server.")

    voice_samples = np.frombuffer(raw_voice, dtype="<i2").astype(np.float32)
    if n_channels > 1:
        voice_samples = voice_samples.reshape(-1, n_channels)
        mono_voice = voice_samples.mean(axis=1)
    else:
        mono_voice = voice_samples

    num_samples = mono_voice.shape[0]
    voice_float = mono_voice / 32768.0

    load_warning = None
    if ambient_style.lower() == "none":
        mixed = voice_float
    else:
        ambient, load_warning = _build_ambient_track(
            ambient_style,
            num_samples,
            framerate,
        )
        gain = 10 ** (music_volume_db / 20.0)
        ambient = ambient * gain if ambient is not None else None
        mixed = voice_float if ambient is None else voice_float + ambient

    max_amp = float(np.max(np.abs(mixed))) or 1.0
    if max_amp > 0.99:
        mixed = mixed / max_amp * 0.98

    mixed_int16 = (mixed * 32767.0).astype("<i2")

    if n_channels > 1:
        mixed_int16 = np.repeat(mixed_int16[:, None], n_channels, axis=1).reshape(-1)

    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(mixed_int16.tobytes())
    out_buf.seek(0)
    return out_buf.read(), load_warning


def create_meditation_audio(
    text: str,
    ambient_style: str,
    music_volume_db: int = -18,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    High-Level-Helper für die UI. Erstellt eine Meditation als Audio (TTS + Ambient).

    Args:
        text: Meditationstext
        ambient_style: Ambient-Stil
        music_volume_db: Lautstärke des Hintergrunds in dB

    Returns:
        (audio_bytes, error_message)
    """
    try:
        tts_wav = _call_voice_clone_server(text)
    except Exception as exc:  # noqa: BLE001
        return None, f"XTTS server error: {exc}"

    try:
        mixed_wav, warn = _mix_voice_and_ambient(
            tts_wav,
            ambient_style,
            music_volume_db,
        )
    except Exception as exc:  # noqa: BLE001
        # Fallback: nur Stimme ohne Ambient
        return tts_wav, f"Ambient mix disabled due to error: {exc}"

    return mixed_wav, warn


# ---------------------------------------------------------------------------
# Kleine Persistenz für gespeicherte Meditationen
# ---------------------------------------------------------------------------

INDEX_FILE = DATA_DIR / "meditations.json"


def _load_index() -> Dict[str, Dict[str, str]]:
    """
    Lädt das Index-File mit den gespeicherten Meditationen.
    Returns ein Dict mit Slugs als Keys.
    """
    if not INDEX_FILE.exists():
        return {}
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save_index(index: Dict[str, Dict[str, str]]) -> None:
    """
    Speichert das Index-File für Meditationen.
    """
    INDEX_FILE.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_meditation(
    title: str,
    config: MeditationConfig,
    text: str,
    audio_bytes: Optional[bytes],
) -> None:
    """
    Speichert eine Meditation (Text und Audio) und aktualisiert den Index.

    Args:
        title: Titel der Meditation
        config: MeditationConfig-Objekt
        text: Meditationstext
        audio_bytes: Optional, Audio als WAV-Bytes
    """
    index = _load_index()
    slug = title.strip() or "untitled"
    slug = slug.replace("/", "_")

    entry = {
        "title": title,
        "category": config.category,
        "length": config.length,
        "ambient_style": config.ambient_style,
    }
    index[slug] = entry
    _save_index(index)

    (DATA_DIR / f"{slug}.txt").write_text(text, encoding="utf-8")
    if audio_bytes is not None:
        (DATA_DIR / f"{slug}.wav").write_bytes(audio_bytes)


def list_saved_meditations() -> List[Dict[str, str]]:
    """
    Listet alle gespeicherten Meditationen mit Metadaten auf.
    Returns eine Liste von Dicts mit Slug und Metadaten.
    """
    index = _load_index()
    return [
        {"slug": slug, **meta}
        for slug, meta in sorted(index.items(), key=lambda kv: kv[0].lower())
    ]


def load_meditation(slug: str) -> Tuple[str, Optional[bytes]]:
    """
    Lädt eine gespeicherte Meditation (Text und ggf. Audio) anhand des Slugs.

    Args:
        slug: Slug der Meditation

    Returns:
        (Text, Audio-Bytes oder None)
    """
    text_path = DATA_DIR / f"{slug}.txt"
    audio_path = DATA_DIR / f"{slug}.wav"

    text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
    audio = audio_path.read_bytes() if audio_path.exists() else None
    return text, audio


def delete_meditation(slug: str) -> None:
    """
    Löscht eine gespeicherte Meditation (Text, Audio und Index-Eintrag).

    Args:
        slug: Slug der Meditation
    """
    index = _load_index()
    index.pop(slug, None)
    _save_index(index)

    for ext in (".txt", ".wav"):
        path = DATA_DIR / f"{slug}{ext}"
        try:
            path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except TypeError:
            if path.exists():
                path.unlink()


# Backwards-compat Wrapper
def generate_meditation(category: str, length: str) -> str:
    """
    Wrapper für generate_meditation_text (aus Kompatibilitätsgründen).
    """
    return generate_meditation_text(category, length)
