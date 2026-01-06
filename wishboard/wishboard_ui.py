# wishboard_ui.py (DE/EN/Both + Ernährungsstile + Health Guardrails pro User)
# OUTPUT-FIX: Keine Wiederholung "I want..." -> nur Recipe Title + Zutaten/Steps

from __future__ import annotations

import os
import html
import json
import re
from typing import Literal

import streamlit as st
from . import wishboard_css as css


LanguagePref = Literal["Auto", "Deutsch", "English", "Both (DE+EN)"]
LangCode = Literal["de", "en", "both"]


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
    out: list[str] = []
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

    out: list[str] = []
    for it in cond:
        for part in re.split(r"[,;/|]+", it):
            p = part.strip().lower()
            if p:
                out.append(p)
    return list(dict.fromkeys(out))


# ---------------------------------------------------------
# Language (UI Pref + Auto Detect)
# ---------------------------------------------------------
def _get_lang_pref() -> LanguagePref:
    return st.session_state.get("wishboard_lang", "Auto")


def _detect_lang_from_text(user_text: str) -> LangCode:
    pref = _get_lang_pref()
    if pref == "Deutsch":
        return "de"
    if pref == "English":
        return "en"
    if pref == "Both (DE+EN)":
        return "both"

    # Auto: einfache Heuristik
    t = f" {user_text.lower()} "
    umlauts = any(ch in user_text for ch in "äöüßÄÖÜ")

    de_hits = sum(
        w in t for w in [
            " ich ", " und ", " mit ", " ohne ", " bitte ", " rezept", " zutaten", " zubereitung",
            " frühstück", " mittagessen", " abendessen"
        ]
    )
    en_hits = sum(
        w in t for w in [
            " recipe", " ingredients", " instructions", " please ", " breakfast", " lunch", " dinner",
            " i want", " i would like", " make "
        ]
    )

    if umlauts or de_hits >= 2:
        return "de"
    if en_hits >= 2:
        return "en"
    return "de"


