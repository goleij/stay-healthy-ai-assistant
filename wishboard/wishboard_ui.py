# wishboard_ui.py (optimierte Version mit Ernährungsstilen)

import os
import html
import json
import requests
from typing import List, Dict

import streamlit as st
from . import wishboard_css as css

#Verbindet Chat mit Nutzerprofil
#Einziger Zugriffspunkt auf Profildaten

def load_user_profile(username: str) -> dict:
    """
    Lädt das Profil eines Nutzers aus profiles.json.
    Wird für personalisierte KI-Antworten verwendet.
    """
    try:
        with open("profiles.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(username, {}).get("profile", {})
    except Exception:
        return {}





# ---------------------------------------------------------
# ask_ollama – Schnittstelle zur KI
# ---------------------------------------------------------
# ZWECK:
# Sendet einen Prompt an das lokale LLM (Ollama)
# und zeigt die Antwort LIVE im UI an.
# TECHNIK:
# - HTTP POST Request
# - Streaming Response (Server-Sent Events)
# - JSON-Chunks werden nacheinander verarbeitet
# ---------------------------------------------------------
def ask_ollama(prompt: str, model: str = "gemma2:2b") -> str:
    buffer = ""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt},
            stream=True,
            timeout=60,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
            except Exception:
                continue

            chunk = data.get("response", "")
            if chunk:
                buffer += chunk

        return buffer.strip()

    except Exception as e:
        return f"Fehler bei Ollama: {e}"



# ---------------------------------------------------------
# Rezept-Erkennung (damit RAG nur dann genutzt wird)
# ZWECK:
# Erkennt, ob die Nutzereingabe wahrscheinlich
# eine Essens- oder Rezeptanfrage ist.
# RAG Soll nur ausgeführt werden, wenn es Sinn macht
#
# TECHNIK:
# - Keyword-basierte Heuristik
# ---------------------------------------------------------
def is_recipe_request(text: str) -> bool:
    text = text.lower()

    recipe_keywords = [
        # Allgemeine Koch-/Backverben
        "rezept", "koch", "koche", "kochen",
        "backe", "backen", "zubereitung", "zutaten",
        "gericht", "essen", "mahlzeit", "snack",
        "ich will", "ich möchte", "mach", "mache",

        # Sweets & Desserts
        "muffins", "kuchen", "brownies", "donuts",
        "eis", "ice", "icecream", "nicecream",
        "dessert", "nachtisch", "pudding",
        "torte", "cupcakes", "gummibärchen",
        "schokolade", "kekse", "cookies",

        # Snacks
        "chips", "cracker", "popcorn",
        "wrap", "sandwich", "toast",

        # Herzhaftes
        "pizza", "burger", "lasagne",
        "pasta", "nudeln", "spaghetti",
        "risotto", "auflauf", "salat",

        # Protein/Savory
        "hähnchen", "chicken", "pute",
        "lachs", "fisch", "thunfisch",
        "rind", "hackfleisch",

        # Bowls & Healthy Foods
        "bowl", "smoothie", "shake",
        "overnight oats", "porridge",

        # Sonstiges Essen
        "frühstück", "mittagessen", "abendessen",
        "snackidee", "snack ideen",

        # Generische Essenswörter
        "gericht", "kochst", "rezepte", "idee",
    ]
    # True, sobald ein Schlüsselwort gefunden wird
    return any(k in text for k in recipe_keywords)


