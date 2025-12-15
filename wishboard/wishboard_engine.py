# wishboard_engine.py

# Aufgaben dieser Datei:
# Laden & Speichern von Suchindizes (URLs + PDFs)
# Vorverarbeitung von Texten (Tokenisierung, Reinigung)
# Heuristische Suche nach relevanten Dokumenten
# Erkennung & Extraktion von Rezept-Strukturen

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

import requests
import collections

# BASE_DIR:
# Verzeichnis, in dem sich diese Datei befindet
BASE_DIR = Path(__file__).resolve().parent

# Haupt-Index-Dateien
INDEX_FILE = BASE_DIR / "wishboard_index.json"
# Separater Index für PDF-Dokumente
PDF_INDEX_FILE = BASE_DIR / "wishboard_pdf_index.json"


# ---------------------------------------------------------
# Stopwörter (für Suchanfragen)
# Wörter, die für die Suche keine Bedeutung haben,
# werden aus der Anfrage entfernt.
# um Relevanz der Treffer zu verbessern
# ---------------------------------------------------------
STOPWORDS_DE = {
    "ich", "du", "er", "sie", "es", "wir", "ihr", "sie",
    "will", "möchte", "haben", "bitte", "brauche",
    "ein", "eine", "einen", "einem", "einer",
    "der", "die", "das", "den", "dem",
    "und", "oder", "aber", "mit", "ohne", "für", "von", "aus",
    "gesund", "gesunde", "gesunder", "gesundes",
    "rezept", "rezepte", "snack", "snacks"
}


# ---------------------------------------------------------
# Hilfsfunktionen für Index laden/speichern

# ---------------------------------------------------------
def _load_index_file(path: Path) -> List[Dict]:
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []

# Speichert einen Index (Liste von Dokumenten) als JSON.
def _save_index_file(path: Path, data: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# Tokenisierung der Suchanfrage
# Zerlegt eine Nutzeranfrage in sinnvolle Suchbegriffe.
# ABLAUF:
# 1. Alles in Kleinbuchstaben
# 2. Nur Wortzeichen extrahieren
# 3. Stopwörter entfernen
# TECHNIK:
# - Regex
# ---------------------------------------------------------
def _tokenize_query(text: str) -> List[str]:
    return [
        t for t in re.findall(r"\w+", text.lower())
        if len(t) > 2 and t not in STOPWORDS_DE
    ]


# ---------------------------------------------------------
# HTML-Extraktion -> # Wandelt HTML-Seiten in reinen Text um.
# TECHNIK:
# - BeautifulSoup (Fallback: Regex)
# ---------------------------------------------------------
def _extract_text_from_html(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n")
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------
# Rezept-Struktur erkennen (Zutaten/Zubereitung)
# TECHNIK:
# - Regex
# - Heuristiken
# - Imperativ-Erkennung
# ---------------------------------------------------------
def extract_recipe_from_text(text: str, max_chars: int = 800) -> Optional[Dict[str, str]]:
    """
    Verbesserter Parser, der auch Rezepte erkennt, wenn:
    - keine Überschriften 'Zutaten' oder 'Zubereitung' existieren
    - Zutaten im Fließtext stehen
    - mehrere Rezepte auf einer Seite stehen

    Nutzt Muster-Erkennung (Heuristik) für Zutaten + Schritte.
    """

    if not text:
        return None

    # Grundreinigung
    text = clean_recipe_text(text)
    txt = text.replace("\r", "\n")

    # Versuch: klassische Suche (Zutaten / Zubereitung Header)
    ingr_re = re.compile(
        r'(zutaten?)[:\s\-–—]*\n(?P<body>.+?)(?=\n\s*(zubereitung|anleitung|schritte)\b)',
        re.I | re.S
    )
    steps_re = re.compile(
        r'(zubereitung|anleitung|schritte)[:\s\-–—]*\n(?P<body>.+)',
        re.I | re.S
    )

    m_ingr = ingr_re.search(txt)
    m_steps = steps_re.search(txt)

    ingredients = m_ingr.group("body").strip() if m_ingr else ""
    steps = m_steps.group("body").strip() if m_steps else ""

    # Wenn klassisch erkannt → gut!
    if ingredients or steps:
        return {
            "ingredients": ingredients[:max_chars],
            "steps": steps[:max_chars]
        }

    # Kein klassisches Rezept gefunden → automatische Erkennung
    # Zutaten-Muster: Mengenangaben ("g", "ml", "EL", "TL") + Worte
    ingredient_lines = []
    for line in txt.split("\n"):
        if re.search(r'\b(\d+|\d+\.\d+)\s*(g|ml|kg|l|el|tl|stück|stck|bananen|eier)\b', line.lower()):
            ingredient_lines.append(line.strip())

    # Schritte-Muster: Verben am Satzanfang (imperativ)
    step_lines = []
    for line in txt.split("\n"):
        if re.match(r'^(schneide|mixe|rühre|vermische|koche|backe|gib|füge|püriere|erhitze|serviere|lasse|lege|hacke|schmelze)\b', line.lower()):
            step_lines.append(line.strip())

    # Keine Zutaten oder Schritte → Kein Rezept erkennbar
    if not ingredient_lines and not step_lines:
        return None

    return {
        "ingredients": "\n".join(ingredient_lines)[:max_chars],
        "steps": "\n".join(step_lines)[:max_chars]
    }




# ---------------------------------------------------------
# Quelle kürzen
# ---------------------------------------------------------
def short_source(url: Optional[str]) -> str:
    try:
        if not url:
            return "unbekannte Quelle"
        p = urlparse(url)
        netloc = p.netloc
        return netloc
    except:
        return url or "unbekannte Quelle"


# ---------------------------------------------------------
# Formatierung der Suchergebnisse
# ---------------------------------------------------------
def format_search_results(results: List[Dict]) -> str:
    """
    Gibt NUR das Rezept zurück:
    - Zutaten
    - Zubereitung
    Keine Snippets, keine Webseiten-Texte, keine Metadaten.
    """
    if not results:
        return ""

    # wir nehmen nur das beste Rezept (Erster Treffer)
    r = results[0]
    text = r.get("text", "")

    recipe = extract_recipe_from_text(text)

    if recipe and (recipe.get("ingredients") or recipe.get("steps")):
        ingredients = recipe.get("ingredients", "").strip()
        steps = recipe.get("steps", "").strip()

        final = ""

        if ingredients:
            final += f"**Zutaten:**\n{ingredients}\n\n"
        if steps:
            final += f"**Zubereitung:**\n{steps}"

        return final.strip()

    # Wenn KEIN Rezept extrahiert werden konnte
    return "Für diese Anfrage konnte kein vollständiges Rezept gefunden werden."



# ---------------------------------------------------------
# URL indexieren
#Lädt Webseiten herunter und speichert deren Text im Index.
# ---------------------------------------------------------
def index_urls(urls: List[str], index_path: Path = INDEX_FILE) -> None:
    index = _load_index_file(index_path)
    next_id = max((doc.get("id", 0) for doc in index), default=0) + 1

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    }

    for url in urls:
        try:
            resp = requests.get(url, timeout=15, headers=headers)
            resp.raise_for_status()
            text = _extract_text_from_html(resp.text)
            if not text.strip():
                continue

            index.append({
                "id": next_id,
                "source": url,
                "page": 1,
                "text": text,
            })
            next_id += 1

        except Exception as e:
            print(f"Fehler beim Abrufen von {url}: {e}")

    _save_index_file(index_path, index)

def clean_recipe_text(text: str) -> str:
    """
    Entfernt irrelevante Inhalte wie:
    - Einkaufsliste-Buttons
    - Zeitangaben
    - Portionen
    - Icons / Sonderzeichen
    - Mengentabellen
    - SEO-Kästen
    """
    # Entferne bullet-icons, Kästchen, Symbole
    text = re.sub(r"[▢•●■□▶►✓✔✘✖🟦🟩🟧🟥🟨]", " ", text)

    # Entferne doppelte Leerzeilen
    text = re.sub(r"\n{2,}", "\n", text)

    # Entferne Minuten / Zeiten / Backzeit / Gesamtzeit / Portionen-Blöcke
    text = re.sub(r"\b\d+\s*Minuten?\b", "", text, flags=re.I)
    text = re.sub(r"\bBackzeit.*\n", "", text, flags=re.I)
    text = re.sub(r"\bGesamtzeit.*\n", "", text, flags=re.I)
    text = re.sub(r"\bPortionen?.*\n", "", text, flags=re.I)

    # Entferne "Auf die Einkaufsliste" oder Buttons
    text = re.sub(r"Auf die.*?\n", "", text, flags=re.I)
    text = re.sub(r"Einkaufsliste.*?\n", "", text, flags=re.I)

    # Entferne sehr lange numerische Blöcke, die Tabellen darstellen
    text = re.sub(r"\b\d+\b", "", text)

    # Entferne überflüssige Bindestriche
    text = re.sub(r"[-–—]+", " ", text)

    # Entferne überflüssige Leerzeichen
    text = re.sub(r"[ ]{2,}", " ", text)

    # Entferne leere Zeilen erneut
    text = re.sub(r"\n\s*\n", "\n", text)

    return text.strip()

# ---------------------------------------------------------
# Suche verbessern (Rezepte werden bevorzugt)
# ---------------------------------------------------------
def search_index(query: str, top_k: int = 3) -> List[Dict]:
    docs = _load_index_file(INDEX_FILE) + _load_index_file(PDF_INDEX_FILE)
    if not docs:
        return []

    q_tokens = _tokenize_query(query)
    if not q_tokens:
        return []

    main_token = q_tokens[0]

    scored = []
    for doc in docs:
        text = doc.get("text", "")
        text_low = text.lower()

        hits = sum(text_low.count(t) for t in q_tokens)
        if hits == 0:
            continue

        recipe_bonus = 2 if any(k in text_low for k in ["zutaten", "zubereitung"]) else 0

        score = hits * 3 + recipe_bonus

        pos = text_low.find(main_token)
        if pos == -1:
            snippet = text[:300]
        else:
            start = max(0, pos - 150)
            end = min(len(text), pos + 300)
            snippet = text[start:end]

        scored.append({
            "source": doc.get("source"),
            "text": text,
            "snippet": snippet.strip(),
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