# ---------------------------------------------------------
# Health Rules (DE + EN) + Block Terms (DE + EN)
# ---------------------------------------------------------
HEALTH_RULES = {
    "diabetes": {
        "prompt_rules_de": [
            "KEIN zugesetzter Zucker (kein Honig, Ahornsirup, Agave, Sirup, Marmelade, gezuckerte Produkte).",
            "Wenn süß: nur Erythrit oder Stevia oder gar keine Süße.",
            "Bevorzuge ballaststoffreiche Zutaten, Low-GI/Low-GL.",
            "Ziel: <= 25g Kohlenhydrate pro Portion. Wenn nicht möglich, biete eine Alternative mit weniger Carbs an.",
        ],
        "prompt_rules_en": [
            "NO added sugar (no honey, maple syrup, agave, syrups, jam, sweetened products).",
            "If sweet: only erythritol or stevia, or no sweetener at all.",
            "Prefer high-fiber, low-GI/low-GL ingredients.",
            "Target: <= 25g carbs per serving. If not possible, offer a lower-carb alternative.",
        ],
        "block_terms": [
            # DE
            "zucker", "honig", "ahornsirup", "agave", "sirup", "marmelade", "gezuckert",
            "kondensmilch", "cola", "limonade",
            # EN
            "sugar", "honey", "maple syrup", "agave", "syrup", "jam", "sweetened",
            "condensed milk", "soda", "soft drink",
        ],
    },
    "prädiabetes": {
        "prompt_rules_de": [
            "KEIN zugesetzter Zucker (kein Honig, Ahornsirup, Agave, Sirup).",
            "Bevorzuge ballaststoffreiche Zutaten, Low-GI/Low-GL.",
            "Ziel: <= 30g Kohlenhydrate pro Portion.",
        ],
        "prompt_rules_en": [
            "NO added sugar (no honey, maple syrup, agave, syrups).",
            "Prefer high-fiber, low-GI/low-GL ingredients.",
            "Target: <= 30g carbs per serving.",
        ],
        "block_terms": [
            "zucker", "honig", "ahornsirup", "agave", "sirup", "marmelade", "gezuckert",
            "sugar", "honey", "maple syrup", "agave", "syrup", "jam", "sweetened",
        ],
    },

    "gluten": {
        "prompt_rules_de": [
            "100% glutenfrei. Keine Zutaten mit Weizen/Roggen/Gerste/Dinkel/Seitan.",
            "Nutze glutenfreie Alternativen (Reis, Mais, Buchweizen, Hirse, Kartoffeln, glutenfreie Haferflocken).",
        ],
        "prompt_rules_en": [
            "100% gluten-free. No wheat/rye/barley/spelt/seitan.",
            "Use gluten-free alternatives (rice, corn, buckwheat, millet, potatoes, gluten-free oats).",
        ],
        "block_terms": [
            "weizen", "roggen", "gerste", "dinkel", "seitan", "bulgur", "couscous", "panko", "paniermehl", "weizenmehl",
            "wheat", "rye", "barley", "spelt", "seitan", "bulgur", "couscous", "panko", "breadcrumbs", "wheat flour",
        ],
    },
    "zöliakie": {
        "prompt_rules_de": [
            "100% glutenfrei. Keine Zutaten mit Weizen/Roggen/Gerste/Dinkel/Seitan.",
        ],
        "prompt_rules_en": [
            "100% gluten-free. No wheat/rye/barley/spelt/seitan.",
        ],
        "block_terms": [
            "weizen", "roggen", "gerste", "dinkel", "seitan", "bulgur", "couscous", "panko", "paniermehl", "weizenmehl",
            "wheat", "rye", "barley", "spelt", "seitan", "bulgur", "couscous", "panko", "breadcrumbs", "wheat flour",
        ],
    },

    "reflux": {
        "prompt_rules_de": [
            "Magenfreundlich: vermeide sehr fettig, sehr scharf, viel Zitrus, sehr tomatenlastig, Minze und große Mengen Schokolade.",
        ],
        "prompt_rules_en": [
            "GERD-friendly: avoid very fatty foods, very spicy foods, lots of citrus, tomato-heavy dishes, mint, and large amounts of chocolate.",
        ],
        "block_terms": [
            "chili", "jalapeno", "sehr scharf", "scharf", "tomatensauce", "zitrone", "orange", "minze",
            "chili", "jalapeno", "very spicy", "spicy", "tomato sauce", "lemon", "orange", "mint",
        ],
    },
    "gerd": {
        "prompt_rules_de": [
            "Magenfreundlich: vermeide sehr fettig, sehr scharf, viel Zitrus, sehr tomatenlastig, Minze.",
        ],
        "prompt_rules_en": [
            "GERD-friendly: avoid very fatty foods, very spicy foods, lots of citrus, tomato-heavy dishes, mint.",
        ],
        "block_terms": [
            "chili", "jalapeno", "scharf", "tomatensauce", "zitrone", "orange", "minze",
            "chili", "jalapeno", "spicy", "tomato sauce", "lemon", "orange", "mint",
        ],
    },

    "bluthochdruck": {
        "prompt_rules_de": [
            "Salzarm kochen, vermeide stark verarbeitete Lebensmittel und sehr salzige Zutaten.",
            "Nutze Kräuter/Gewürze statt viel Salz.",
        ],
        "prompt_rules_en": [
            "Cook low-sodium; avoid highly processed foods and very salty ingredients.",
            "Use herbs/spices instead of lots of salt.",
        ],
        "block_terms": [
            "salami", "speck", "wurst", "chips", "salzstangen", "fertigsauce", "tütensuppe", "instant",
            "salami", "bacon", "sausage", "chips", "pretzel sticks", "ready-made sauce", "instant soup", "instant",
        ],
    },
    "hypertonie": {
        "prompt_rules_de": [
            "Salzarm kochen, vermeide stark verarbeitete Lebensmittel und sehr salzige Zutaten.",
        ],
        "prompt_rules_en": [
            "Cook low-sodium; avoid highly processed foods and very salty ingredients.",
        ],
        "block_terms": [
            "salami", "speck", "wurst", "chips", "salzstangen", "fertigsauce", "tütensuppe", "instant",
            "salami", "bacon", "sausage", "chips", "pretzel sticks", "ready-made sauce", "instant soup", "instant",
        ],
    },

    "laktose": {
        "prompt_rules_de": [
            "Laktosefrei: verwende laktosefreie Milchprodukte oder pflanzliche Alternativen.",
        ],
        "prompt_rules_en": [
            "Lactose-free: use lactose-free dairy or plant-based alternatives.",
        ],
        "block_terms": [
            "milch", "sahne", "joghurt", "quark", "käse", "butter",
            "milk", "cream", "yogurt", "quark", "cheese", "butter",
        ],
    },

    "nuss": {
        "prompt_rules_de": [
            "Nussfrei: keine Nüsse, kein Nussmus, keine Spuren-Zutaten wie Mandelmehl/Erdnussbutter.",
        ],
        "prompt_rules_en": [
            "Nut-free: no nuts, no nut butters, avoid almond flour/peanut butter and similar.",
        ],
        "block_terms": [
            "mandel", "haselnuss", "walnuss", "cashew", "erdnuss", "pistazie", "nuss", "nussmus", "erdnussbutter", "mandelmehl",
            "almond", "hazelnut", "walnut", "cashew", "peanut", "pistachio", "nut", "nut butter", "peanut butter", "almond flour",
        ],
    },
}


