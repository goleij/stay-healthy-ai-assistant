# wishboard_ui.py (optimiert: Ernährungsstile + Health Guardrails pro User)

import os
import html
import json
import re

import streamlit as st
from . import wishboard_css as css


# ---------------------------------------------------------
# Profil laden
# ---------------------------------------------------------
def load_user_profile(username: str) -> dict:
    """
    Lädt das Profil eines Nutzers aus profiles.json (robust, egal wo gestartet wird).
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(base_dir, "..", "profiles.json")

        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get(username, {}).get("profile", {})
    except Exception as e:
        print("Profil-Ladefehler:", e)
        return {}


# ---------------------------------------------------------
# Profil-Normalisierung
# ---------------------------------------------------------
def _normalize_list(x) -> list[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return []
        return [s]
    return [str(x).strip()]


def _normalize_allergies(profile: dict) -> list[str]:
    """
    Allergien/Unverträglichkeiten können String oder Liste sein.
    Gibt eine Liste lower-case tokens zurück.
    """
    a = profile.get("allergies", "")
    items = _normalize_list(a)
    # Splitte auch "Gluten, Nüsse" etc.
    out = []
    for it in items:
        for part in re.split(r"[,;/|]+", it):
            p = part.strip().lower()
            if p:
                out.append(p)
    return list(dict.fromkeys(out))


def _get_conditions(profile: dict) -> list[str]:
    """
    Krankheiten/Diagnosen:
    - health_conditions (Liste oder String)
    - health_issues (Freitext)
    -> normalisiert auf lower-case tokens
    """
    cond = _normalize_list(profile.get("health_conditions"))
    issues = str(profile.get("health_issues", "") or "").strip()
    if issues:
        cond.append(issues)

    # Splitte grob auf Trennzeichen
    out = []
    for it in cond:
        for part in re.split(r"[,;/|]+", it):
            p = part.strip().lower()
            if p:
                out.append(p)
    return list(dict.fromkeys(out))


# ---------------------------------------------------------
# Health Rules (erweiterbar)
# ---------------------------------------------------------
# Idee: Wir matchen "keys" als Substring in conditions/allergies.
# Du kannst hier jederzeit neue Krankheiten ergänzen.
HEALTH_RULES = {
    # --- Diabetes / Prädiabetes ---
    "diabetes": {
        "prompt_rules": [
            "KEIN zugesetzter Zucker (kein Honig, Ahornsirup, Agave, Sirup, Marmelade, gezuckerte Produkte).",
            "Wenn süß: nur Erythrit oder Stevia oder gar keine Süße.",
            "Bevorzuge ballaststoffreiche Zutaten, Low-GI/Low-GL.",
            "Ziel: <= 25g Kohlenhydrate pro Portion. Wenn nicht möglich, biete eine Alternative mit weniger Carbs an.",
        ],
        "block_terms": ["zucker", "honig", "ahornsirup", "agave", "sirup", "marmelade", "gezuckert", "kondensmilch", "cola", "limonade"],
    },
    "prädiabetes": {  # alias
        "prompt_rules": [
            "KEIN zugesetzter Zucker (kein Honig, Ahornsirup, Agave, Sirup).",
            "Bevorzuge ballaststoffreiche Zutaten, Low-GI/Low-GL.",
            "Ziel: <= 30g Kohlenhydrate pro Portion.",
        ],
        "block_terms": ["zucker", "honig", "ahornsirup", "agave", "sirup", "marmelade", "gezuckert"],
    },

    # --- Zöliakie / Gluten ---
    "gluten": {
        "prompt_rules": [
            "100% glutenfrei. Keine Zutaten mit Weizen/Roggen/Gerste/Dinkel/Seitan.",
            "Nutze glutenfreie Alternativen (Reis, Mais, Buchweizen, Hirse, Kartoffeln, glutenfreie Haferflocken).",
        ],
        "block_terms": ["weizen", "roggen", "gerste", "dinkel", "seitan", "bulgur", "couscous", "panko", "paniermehl", "weizenmehl"],
    },
    "zöliakie": {  # alias
        "prompt_rules": [
            "100% glutenfrei. Keine Zutaten mit Weizen/Roggen/Gerste/Dinkel/Seitan.",
        ],
        "block_terms": ["weizen", "roggen", "gerste", "dinkel", "seitan", "bulgur", "couscous", "panko", "paniermehl", "weizenmehl"],
    },

    # --- Reflux / GERD (konservativ) ---
    "reflux": {
        "prompt_rules": [
            "Magenfreundlich: vermeide sehr fettig, sehr scharf, viel Zitrus, sehr tomatenlastig, Minze und große Mengen Schokolade.",
        ],
        "block_terms": ["chili", "jalapeno", "sehr scharf", "scharf", "tomatensauce", "zitrone", "orange", "minze"],
    },
    "gerd": {  # alias
        "prompt_rules": [
            "Magenfreundlich: vermeide sehr fettig, sehr scharf, viel Zitrus, sehr tomatenlastig, Minze.",
        ],
        "block_terms": ["chili", "jalapeno", "scharf", "tomatensauce", "zitrone", "orange", "minze"],
    },

    # --- Hypertonie / Bluthochdruck (konservativ) ---
    "bluthochdruck": {
        "prompt_rules": [
            "Salzarm kochen, vermeide stark verarbeitete Lebensmittel und sehr salzige Zutaten.",
            "Nutze Kräuter/Gewürze statt viel Salz.",
        ],
        "block_terms": ["salami", "speck", "wurst", "chips", "salzstangen", "fertigsauce", "tütensuppe", "instant"],
    },
    "hypertonie": {  # alias
        "prompt_rules": [
            "Salzarm kochen, vermeide stark verarbeitete Lebensmittel und sehr salzige Zutaten.",
        ],
        "block_terms": ["salami", "speck", "wurst", "chips", "salzstangen", "fertigsauce", "tütensuppe", "instant"],
    },

    # --- Laktose (Allergie/Intoleranz) ---
    "laktose": {
        "prompt_rules": [
            "Laktosefrei: verwende laktosefreie Milchprodukte oder pflanzliche Alternativen.",
        ],
        "block_terms": ["milch", "sahne", "joghurt", "quark", "käse", "butter"],
    },

    # --- Nuss-Allergie (konservativ) ---
    "nuss": {
        "prompt_rules": [
            "Nussfrei: keine Nüsse, kein Nussmus, keine Spuren-Zutaten wie Mandelmehl/Erdnussbutter.",
        ],
        "block_terms": ["mandel", "haselnuss", "walnuss", "cashew", "erdnuss", "pistazie", "nuss", "nussmus", "erdnussbutter", "mandelmehl"],
    },
}


def build_health_guardrails(profile: dict) -> dict:
    """
    Baut aus Allergien + Diagnosen eine konsolidierte Menge an:
    - prompt_rules: Regeln, die in den Prompt müssen
    - block_terms: Begriffe, die wir im Output/RAG blocken
    - tags: gematchte Schlüssel (für Debug/Transparenz, optional)
    """
    allergies = _normalize_allergies(profile)
    conditions = _get_conditions(profile)

    # Allergien als Bedingungen “mappen” (z.B. "Gluten" -> gluten)
    # Außerdem: wenn Allergien genau Krankheitsschlüssel enthalten (z.B. "laktose").
    merged = conditions + allergies

    prompt_rules: list[str] = []
    block_terms: list[str] = []
    tags: list[str] = []

    for item in merged:
        for key, rule in HEALTH_RULES.items():
            if key in item:
                tags.append(key)
                prompt_rules.extend(rule.get("prompt_rules", []))
                block_terms.extend(rule.get("block_terms", []))

    # Duplikate entfernen
    tags = list(dict.fromkeys(tags))
    prompt_rules = list(dict.fromkeys(prompt_rules))
    block_terms = list(dict.fromkeys(block_terms))

    return {"prompt_rules": prompt_rules, "block_terms": block_terms, "tags": tags}


def violates_guardrails(text: str, guardrails: dict) -> bool:
    """
    Prüft ob Text gegen block_terms verstößt.
    (Heuristik, aber sehr effektiv in der Praxis.)
    """
    t = (text or "").lower()
    return any(term in t for term in guardrails.get("block_terms", []))


# ---------------------------------------------------------
# ask_ollama – Schnittstelle zur KI (über get_llm)
# ---------------------------------------------------------
def ask_ollama(prompt: str, model: str = "gemma2:2b") -> str:
    try:
        from llm_utils import get_llm

        llm = get_llm(model)
        if hasattr(llm, "invoke"):
            result = llm.invoke(prompt)
        else:
            result = llm(prompt)

        return str(result).strip()

    except Exception as e:
        return f"Fehler bei Ollama: {e}"


# ---------------------------------------------------------
# Rezept-Erkennung
# ---------------------------------------------------------
def is_recipe_request(text: str) -> bool:
    text = text.lower()

    recipe_keywords = [
        "rezept", "koch", "koche", "kochen",
        "backe", "backen", "zubereitung", "zutaten",
        "gericht", "essen", "mahlzeit", "snack",
        "ich will", "ich möchte", "mach", "mache",

        "muffins", "kuchen", "brownies", "donuts",
        "eis", "ice", "icecream", "nicecream",
        "dessert", "nachtisch", "pudding",
        "torte", "cupcakes", "gummibärchen",
        "schokolade", "kekse", "cookies",

        "chips", "cracker", "popcorn",
        "wrap", "sandwich", "toast",

        "pizza", "burger", "lasagne",
        "pasta", "nudeln", "spaghetti",
        "risotto", "auflauf", "salat",

        "hähnchen", "chicken", "pute",
        "lachs", "fisch", "thunfisch",
        "rind", "hackfleisch",

        "bowl", "smoothie", "shake",
        "overnight oats", "porridge",

        "frühstück", "mittagessen", "abendessen",
        "snackidee", "snack ideen",

        "rezepte", "idee",
    ]

    return any(k in text for k in recipe_keywords)


# ---------------------------------------------------------
# Ernährungsstil-Erkennung
# ---------------------------------------------------------
def detect_recipe_style(text: str) -> str:
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

    return "healthy"


# ---------------------------------------------------------
# Profil-Kontext für KI-Prompts
# ---------------------------------------------------------
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
- Krankheiten / Diagnosen: {", ".join(health_conditions) if isinstance(health_conditions, list) and health_conditions else (health_conditions if health_conditions else "keine bekannt")}
- Gesundheitliche Probleme: {health_issues if health_issues else "keine"}
- Einschränkungen: {", ".join(limitations) if isinstance(limitations, list) and limitations else (limitations if limitations else "keine")}
""".strip()


