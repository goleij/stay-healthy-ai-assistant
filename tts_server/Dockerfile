FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 🔒 Transformers + Tokenizers – EXAKT passend
RUN pip install --no-cache-dir \
    transformers==4.35.2 \
    tokenizers==0.14.1

# 🔒 Coqui TTS + Runtime-Abhängigkeiten
RUN pip install --no-cache-dir \
    TTS \
    librosa \
    numpy \
    scipy \
    soundfile \
    fastapi \
    uvicorn

# ✅ IMPORTANT: force torch AFTER TTS (TTS can upgrade torch)
RUN pip install --no-cache-dir \
    "torch<2.6" \
    "torchaudio<2.6"

COPY voice_samples /voices
COPY server.py /app/server.py

ENV COQUI_TOS_AGREED=1
ENV COQUI_DISABLE_TOS_PROMPT=1

EXPOSE 5005
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5005"]