# ---------------------------------------------------------
# Ernährungsstil-Erkennung (Low-Carb, High-Protein, Vegan usw.)
#Zweck: Prompt Kontrolle, Konsistente, gezielte KI-Ausgaben.
#Technik: regelbasierte Klassifikation.
# ---------------------------------------------------------
def detect_recipe_style(text: str) -> str:
    """
    Versucht aus der Nutzeranfrage einen gewünschten Ernährungsstil zu erkennen.
    Rückgabe ist einer dieser Strings:
    'lowcarb', 'highprotein', 'vegan', 'zuckerfrei',
    'lowfat', 'glutenfrei', 'paleo', 'keto', 'healthy'
    """
    t = text.lower()

    if "keto" in t:
        return "keto"
    if "paleo" in t:
        return "paleo"
    if "glutenfrei" in t or "gluten-frei" in t or "ohne gluten" in t:
        return "glutenfrei"
    if "lowcarb" in t or "low carb" in t or "kohlenhydratarm" in t:
        return "lowcarb"
    if "high protein" in t or "high-protein" in t or "viel eiweiß" in t or "viel eiweiss" in t:
        return "highprotein"
    if "vegan" in t:
        return "vegan"
    if "zuckerfrei" in t or "ohne zucker" in t or "sugar free" in t:
        return "zuckerfrei"
    if "low fat" in t or "fettarm" in t or "fett-arm" in t:
        return "lowfat"

    # Standard: gesund, aber ohne speziellen Stil
    return "healthy"


# ---------------------------------------------------------
# Profil-Kontext für KI-Prompts
# ---------------------------------------------------------
# Wandelt ein Nutzerprofil in Text um,
# der der KI als Kontext übergeben wird.
# Personalisierte Rezepte
# Berücksichtigung von Ziel, Aktivität, Allergien

def build_profile_context(profile: dict) -> str:
    if not profile:
        return ""

    health_conditions = profile.get("health_conditions") or []
    limitations = profile.get("limitations") or []
    health_issues = profile.get("health_issues") or ""

    return f"""
Nutzerprofil:
- Alter: {profile.get('age')}
- Geschlecht: {profile.get('gender')}
- Ziel: {profile.get('goal')}
- Aktivitätslevel: {profile.get('activity')}
- Ernährung: {profile.get('diet')}
- Allergien: {profile.get('allergies')}

Gesundheitliche Aspekte:
- Krankheiten / Diagnosen: {", ".join(health_conditions) if health_conditions else "keine bekannt"}
- Gesundheitliche Probleme: {health_issues if health_issues else "keine"}
- Einschränkungen: {", ".join(limitations) if limitations else "keine"}
"""




# ---------------------------------------------------------
# RAG-Relevanzprüfung
# ---------------------------------------------------------
# ZWECK:
# Prüft, ob ein gefundenes Rezept wirklich
# zur Anfrage des Nutzers passt.
#
# Damit keine Falsche Rezepte gezeigt werden und für Antwortqualität
# ---------------------------------------------------------

def is_relevant_to_query(recipe_text: str, user_query: str) -> bool:
    """Prüft, ob das RAG-Rezept thematisch zur Anfrage passt."""
    q = user_query.lower().strip()
    t = recipe_text.lower()

    # Wichtige Wörter extrahieren
    words = [w for w in q.split() if len(w) > 3]

    # Wenn kein Wort im Rezept vorkommt → nicht relevant
    return any(w in t for w in words)

