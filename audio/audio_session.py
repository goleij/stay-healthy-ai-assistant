# audio/audio_session.py

def start_session(steps: list[str]) -> dict:
    """
    Startet eine neue Audio-Session.
    """
    return {
        "steps": steps,
        "index": 0,
    }


def next_sentence(session: dict, command: str | None) -> str | None:
    """
    Liefert den nächsten Satz basierend auf Sprachkommando.
    Unterstützt:
    - weiter
    - nochmal
    - stopp
    """
    if not session or "steps" not in session:
        return None

    if not command:
        return None

    command = command.lower()

    # ▶️ weiter
    if "weiter" in command or "next" in command or "continue" in command:
        session["index"] += 1

    # 🔁 nochmal
    elif "nochmal" in command or "repeat" in command:
        pass  # gleicher Index

    # ⛔ stopp
    elif "stopp" in command or "stop" in command:
        return None

    else:
        # kein relevantes Kommando
        return None

    # Ende erreicht
    if session["index"] >= len(session["steps"]):
        return None

    return session["steps"][session["index"]]