def build_health_guardrails(profile: dict) -> dict:
    allergies = _normalize_allergies(profile)
    conditions = _get_conditions(profile)
    merged = conditions + allergies

    prompt_rules_de: list[str] = []
    prompt_rules_en: list[str] = []
    block_terms: list[str] = []
    tags: list[str] = []

    for item in merged:
        for key, rule in HEALTH_RULES.items():
            if key in item:
                tags.append(key)
                prompt_rules_de.extend(rule.get("prompt_rules_de", []))
                prompt_rules_en.extend(rule.get("prompt_rules_en", []))
                block_terms.extend(rule.get("block_terms", []))

    return {
        "prompt_rules_de": list(dict.fromkeys(prompt_rules_de)),
        "prompt_rules_en": list(dict.fromkeys(prompt_rules_en)),
        "block_terms": list(dict.fromkeys(block_terms)),
        "tags": list(dict.fromkeys(tags)),
    }


def violates_guardrails(text: str, guardrails: dict) -> bool:
    t = (text or "").lower()
    return any(term.lower() in t for term in guardrails.get("block_terms", []))


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
        # DE
        "rezept", "koch", "koche", "kochen",
        "backe", "backen", "zubereitung", "zutaten",
        "gericht", "essen", "mahlzeit", "snack",
        "ich will", "ich möchte", "mach", "mache",
        "frühstück", "mittagessen", "abendessen",
        "snackidee", "snack ideen", "rezepte", "idee",

        # EN
        "recipe", "cook", "cooking", "bake", "baking",
        "ingredients", "instructions", "method", "directions",
        "meal", "snack", "i want", "i would like", "make me",

        # Misch/Beispiele
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
    if "glutenfrei" in t or "gluten-frei" in t or "ohne gluten" in t or "gluten free" in t:
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
# Profil-Kontext für KI-Prompts (sprachabhängig)
# ---------------------------------------------------------
def build_profile_context(profile: dict, lang: LangCode) -> str:
    if not profile:
        return ""

    health_conditions = profile.get("health_conditions") or []
    limitations = profile.get("limitations") or []
    health_issues = profile.get("health_issues") or ""

    cond_str = (
        ", ".join(health_conditions) if isinstance(health_conditions, list) and health_conditions
        else (str(health_conditions) if health_conditions else ("keine bekannt" if lang == "de" else "none known"))
    )
    lim_str = (
        ", ".join(limitations) if isinstance(limitations, list) and limitations
        else (str(limitations) if limitations else ("keine" if lang == "de" else "none"))
    )

    if lang == "en":
        return f"""
User profile:
- Age: {profile.get('age')}
- Gender: {profile.get('gender')}
- Goal: {profile.get('goal')}
- Activity level: {profile.get('activity')}
- Diet: {profile.get('diet')}
- Allergies: {profile.get('allergies')}

Health:
- Conditions / diagnoses: {cond_str}
- Health issues: {health_issues if health_issues else "none"}
- Limitations: {lim_str}
""".strip()

    return f"""
Nutzerprofil:
- Alter: {profile.get('age')}
- Geschlecht: {profile.get('gender')}
- Ziel: {profile.get('goal')}
- Aktivitätslevel: {profile.get('activity')}
- Ernährung: {profile.get('diet')}
- Allergien: {profile.get('allergies')}

Gesundheitliche Aspekte:
- Krankheiten / Diagnosen: {cond_str}
- Gesundheitliche Probleme: {health_issues if health_issues else "keine"}
- Einschränkungen: {lim_str}
""".strip()