# ---------------------------------------------------------
# KI: Gesundes Rezept im gewünschten Stil erzeugen
# ZWECK:
# Erstellt ein komplett neues, gesundes Rezept,
# wenn kein passendes RAG-Ergebnis existiert.
# ---------------------------------------------------------
def generate_styled_recipe(user_text: str, style: str, profile: dict) -> str:
    style_descriptions = {
        "lowcarb": "ein gesundes Low-Carb Rezept (sehr wenige Kohlenhydrate, kein Industriezucker)",
        "highprotein": "ein gesundes High-Protein Rezept (viel Eiweiß, wenig Fett, kein Industriezucker)",
        "vegan": "ein gesundes veganes Rezept (keine tierischen Produkte, vollwertige Zutaten)",
        "zuckerfrei": "ein gesundes zuckerfreies Rezept (kein Haushaltszucker, nur Stevia/Erythrit oder natürliche Süße)",
        "lowfat": "ein gesundes fettarmes Rezept (wenig Fett, leichte Zutaten)",
        "glutenfrei": "ein gesundes glutenfreies Rezept (ohne Gluten, mit verträglichen Alternativen)",
        "paleo": "ein gesundes Paleo-Rezept (unverarbeitete Lebensmittel, kein Zucker, kein Getreide)",
        "keto": "ein gesundes Keto-Rezept (sehr wenige Kohlenhydrate, viel gute Fette, moderates Protein)",
        "healthy": "ein gesundes, ausgewogenes Rezept (natürliche Zutaten, wenig Zucker und wenig Fett)",
    }

    desc = style_descriptions.get(style, style_descriptions["healthy"])

    # Profil-Kontext für die KI erzeugen
    profile_context = build_profile_context(profile)

    # Prompt inklusive Nutzerprofil bauen
    prompt = (
            profile_context +
            "\nDu bist ein gesunder Ernährungscoach.\n"
            f"Erstelle ein passendes Rezept für: {user_text}\n\n"
            "Vorgaben:\n"
            "- Das Rezept MUSS zum Nutzerprofil passen.\n"
            "- Berücksichtige Ziel, Aktivitätslevel, Allergien und gesundheitliche Einschränkungen.\n"
            "- Vermeide Zutaten oder Zubereitungen, die für den Nutzer ungeeignet sein könnten.\n"
            "- Antworte NUR mit folgendem Format:\n"
            "Zutaten:\n"
            "- ...\n\n"
            "Zubereitung:\n"
            "1. ...\n"
    )

    return ask_ollama(prompt)


# ---------------------------------------------------------
# Debug-Modus: zeigt Rohdaten aus dem Index
# ---------------------------------------------------------
def debug_request(user_text: str) -> str:
    term = user_text.replace("debug", "", 1).strip()

    try:
        from .wishboard_engine import search_index
        results = search_index(term, top_k=5)
    except Exception as e:
        return f"Debug-Fehler: {e}"

    if not results:
        return f"Keine Treffer im Index für: '{term}'"

    out = ["🔍 DEBUG TREFFER:"]
    for r in results:
        out.append(
            f"\nQuelle: {r.get('source')}\n"
            f"Score: {r.get('score')}\n"
            f"Snippet: {r.get('snippet')[:200]}..."
        )
    return "\n".join(out)


# ---------------------------------------------------------
# Streamlit Session State
# Speichert Chatverlauf & Eingabefeld
# zwischen UI-Neurenderings
# ---------------------------------------------------------
def _ensure_state() -> None:
    if "wishboard_chat" not in st.session_state:
        st.session_state["wishboard_chat"] = []
    if "wishboard_input" not in st.session_state:
        st.session_state["wishboard_input"] = ""


def _add_user_message(text: str):
    st.session_state["wishboard_chat"].append({"role": "user", "text": text})


def _add_assistant_message(text: str):
    st.session_state["wishboard_chat"].append({"role": "assistant", "text": text})


