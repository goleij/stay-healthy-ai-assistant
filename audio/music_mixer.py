import tempfile
from pydub import AudioSegment

def mix_tts_with_music(
    tts_wav_path: str,
    music_path: str,
    music_gain_db: int = -18,
    fade_in_ms: int = 1200,
    fade_out_ms: int = 1200,
) -> str:
    voice = AudioSegment.from_wav(tts_wav_path)
    music = AudioSegment.from_file(music_path)

    music = (music + music_gain_db).fade_in(fade_in_ms).fade_out(fade_out_ms)

    if len(music) < len(voice):
        reps = (len(voice) // len(music)) + 1
        music = (music * reps)[: len(voice)]
    else:
        music = music[: len(voice)]

    mixed = music.overlay(voice)

    out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    out.close()
    mixed.export(out.name, format="wav")
    return out.name