# ---------------------------------------------------------
# RAG-Relevanzprüfung
# ---------------------------------------------------------
def is_relevant_to_query(recipe_text: str, user_query: str) -> bool:
    q = user_query.lower().strip()
    t = (recipe_text or "").lower()
    words = [w for w in q.split() if len(w) > 3]
    return any(w in t for w in words)


# ---------------------------------------------------------
# Anti-Echo: Request normalisieren (damit "I want..." nicht zurückkommt)
# ---------------------------------------------------------
def normalize_recipe_request(user_text: str) -> str:
    """
    Entfernt typische Einleitungen wie 'I want ...', 'Ich will ...', 'Please ...'.
    So spiegelt das Modell die Anfrage nicht als Satz zurück.
    """
    t = (user_text or "").strip()
    t = t.strip(' "\'')

    patterns = [
        # EN
        r"^\s*i\s*(want|would like|need)\s*(a|an|some)?\s*",
        r"^\s*can you\s*(please\s*)?(make|create|give)\s*(me\s*)?(a|an)?\s*",
        r"^\s*please\s*",
        r"^\s*make\s*(me\s*)?(a|an)?\s*",
        r"^\s*give\s*(me\s*)?(a|an)?\s*",
        # DE
        r"^\s*ich\s*(will|möchte|brauche)\s*(ein|eine|einen|etwas)?\s*",
        r"^\s*kannst\s*du\s*(bitte\s*)?(mir\s*)?(ein|eine|einen)?\s*",
        r"^\s*bitte\s*",
        r"^\s*mach\s*(mir\s*)?(ein|eine|einen)?\s*",
        r"^\s*gib\s*(mir\s*)?(ein|eine|einen)?\s*",
    ]
    for p in patterns:
        t = re.sub(p, "", t, flags=re.I)

    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) >= 3 else (user_text or "").strip()


def strip_non_recipe_preamble(text: str) -> str:
    """
    Entfernt Einleitungen wie 'Here is...' / 'Du willst...' am Anfang.
    Lässt Rezept-Format möglichst unangetastet.
    """
    if not text:
        return text
    out = text.strip()

    # Entferne typische Einleitungszeilen
    preambles = [
        r"^(you (asked|want|wanted).+?\n+)",
        r"^(i (will|want|would like).+?\n+)",
        r"^(here('s| is).+?\n+)",
        r"^(du (willst|möchtest|brauchst).+?\n+)",
        r"^(hier ist.+?\n+)",
    ]
    for p in preambles:
        out = re.sub(p, "", out, flags=re.I | re.S).strip()

    return out


def keep_only_title_and_body(text: str, lang: LangCode) -> str:
    """
    Erzwingt: Title + (Zutaten/Zubereitung) oder (Ingredients/Instructions).
    Falls das Modell mehr schreibt, wird alles außerhalb abgeschnitten.
    """
    if not text:
        return text

    t = text.strip()

    if lang == "en":
        # Keep from Title to end; otherwise from Ingredients
        m = re.search(r"(?im)^\s*title\s*:\s*.+$", t)
        if m:
            start = m.start()
            t = t[start:].strip()

        # If there's text before Title, already cut; now ensure we cut before Ingredients if Title is missing
        if not re.search(r"(?im)^\s*ingredients\s*:", t):
            # Not a valid recipe body, return as-is (better than deleting)
            return t

        # remove anything after instructions block if it adds tips etc.
        # (optional conservative: we keep all, but strip trailing "Notes:" blocks)
        t = re.split(r"(?im)^\s*(notes|tip|tips|nutrition|disclaimer)\s*:", t)[0].strip()
        return t

    # DE / both-DE segment: Zutaten/Zubereitung
    m = re.search(r"(?im)^\s*titel\s*:\s*.+$", t)
    if m:
        t = t[m.start():].strip()

    if not re.search(r"(?im)^\s*zutaten\s*:", t):
        return t

    t = re.split(r"(?im)^\s*(hinweis|tipps|tipp|nährwerte|haftung)\s*:", t)[0].strip()
    return t


