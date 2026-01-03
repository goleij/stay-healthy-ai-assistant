import subprocess
import tempfile
from pathlib import Path
from faster_whisper import WhisperModel


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODEL


def webm_bytes_to_wav16k_mono(webm_bytes: bytes) -> bytes:
    """
    Convert WebM/Opus bytes -> WAV 16kHz mono using ffmpeg.
    """
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        in_path = td / "input.webm"
        out_path = td / "output.wav"

        in_path.write_bytes(webm_bytes)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(in_path),
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            str(out_path),
        ]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            raise RuntimeError(p.stderr.decode(errors="ignore"))

        return out_path.read_bytes()


def transcribe_webm_bytes(webm_bytes: bytes) -> str:
    wav_bytes = webm_bytes_to_wav16k_mono(webm_bytes)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        wav_path = td / "audio.wav"
        wav_path.write_bytes(wav_bytes)

        model = _get_model()
        segments, info = model.transcribe(
            str(wav_path),
            language="en",
            vad_filter=True,
        )

        texts = [seg.text.strip() for seg in segments if seg.text.strip()]
        return " ".join(texts).strip()
