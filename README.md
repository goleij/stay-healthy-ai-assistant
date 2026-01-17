# Stay Healthy AI


------------------------------------------------------------
1. Requirements
------------------------------------------------------------

To run the project you need a few things.

-----------------------------------
Option 1: Run with Docker (suggested)
-----------------------------------

1. Requirements

- Docker
- Docker Compose
- Ollama installed on the host system
(or running as a separate container)

2. Build & Run

- From the project root:
    docker compose up --build
    or (older Docker versions):
    docker-compose up --build

3. Access the app

Once containers are running:

http://localhost:8501

Notes (Docker)

- Ollama must be running and accessible
- Models are detected automatically

-----------------------------------
Option 2: Run with Local Python 
-----------------------------------

 Python
------------

Python 3.10 / 3.11.

Download Python from:

    https://www.python.org/downloads/

On Windows, during install, make sure to enable:

    Add Python to PATH


Please open the Settings in PyCharm and change the project interpreter to Python 3.11. 

 Virtual environment 
-----------------------------------

Inside the project folder:

    python -m venv .venv

Activate it:

    # Windows:
    .venv\Scripts\activate

    # macOS / Linux:
    source .venv/bin/activate

Then install dependencies:

    pip install -r requirements.txt

 Ollama
---------

The app uses local LLMs via Ollama.

Download and install from:

    https://ollama.com/download

Check that it works:

    ollama list

Make sure that Ollama App running in the background.

 At least one LLM model
-------------------------

You must install the following model before running the app:

    ollama pull gemma2:2b

This project is built and tested specifically with gemma2:2b.


 RAG database (optional)
--------------------------

To enable the chatbot's external knowledge base (RAG):

1. Add URLs to index:

       data/urls.txt

   (one URL per line)

2. Build the Chroma DB:

       python prepare_data.py

This creates:

    chroma_db/


------------------------------------------------------------
2. Running the application
------------------------------------------------------------

From the project root (where app_ui.py is):

    streamlit run app_ui.py

By default Streamlit runs at:

    http://localhost:8501

On the first run:

- users.json and profiles.json will be created/updated automatically
  when users sign up and save their profiles.


------------------------------------------------------------
3. Project structure
------------------------------------------------------------

This is the current structure of the project.

Project directory tree:

```text
angewandte-generative-ki/
│
├── app_ui.py
├── app_css.py
├── sidebar_css.py
├── llm_utils.py
├── main.py
├── main_page.py
├── prepare_data.py
├── stt_whisper.py
├── voice_test.py
├── requirements.txt
├── requirements_vcs.txt
├── users.json
├── profiles.json
├── docker-compose.yml
├── Dockerfile.streamlit
├── Dockerfile.voice_clone_server
├── Logo.png
├── README.md
│
├── assets/
│   └── music/
│       ├── low.mp3
│       ├── medium.mp3
│       └── high.mp3
│
├── audio/
│   ├── __init__.py
│   ├── audio_session.py
│   ├── music_mixer.py
│   ├── recipe_llm.py
│   ├── recipe_parser.py
│   └── tts_coqui.py
│
├── auth/
│   ├── __init__.py
│   ├── auth_ui.py
│   ├── auth_logic.py
│   └── auth_css.py
│
├── chatbot/
│   ├── __init__.py
│   ├── chat_ui.py
│   └── chat_css.py
│
├── components/
│   ├── __init__.py
│   ├── silence_component_test.py
│   └── silence_recorder/
│       ├── __init__.py
│       ├── silence_recorder.py
│       └── frontend/
│           ├── index.html
│           └── streamlit.js
│
├── data/
│   └── urls.txt
│
├── landing/
│   ├── __init__.py
│   ├── landing_ui.py
│   └── landing_css.py
│
├── live_stt_server/
│   └── __init__.py
│
├── meditation/
│   ├── __init__.py
│   ├── meditation_ui.py
│   ├── meditation_logic.py
│   ├── meditation_css.py
│   └── ambient/
│
├── onboarding/
│   ├── __init__.py
│   ├── onboarding_ui.py
│   └── onboarding_css.py
│
├── plan/
│   ├── __init__.py
│   ├── plan_ui.py
│   ├── plan_generator.py
│   └── plan_css.py
│
├── profile/
│   ├── __init__.py
│   ├── profile_ui.py
│   ├── profile_css.py
│   └── Recepies/
│       ├── __init__.py
│       ├── library_ui.py
│       └── library_css.py
│
├── profile_ui/
│   ├── __init__.py
│   ├── profile_ui.py
│   ├── profile_css.py
│   └── Recepies/
│       ├── __init__.py
│       ├── library_ui.py
│       └── library_css.py
│
├── scripts/
│   ├── index_urls.py
│   └── index_pdfs.py
│
├── storage/
│   ├── __init__.py
│   ├── file_utils.py
│   └── profile_manager.py
│
├── tts_server/
│   ├── Dockerfile
│   ├── server.py
│   └── voice_samples/
│
├── voice_clone_server/
│   ├── server.py
│   ├── README.md
│   ├── lina-motivation.mp3
│   ├── lina-motivation.wav
│   ├── lina-voice-meditation.mp3
│   └── lina-voice-meditation.wav
│
│
├── wishboard/
│   ├── __init__.py
│   ├── urls.txt
│   ├── wishboard_css.py
│   ├── wishboard_engine.py
│   └── wishboard_ui.py
│
└── chroma_db/
    └── chroma.sqlite3   # generated by prepare_data.py

```
------------------------------------------------------------
5. What each part does
------------------------------------------------------------


