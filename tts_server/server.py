from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile

from TTS.api import TTS

app = FastAPI()

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

VOICE_SAMPLE = "/voices/Miray_Rezept.wav"

class SpeakRequest(BaseModel):
    text: str

@app.post("/speak")
def speak(req: SpeakRequest):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()

    tts.tts_to_file(
        text=req.text,
        speaker_wav=VOICE_SAMPLE,
        language="de",
        file_path=tmp.name,
    )

    return FileResponse(tmp.name, media_type="audio/wav")
