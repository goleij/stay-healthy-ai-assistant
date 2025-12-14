import os
os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["COQUI_DISABLE_TOS_PROMPT"] = "1"

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import tempfile
import soundfile as sf
import numpy as np


import nltk
nltk.download("punkt")
nltk.download("punkt_tab")


from TTS.api import TTS

# download punkt tokenizer if needed
try:
    nltk.data.find("tokenizers/punkt")
except:
    nltk.download("punkt")

app = FastAPI()

print("Loading XTTS-v2 model…")
tts = TTS(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
    progress_bar=False,
    gpu=False
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEDITATION_VOICE = os.path.join(BASE_DIR, "lina-voice-meditation.wav")
MOTIVATION_VOICE = os.path.join(BASE_DIR, "lina-voice-motivation.wav")


class SynthesisRequest(BaseModel):
    text: str


def synthesize_chunks(text, speaker_wav):
    """
    Split text into manageable sentences,
    synthesize each sentence separately,
    merge into final WAV.
    """

    # Split text into sentences
    sentences = nltk.sent_tokenize(text)

    wav_segments = []
    sr = None

    for sentence in sentences:
        # short silence between segments
        silence = np.zeros(int(0.4 * 22050), dtype=np.float32)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
            temp_wav = fp.name

        # synthesize the chunk
        tts.tts_to_file(
            text=sentence,
            file_path=temp_wav,
            speaker_wav=speaker_wav,
            language="en"
        )

        audio, sample_rate = sf.read(temp_wav)

        if sr is None:
            sr = sample_rate

        # append: audio + silence pause
        wav_segments.append(audio.astype(np.float32))
        wav_segments.append(silence)

        os.remove(temp_wav)

    # merge everything
    final_audio = np.concatenate(wav_segments)

    # store final file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
        final_path = fp.name

    sf.write(final_path, final_audio, sr)
    return final_path


@app.post("/synthesize_meditation")
def synthesize_meditation(req: SynthesisRequest):
    try:
        result_path = synthesize_chunks(req.text, MEDITATION_VOICE)
        return FileResponse(result_path, media_type="audio/wav")
    except Exception as e:
        return {"error": str(e)}


@app.post("/synthesize_motivation")
def synthesize_motivation(req: SynthesisRequest):
    try:
        result_path = synthesize_chunks(req.text, MOTIVATION_VOICE)
        return FileResponse(result_path, media_type="audio/wav")
    except Exception as e:
        return {"error": str(e)}
