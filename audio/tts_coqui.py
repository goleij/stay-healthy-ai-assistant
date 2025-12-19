import os
import requests
import tempfile

TTS_URL = os.getenv(
    "RECIPE_TTS_URL",
    "http://tts_server:5005/speak"
)

def speak(text: str) -> str:
    r = requests.post(TTS_URL, json={"text": text}, timeout=120)
    r.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(r.content)
    tmp.close()

    return tmp.name