# ---------------------------------------------------------
# KI: Gesundes Rezept im gewünschten Stil erzeugen (mit Guardrails + Auto-Repair)
# Format: Title + Ingredients/Instructions (oder DE)
# ---------------------------------------------------------
def generate_styled_recipe(user_text: str, style: str, profile: dict, lang: LangCode) -> str:
    style_de = {
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
    style_en = {
        "lowcarb": "a healthy low-carb recipe (few carbs)",
        "highprotein": "a healthy high-protein recipe (high protein, balanced)",
        "vegan": "a healthy vegan recipe (no animal products, whole foods)",
        "zuckerfrei": "a healthy sugar-free recipe (no added sugar)",
        "lowfat": "a healthy low-fat recipe (light, low fat)",
        "glutenfrei": "a healthy gluten-free recipe (gluten-free alternatives)",
        "paleo": "a healthy paleo recipe (unprocessed, no grains, no sugar)",
        "keto": "a healthy keto recipe (very low carb, healthy fats)",
        "healthy": "a healthy balanced recipe (natural ingredients)",
    }

    guard = build_health_guardrails(profile)

    # Health rules in Prompt (sprachabhängig)
    health_rules_text = ""
    if lang == "en":
        rules = guard.get("prompt_rules_en", [])
        if rules:
            health_rules_text = "Health rules (must follow strictly):\n" + "\n".join(f"- {r}" for r in rules)
    else:
        rules = guard.get("prompt_rules_de", [])
        if rules:
            health_rules_text = "Gesundheits-Regeln (strikt einhalten):\n" + "\n".join(f"- {r}" for r in rules)

    clean_request = normalize_recipe_request(user_text)

    if lang == "both":
        # 2-pass: stabil (DE + EN getrennt)
        de = generate_styled_recipe(user_text, style, profile, "de")
        en = generate_styled_recipe(user_text, style, profile, "en")
        return f"**DE**\n\n{de}\n\n---\n\n**EN**\n\n{en}"

    if lang == "en":
        profile_context = build_profile_context(profile, "en")
        desc = style_en.get(style, style_en["healthy"])

        prompt = (
            (profile_context + "\n\n" if profile_context else "")
            + "You are a health-focused nutrition coach.\n"
            + f"Create {desc} based on this request: {clean_request}\n\n"
            + "Requirements:\n"
            + "- The recipe MUST fit the user profile.\n"
            + "- Consider goal, activity level, allergies, and medical constraints.\n"
            + "- If a diagnosis is unclear or you're unsure: avoid risky ingredients and suggest a safer alternative.\n"
            + "- DO NOT repeat or quote the user's request.\n"
            + "- DO NOT start with phrases like 'I want', 'You asked for', or 'Here is'.\n"
            + (health_rules_text + "\n\n" if health_rules_text else "")
            + "Reply ONLY in this format (no extra text):\n"
            + "Title: <short recipe name>\n\n"
            + "Ingredients:\n"
            + "- ...\n\n"
            + "Instructions:\n"
            + "1. ...\n"
        )

        out = ask_ollama(prompt)
        out = strip_non_recipe_preamble(out)
        out = keep_only_title_and_body(out, "en")

        # Auto-Repair
        if guard["block_terms"] and violates_guardrails(out, guard):
            fix_prompt = (
                "Fix the following recipe so it strictly follows the health rules.\n"
                "Remove/replace any problematic ingredients.\n"
                "Return ONLY this format (no extra text):\n"
                "Title: <short recipe name>\n\n"
                "Ingredients:\n- ...\n\n"
                "Instructions:\n1. ...\n\n"
                + (health_rules_text + "\n\n" if health_rules_text else "")
                + out
            )
            out = ask_ollama(fix_prompt)
            out = strip_non_recipe_preamble(out)
            out = keep_only_title_and_body(out, "en")

        return out

    # de
    profile_context = build_profile_context(profile, "de")
    desc = style_de.get(style, style_de["healthy"])

    prompt = (
        (profile_context + "\n\n" if profile_context else "")
        + "Du bist ein gesunder Ernährungscoach.\n"
        + f"Erstelle {desc} basierend auf dieser Anfrage: {clean_request}\n\n"
        + "Vorgaben:\n"
        + "- Das Rezept MUSS zum Nutzerprofil passen.\n"
        + "- Berücksichtige Ziel, Aktivitätslevel, Allergien und gesundheitliche Einschränkungen.\n"
        + "- Wenn eine Diagnose unklar ist oder du unsicher bist: vermeide riskante Zutaten und schlage eine sichere Alternative vor.\n"
        + "- Wiederhole die Nutzeranfrage NICHT und zitiere sie nicht.\n"
        + "- Beginne NICHT mit Formulierungen wie 'Ich will', 'Du willst', 'Hier ist'.\n"
        + (health_rules_text + "\n\n" if health_rules_text else "")
        + "Antworte NUR in diesem Format (kein Extra-Text):\n"
        + "Titel: <kurzer Rezeptname>\n\n"
        + "Zutaten:\n"
        + "- ...\n\n"
        + "Zubereitung:\n"
        + "1. ...\n"
    )

    out = ask_ollama(prompt)
    out = strip_non_recipe_preamble(out)
    out = keep_only_title_and_body(out, "de")

    # Auto-Repair
    if guard["block_terms"] and violates_guardrails(out, guard):
        fix_prompt = (
            "Korrigiere das folgende Rezept so, dass es die Gesundheits-Regeln strikt einhält.\n"
            "Entferne/ersetze alle problematischen Zutaten.\n"
            "Gib NUR dieses Format aus (kein Extra-Text):\n"
            "Titel: <kurzer Rezeptname>\n\n"
            "Zutaten:\n- ...\n\n"
            "Zubereitung:\n1. ...\n\n"
            + (health_rules_text + "\n\n" if health_rules_text else "")
            + out
        )
        out = ask_ollama(fix_prompt)
        out = strip_non_recipe_preamble(out)
        out = keep_only_title_and_body(out, "de")

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
    if "wishboard_lang" not in st.session_state:
        st.session_state["wishboard_lang"] = "Auto"


def _add_user_message(text: str):
    st.session_state["wishboard_chat"].append({"role": "user", "text": text})


def _add_assistant_message(text: str):
    st.session_state["wishboard_chat"].append({"role": "assistant", "text": text})


# ---------------------------------------------------------
# Haupt-Logik: RAG + KI mit Ernährungsstilen + Guardrails
# OUTPUT-FIX: Bei Rezepten nur Rezept (Title+Body), keine Einleitungstexte
# ---------------------------------------------------------
def _generate_assistant_reply(user_text: str, profile: dict) -> str:
    raw_text = user_text.strip()
    if not raw_text:
        return "Wie kann ich dir helfen?"

    lower_text = raw_text.lower()

    # Sprache bestimmen (Auto/DE/EN/Both)
    lang = _detect_lang_from_text(raw_text)

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
        try:
            from .wishboard_engine import format_search_results
            recipe_raw = format_search_results(results).strip()
        except Exception:
            recipe_raw = ""

        # RAG: thematisch passend + kein Guardrail-Verstoß
        if recipe_raw and is_relevant_to_query(recipe_raw, raw_text) and not violates_guardrails(recipe_raw, guard):
            if lang == "en":
                prompt = (
                    "Rewrite and format this recipe clearly.\n"
                    "Output ONLY this format (no extra text):\n"
                    "Title: <short recipe name>\n\n"
                    "Ingredients:\n- ...\n\n"
                    "Instructions:\n1. ...\n\n"
                    "If the source is in German, translate it to English.\n"
                    "Do NOT repeat or quote the user's request.\n"
                    "Do NOT start with 'Here is' or 'I want'.\n\n"
                    f"{recipe_raw}"
                )
                formatted = ask_ollama(prompt)
                formatted = strip_non_recipe_preamble(formatted)
                formatted = keep_only_title_and_body(formatted, "en")

                if guard["block_terms"] and violates_guardrails(formatted, guard):
                    style = detect_recipe_style(raw_text)
                    return generate_styled_recipe(raw_text, style, profile, lang)

                return formatted

            if lang == "both":
                prompt_de = (
                    "Formatiere dieses Rezept klar und übersichtlich.\n"
                    "Gib NUR dieses Format aus (kein Extra-Text):\n"
                    "Titel: <kurzer Rezeptname>\n\n"
                    "Zutaten:\n- ...\n\n"
                    "Zubereitung:\n1. ...\n\n"
                    "Wiederhole die Nutzeranfrage nicht.\n"
                    "Beginne nicht mit 'Hier ist' oder 'Ich will'.\n\n"
                    f"{recipe_raw}"
                )
                de = ask_ollama(prompt_de)
                de = strip_non_recipe_preamble(de)
                de = keep_only_title_and_body(de, "de")

                prompt_en = (
                    "Rewrite and format this recipe clearly.\n"
                    "Output ONLY this format (no extra text):\n"
                    "Title: <short recipe name>\n\n"
                    "Ingredients:\n- ...\n\n"
                    "Instructions:\n1. ...\n\n"
                    "If the source is in German, translate it to English.\n"
                    "Do NOT repeat or quote the user's request.\n"
                    "Do NOT start with 'Here is' or 'I want'.\n\n"
                    f"{recipe_raw}"
                )
                en = ask_ollama(prompt_en)
                en = strip_non_recipe_preamble(en)
                en = keep_only_title_and_body(en, "en")

                combined = f"**DE**\n\n{de}\n\n---\n\n**EN**\n\n{en}"
                if guard["block_terms"] and violates_guardrails(combined, guard):
                    style = detect_recipe_style(raw_text)
                    return generate_styled_recipe(raw_text, style, profile, lang)

                return combined

            # DE (default)
            prompt = (
                "Formatiere dieses Rezept klar und übersichtlich.\n"
                "Gib NUR dieses Format aus (kein Extra-Text):\n"
                "Titel: <kurzer Rezeptname>\n\n"
                "Zutaten:\n- ...\n\n"
                "Zubereitung:\n1. ...\n\n"
                "Wiederhole die Nutzeranfrage nicht.\n"
                "Beginne nicht mit 'Hier ist' oder 'Ich will'.\n\n"
                f"{recipe_raw}"
            )
            formatted = ask_ollama(prompt)
            formatted = strip_non_recipe_preamble(formatted)
            formatted = keep_only_title_and_body(formatted, "de")

            if guard["block_terms"] and violates_guardrails(formatted, guard):
                style = detect_recipe_style(raw_text)
                return generate_styled_recipe(raw_text, style, profile, lang)

            return formatted

        # Falls unpassend oder Guardrail-Risiko → KI generiert sicher
        style = detect_recipe_style(raw_text)
        return generate_styled_recipe(raw_text, style, profile, lang)

    # Kein Treffer im Index → KI erzeugt Rezept
    if recipe_requested:
        style = detect_recipe_style(raw_text)
        return generate_styled_recipe(raw_text, style, profile, lang)

    # Keine Essensanfrage → normale KI-Antwort
    if lang == "en":
        normal_prompt = (
            "You are a helpful, friendly AI assistant. "
            "Answer clearly and concisely in English.\n\n"
            f"User: {raw_text}\n\n"
            "Answer:"
        )
        return ask_ollama(normal_prompt)

    if lang == "both":
        normal_prompt = (
            "You are a helpful assistant. Reply in BOTH languages.\n"
            "First German (DE), then English (EN). Keep it concise.\n\n"
            f"User: {raw_text}\n\n"
            "DE:\nEN:"
        )
        return ask_ollama(normal_prompt)

    normal_prompt = (
        "Du bist ein hilfreicher, freundlicher KI-Assistent. "
        "Antworte klar und knapp auf Deutsch.\n\n"
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
        """
        <div class="wishboard-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60"
                 viewBox="0 0 24 24" fill="none" stroke="#009245"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="8" width="18" height="4" rx="1"/>
                <path d="M12 8v13"/>
                <path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/>
                <path d="M7.5 8a2.5 2.5 0 0 1 0-5A4.8 8 0 0 1 12 8a4.8 8 0 0 1 4.5-5 2.5 2.5 0 0 1 0 5"/>
            </svg>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Language selector (keeps state)
    st.selectbox(
        "Language / Sprache",
        ["Auto", "Deutsch", "English", "Both (DE+EN)"],
        key="wishboard_lang"
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
            "Write your wish.",
            key="wishboard_input",
            placeholder="e.g. 'I want chips' / z.B. 'Ich will Chips'",
        )
    with cols[1]:
        st.button("Send", key="wishboard_send", on_click=_on_send_click)


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