# ---------------------------------------------------------
# Haupt-Logik: RAG + KI mit Ernährungsstilen
# ---------------------------------------------------------
def _generate_assistant_reply(user_text: str, profile: dict) -> str:

    raw_text = user_text.strip()
    if not raw_text:
        return "Wie kann ich dir helfen?"

    lower_text = raw_text.lower()

    # Debug-Modus
    if lower_text.startswith("debug"):
        return debug_request(raw_text)

    # Prüfen, ob es überhaupt um Essen / Rezepte geht
    recipe_requested = is_recipe_request(raw_text)

    # ---------------------------------------------------------
    # Nur bei Rezeptanfragen → RAG-Suche (URLs + PDFs)
    # ---------------------------------------------------------
    results = []
    if recipe_requested:
        try:
            from .wishboard_engine import search_index, format_search_results
            results = search_index(raw_text, top_k=3)
        except Exception:
            results = []

    # ---------------------------------------------------------
    # Wenn RAG etwas gefunden hat → Rezept nur formatieren
    # ---------------------------------------------------------
    if recipe_requested and results:
        from .wishboard_engine import format_search_results

        recipe_raw = format_search_results(results).strip()

        # Prüfen, ob das RAG-Rezept thematisch passend ist
        if recipe_raw and is_relevant_to_query(recipe_raw, user_text):
            prompt = (
                "Formatiere dieses Rezept klar und übersichtlich. "
                "Gib NUR 'Zutaten:' und 'Zubereitung:' aus.\n\n"
                f"{recipe_raw}"
            )
            formatted = ask_ollama(prompt)
            return f"Hier ist ein Rezept aus meinen Quellen:\n\n{formatted}"
        else:
            # NICHT passendes Rezept → sofort zur KI
            style = detect_recipe_style(user_text)
            generated = generate_styled_recipe(user_text, style, profile)

            return f"Hier ist ein gesundes {style}-Rezept für dich:\n\n{generated}"

    # ---------------------------------------------------------
    # KEIN Treffer im Index ODER kein gültiges Rezept → KI erzeugt gesundes Rezept
    #     mit automatisch erkanntem Ernährungsstil
    # ---------------------------------------------------------
    if recipe_requested:
        style = detect_recipe_style(raw_text)
        generated = generate_styled_recipe(raw_text, style, profile)

        # Kleiner Text für das Label
        style_labels = {
            "lowcarb": "Low-Carb",
            "highprotein": "High-Protein",
            "vegan": "vegan",
            "zuckerfrei": "zuckerfrei",
            "lowfat": "fettarm",
            "glutenfrei": "glutenfrei",
            "paleo": "Paleo",
            "keto": "Keto",
            "healthy": "gesund",
        }
        label = style_labels.get(style, "gesund")

        return f"Hier ist ein gesundes {label}-Rezept für dich:\n\n{generated}"

    # ---------------------------------------------------------
    # Keine Essensanfrage → normale KI-Antwort
    # ---------------------------------------------------------
    normal_prompt = (
        "Du bist ein hilfreicher, freundlicher KI-Assistent. "
        "Antworte klar, knapp und auf Deutsch.\n\n"
        f"Nutzer: {raw_text}\n\n"
        "Antwort:"
    )
    return ask_ollama(normal_prompt)


# ---------------------------------------------------------
# UI Rendering
# ---------------------------------------------------------
def render_wishboard_chat() -> None:
    css.load_css()
    _ensure_state()

    st.markdown(
        '<div class="wishboard-header"><h2>Wishboard</h2></div>',
        unsafe_allow_html=True,
    )

    # Chat-Verlauf
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["wishboard_chat"]:
            role = msg["role"]
            if role == "user":
                text = html.escape(msg["text"]).replace("\n", "<br>")
            else:
                text = msg["text"]  # Markdown für KI-Antworten erlauben

            bubble_class = (
                "chat-bubble-user" if role == "user" else "chat-bubble-assistant"
            )
            row_class = "chat-row chat-user" if role == "user" else "chat-row chat-assistant"

            st.markdown(
                f'<div class="{row_class}"><div class="{bubble_class}">{text}</div></div>',
                unsafe_allow_html=True
            )

    # Eingabe & Senden
    cols = st.columns([8, 1])
    with cols[0]:
        st.text_input(
            "Nachricht",
            key="wishboard_input",
            placeholder="z.B. 'Ich will Chips' oder 'Low Carb Schokorezept'",
        )
    with cols[1]:
        st.button("Senden", key="wishboard_send", on_click=_on_send_click)


def _on_send_click():
    text = st.session_state["wishboard_input"].strip()
    if not text:
        return

    _add_user_message(text)
    profile = load_user_profile("Miray")  # später dynamisch
    reply = _generate_assistant_reply(text, profile)
    _add_assistant_message(reply)
    st.session_state["wishboard_input"] = ""


def app():
    render_wishboard_chat()


def render_wishboard_page():
    render_wishboard_chat()


if __name__ == "__main__":
    app()