# ---------------------------------------------------------
# RAG-Relevanzprüfung
# ---------------------------------------------------------
def is_relevant_to_query(recipe_text: str, user_query: str) -> bool:
    q = user_query.lower().strip()
    t = recipe_text.lower()
    words = [w for w in q.split() if len(w) > 3]
    return any(w in t for w in words)


# ---------------------------------------------------------
# KI: Gesundes Rezept im gewünschten Stil erzeugen (mit Guardrails + Auto-Repair)
# ---------------------------------------------------------
def generate_styled_recipe(user_text: str, style: str, profile: dict) -> str:
    style_descriptions = {
        "lowcarb": "ein gesundes Low-Carb Rezept (wenige Kohlenhydrate)",
        "highprotein": "ein gesundes High-Protein Rezept (viel Eiweiß, ausgewogen)",
        "vegan": "ein gesundes veganes Rezept (keine tierischen Produkte, vollwertige Zutaten)",
        "zuckerfrei": "ein gesundes zuckerfreies Rezept (kein Haushaltszucker)",
        "lowfat": "ein gesundes fettarmes Rezept (wenig Fett, leichte Zutaten)",
        "glutenfrei": "ein gesundes glutenfreies Rezept (ohne Gluten, mit Alternativen)",
        "paleo": "ein gesundes Paleo-Rezept (unverarbeitet, kein Getreide, kein Zucker)",
        "keto": "ein gesundes Keto-Rezept (sehr wenige Kohlenhydrate, gute Fette)",
        "healthy": "ein gesundes, ausgewogenes Rezept (natürliche Zutaten)",
    }

    desc = style_descriptions.get(style, style_descriptions["healthy"])
    profile_context = build_profile_context(profile)
    guard = build_health_guardrails(profile)

    # Health-Regeln in Prompt
    health_rules_text = ""
    if guard["prompt_rules"]:
        health_rules_text = "Gesundheits-Regeln (strikt einhalten):\n" + "\n".join(f"- {r}" for r in guard["prompt_rules"])

    prompt = (
        (profile_context + "\n\n" if profile_context else "")
        + "Du bist ein gesunder Ernährungscoach.\n"
        + f"Erstelle {desc} für: {user_text}\n\n"
        + "Vorgaben:\n"
        + "- Das Rezept MUSS zum Nutzerprofil passen.\n"
        + "- Berücksichtige Ziel, Aktivitätslevel, Allergien und gesundheitliche Einschränkungen.\n"
        + "- Wenn eine Diagnose unklar ist oder du unsicher bist: vermeide riskante Zutaten und schlage eine sichere Alternative vor.\n"
        + (health_rules_text + "\n\n" if health_rules_text else "")
        + "- Antworte NUR mit folgendem Format:\n"
        + "Zutaten:\n"
        + "- ...\n\n"
        + "Zubereitung:\n"
        + "1. ...\n"
    )

    out = ask_ollama(prompt)

    # Auto-Repair, falls Output gegen Guardrails verstößt
    if guard["block_terms"] and violates_guardrails(out, guard):
        fix_prompt = (
            "Korrigiere das folgende Rezept so, dass es die Gesundheits-Regeln strikt einhält.\n"
            "Entferne/ersetze alle problematischen Zutaten.\n"
            "Gib wieder NUR dieses Format aus:\n"
            "Zutaten:\n- ...\n\nZubereitung:\n1. ...\n\n"
            + (health_rules_text + "\n\n" if health_rules_text else "")
            + out
        )
        out = ask_ollama(fix_prompt)

    return out


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
# Haupt-Logik: RAG + KI mit Ernährungsstilen + Guardrails
# ---------------------------------------------------------
def _generate_assistant_reply(user_text: str, profile: dict) -> str:
    raw_text = user_text.strip()
    if not raw_text:
        return "Wie kann ich dir helfen?"

    lower_text = raw_text.lower()

    # Debug-Modus
    if lower_text.startswith("debug"):
        return debug_request(raw_text)

    recipe_requested = is_recipe_request(raw_text)
    guard = build_health_guardrails(profile)

    # Nur bei Rezeptanfragen → RAG-Suche
    results = []
    if recipe_requested:
        try:
            from .wishboard_engine import search_index
            results = search_index(raw_text, top_k=3)
        except Exception:
            results = []

    # Wenn RAG etwas gefunden hat → nur nutzen, wenn thematisch + guardrail-sicher
    if recipe_requested and results:
        from .wishboard_engine import format_search_results

        recipe_raw = format_search_results(results).strip()

        # RAG: thematisch passend + kein Guardrail-Verstoß
        if recipe_raw and is_relevant_to_query(recipe_raw, raw_text) and not violates_guardrails(recipe_raw, guard):
            prompt = (
                "Formatiere dieses Rezept klar und übersichtlich. "
                "Gib NUR 'Zutaten:' und 'Zubereitung:' aus.\n\n"
                f"{recipe_raw}"
            )
            formatted = ask_ollama(prompt)

            # Auch das formatierte Ergebnis nochmal prüfen
            if guard["block_terms"] and violates_guardrails(formatted, guard):
                # Wenn es weiterhin verstößt: lieber neu generieren
                style = detect_recipe_style(raw_text)
                generated = generate_styled_recipe(raw_text, style, profile)
                return f"Ich habe ein passenderes Rezept für dein Profil erstellt:\n\n{generated}"

            return f"Hier ist ein Rezept aus meinen Quellen:\n\n{formatted}"

        # Falls unpassend (Thema oder Guardrails) → KI generiert sicher
        style = detect_recipe_style(raw_text)
        generated = generate_styled_recipe(raw_text, style, profile)
        return f"Hier ist ein gesundes Rezept für dich:\n\n{generated}"

    # Kein Treffer im Index → KI erzeugt Rezept
    if recipe_requested:
        style = detect_recipe_style(raw_text)
        generated = generate_styled_recipe(raw_text, style, profile)

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

    # Keine Essensanfrage → normale KI-Antwort
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

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["wishboard_chat"]:
            role = msg["role"]
            if role == "user":
                text = html.escape(msg["text"]).replace("\n", "<br>")
            else:
                text = msg["text"]  # Markdown für KI-Antworten erlauben

            bubble_class = "chat-bubble-user" if role == "user" else "chat-bubble-assistant"
            row_class = "chat-row chat-user" if role == "user" else "chat-row chat-assistant"

            st.markdown(
                f'<div class="{row_class}"><div class="{bubble_class}">{text}</div></div>',
                unsafe_allow_html=True
            )

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

    # später dynamisch (z.B. aus Session/User Login)
    profile = load_user_profile("Miray")

    reply = _generate_assistant_reply(text, profile)
    _add_assistant_message(reply)

    st.session_state["wishboard_input"] = ""


def app():
    render_wishboard_chat()


def render_wishboard_page():
    render_wishboard_chat()


if __name__ == "__main__":
    app()
