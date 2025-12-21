# Voice Clone Server

## Übersicht

Der Voice Clone Server stellt eine REST-API bereit, mit der sich Text-zu-Sprache (TTS) und Voice Cloning-Funktionen nutzen lassen. Er basiert auf FastAPI/Uvicorn und verwendet moderne TTS-Modelle (z.B. XTTS-v2) für die Sprachausgabe. Die API kann z.B. von anderen Python-Programmen, Web-Apps oder Streamlit-Anwendungen genutzt werden, um synthetische Sprache zu erzeugen oder Stimmen zu klonen.

---

## Features
- Text-zu-Sprache (TTS) für verschiedene Sprachen
- Voice Cloning (Stimmenklonen) mit XTTS-v2
- Einfache REST-API (JSON)
- Schneller Start durch vortrainierte Modelle

---

## Installation & Setup

1. **Python 3.10 Umgebung anlegen**

    ```bash
    cd voice_clone_server
    python3.10 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

2. **(Optional) Modelle vorbereiten**

   Die benötigten TTS-Modelle werden beim ersten Start automatisch heruntergeladen.

---

## Starten des Servers

Im Verzeichnis `voice_clone_server`:

```bash
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 5005
```

Der Server läuft dann unter http://localhost:5005

---

## API-Endpunkte (Beispiel)

- `POST /synthesize` – Text-zu-Sprache (Text → Audio)
- `POST /clone` – Stimme klonen (Audio + Text → neue Stimme)

Die genauen Endpunkte und Parameter findest du im Quellcode (`server.py`) oder per OpenAPI-Dokumentation unter `http://localhost:5005/docs` (nach Serverstart).

---

## Erweiterung

- Neue Modelle oder Sprachen können in `server.py` integriert werden (siehe TTS-Initialisierung).
- Zusätzliche API-Endpunkte lassen sich mit FastAPI einfach ergänzen.
- Für eigene Logik: Funktionen in `server.py` anpassen oder neue Module importieren.

---

## Troubleshooting

- **ImportError/ModuleNotFoundError:** Stelle sicher, dass du im richtigen Verzeichnis bist und die venv aktiviert ist.
- **Modulkonflikte:** Benenne ggf. eigene Projektordner um, die mit Standardbibliotheken kollidieren (z.B. `profile`).
- **Fehlende Modelle:** Beim ersten Start werden Modelle automatisch geladen. Prüfe ggf. die Internetverbindung.

---

## Beispielaufruf (Python)

```python
import requests

response = requests.post(
    'http://localhost:5005/synthesize',
    json={"text": "Hallo, wie geht's?", "lang": "de"}
)
with open('output.wav', 'wb') as f:
    f.write(response.content)
```

---

## Lizenz & Credits

- Nutzt [coqui-ai/TTS](https://github.com/coqui-ai/TTS) und XTTS-v2
- Siehe Lizenzhinweise in den jeweiligen Modulen