Root Level Files
----------------
```text

main.py
    RAG (Retrieval-Augmented Generation) engine. Initializes Chroma vector 
    database, creates embeddings with Ollama, and builds QA chains for 
    retrieval-based question answering from indexed documents.

main_page.py
    Main page router. Checks if user has a profile, validates available 
    Ollama models, and routes to either the Plan or Chat view.

app_ui.py
    Main Streamlit application entry point. Configures the page, handles 
    authentication flow (landing → auth → main app), manages sidebar 
    navigation between all pages.

app_css.py
    Global CSS styling. Injects app-wide styles including wave backgrounds, 
    transparent headers, color variables, button styles, and responsive design.

llm_utils.py
    LLM utility functions. Provides cached Ollama LLM instances, lists 
    available local models, and manages RAG QA chains per model.

prepare_data.py
    Data preparation script. Loads documents (PDFs, CSVs, text files, URLs), 
    splits them into chunks, and creates a persistent Chroma vector database.

stt_whisper.py
    Speech-to-Text using Whisper. Converts WebM audio bytes to WAV, then 
    transcribes using faster-whisper model with VAD filtering.

sidebar_css.py
    Sidebar-specific CSS. Styles sidebar buttons to be compact and mobile-friendly.

voice_test.py
    Voice activity detection test. Uses WebRTC for real-time audio capture 
    and VAD to detect speech.

profiles.json
    User profiles storage. Stores all user profiles, settings, plans, and chat histories.

users.json
    User credentials storage. Stores usernames, emails, and bcrypt-hashed passwords.

Logo.png
    Application logo displayed on the landing page and throughout the app.


auth/ - Authentication Module
-----------------------------

auth_ui.py
    Renders login and signup forms, handles form submission, validates 
    credentials, and manages session state upon successful login.

auth_logic.py
    Validates email format, handles user signup with bcrypt password hashing, 
    and login verification (supports username or email login).

auth_css.py
    CSS for login/signup pages including wave backgrounds, form styling, 
    and button hover effects.


landing/ - Landing Page Module
------------------------------

landing_ui.py
    Displays the app logo, feature badges, and buttons for signup and login.

landing_css.py
    Fullscreen centered card layout, radial gradient background, and button styling.


onboarding/ - Onboarding Wizard Module
--------------------------------------

onboarding_ui.py
    Multi-step onboarding form. Guides users through 10 questions (goal, weight, 
    height, age, gender, activity level, diet preferences, allergies, health 
    conditions, workout days). Step 11 generates the personalized 7-day plan.

onboarding_css.py
    CSS for form layout, progress bar, navigation buttons, and the full-screen 
    loading overlay shown during plan generation.


plan/ - Fitness & Diet Plan Module
----------------------------------

plan_ui.py
    Shows the generated 7-day plan with expandable days, meal sections, and 
    "Voice Mode" buttons that generate audio recipe guides with background music.

plan_generator.py
    Builds detailed LLM prompts for each day based on user profile. Handles 
    special cases like wheelchair users, broken limbs, diabetes, and heart 
    conditions. Includes post-processing for meal macro normalization and 
    allergy filtering.

plan_css.py
    Styles for Voice Mode buttons, text colors, and expander styling.


chatbot/ - AI Chatbot Module
----------------------------

chat_ui.py
    Full-featured chat UI with voice input (using silence detection), 
    LLM-powered responses, Text-to-Speech output, and chat history management.

chat_css.py
    CSS for chat layout, message bubbles, input fields, and button styling.


meditation/ - Meditation Studio Module
--------------------------------------

meditation_ui.py
    Allows users to select meditation style (Mindfulness/Breathing/Sleep), 
    length, ambient sound (waves/forest/rain), and volume. Creates meditation 
    audio with cloned voice and saves meditations.

meditation_logic.py
    Template-based text generation for meditations, TTS synthesis via XTTS 
    voice cloning server, ambient sound mixing, and meditation persistence.

meditation_css.py
    Green-themed radio buttons, slider styling, and layout CSS.


wishboard/ - Wish Board Module
------------------------------

wishboard_ui.py
    Users can write food wishes (e.g., "I want healthy chips"), and the 
    assistant responds with suggestions.

wishboard_engine.py
    Search and recipe extraction engine. Loads/saves search indexes, tokenizes 
    queries, extracts text from HTML, and parses recipe structures.

wishboard_css.py
    Chat bubble styles, header styling, and input field formatting.

urls.txt
    URL list for recipe indexing.


profile_ui/ - User Profile Module
---------------------------------

profile_ui.py
    Displays user avatar with upload/remove, personal info grid (weight, height, 
    age, gender, activity, workouts), and health information.

profile_css.py
    CSS for avatar circle, info grid layout, and input field backgrounds.

Recepies/library_ui.py
    Displays saved recipes and shopping lists with expandable sections.

Recepies/library_css.py
    Library page styling for background waves and buttons.


storage/ - Data Persistence Module
----------------------------------

profile_manager.py
    Loads/saves users and profiles from JSON files, ensures session defaults, 
    and syncs session state to/from disk.

file_utils.py
    Simple functions for loading and saving JSON files with error handling.


audio/ - Audio Processing Module
--------------------------------

audio_session.py
    Voice-guided cooking session manager. Manages step-by-step audio playback 
    with voice commands (next, repeat, stop).

music_mixer.py
    Mixes TTS voice audio with background music, applies volume adjustments 
    and fade in/out effects.

tts_coqui.py
    TTS client for recipes. Sends text to the TTS server and returns audio.

recipe_llm.py
    Uses LLM to generate 5-7 simple cooking steps for voice guidance.

recipe_parser.py
    Splits day plan into meals and extracts meal names from plan blocks.


components/ - Custom Streamlit Components
-----------------------------------------

silence_recorder/silence_recorder.py
    Custom Streamlit component that records audio and auto-stops after 
    detecting silence. Configurable thresholds for silence detection.

silence_recorder/frontend/
    HTML/JS frontend for the silence recorder component.


voice_clone_server/ - Voice Cloning TTS Server
----------------------------------------------

server.py
    FastAPI server that synthesizes speech using XTTS-v2 model with custom 
    voice samples for meditation and motivation. Splits long texts into 
    sentences for better synthesis.


tts_server/ - Basic TTS Server
------------------------------

server.py
    FastAPI server using XTTS for recipe narration with a fixed voice sample.

Dockerfile
    Docker configuration for the TTS server.


scripts/ - CLI Utilities
------------------------

index_pdfs.py
    CLI tool to extract text from PDFs, chunk them, and save to a JSON 
    index for the wishboard search.

index_urls.py
    CLI tool to index recipe URLs for the wishboard search engine.


Docker Configuration
--------------------

docker-compose.yml
    Defines three services: voice_clone_server (port 5008), tts_server 
    (port 5006), and streamlit-app (port 8501).

Dockerfile.streamlit
    Python 3.11 base, installs FFmpeg and dependencies, runs Streamlit app.

Dockerfile.voice_clone_server
    Python 3.10 base, installs TTS from source, runs XTTS FastAPI server.


Dependencies
------------

requirements.txt
    Main app dependencies including Streamlit, LangChain, ChromaDB, Ollama, 
    bcrypt, BeautifulSoup, pydub, and faster-whisper.

requirements_vcs.txt
    Voice server dependencies including TTS from Coqui, PyTorch 2.1, 
    transformers, and FastAPI.


Data Folders
------------

data/
    Contains source documents (PDFs, CSVs, URLs) for RAG indexing.

assets/music/
    Background music files for different intensity levels (low, medium, high).

meditation/ambient/
    Ambient sound files (ocean waves, forest birds, rain).

meditation_data/
    Saved meditation sessions.

chroma_db/
    Vector database for RAG, generated by prepare_data.py.

```