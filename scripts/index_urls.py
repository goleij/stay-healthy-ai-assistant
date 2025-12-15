# File: scripts/index_urls.py
"""
CLI: Indexiere URLs für das Wishboard.
Wenn keine Datei angegeben wird, wird automatisch wishboard/urls.txt verwendet.

Usage:
  python scripts/index_urls.py
  python scripts/index_urls.py --file myurls.txt
  python scripts/index_urls.py url1 url2 url3
  python scripts/index_urls.py --out custom.json
"""

import sys
from pathlib import Path
import argparse

# Projekt-Root bestimmen
proj_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(proj_root))

# Standard-URL-Datei im Wishboard-Modul
default_urls_file = proj_root / "wishboard" / "urls.txt"


def load_urls_from_file(path: Path):
    if not path.exists():
        print(f"URL-Datei nicht gefunden: {path}")
        sys.exit(1)

    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main():
    parser = argparse.ArgumentParser(description="Indexiere URLs für das Wishboard.")
    parser.add_argument("urls", nargs="*", help="Optionale URLs direkt aus der CLI")
    parser.add_argument("--file", "-f", help="Datei mit URLs (default: wishboard/urls.txt)")
    parser.add_argument("--out", "-o", help="Ausgabe-JSON (default: wishboard_index.json)")

    args = parser.parse_args()

    # ===============================
    #URLs laden (CLI, Datei, Default)
    # ===============================
    if args.urls:
        urls = args.urls

    else:
        file_path = Path(args.file) if args.file else default_urls_file

        print(f"Lade URLs aus Datei: {file_path}")
        urls = load_urls_from_file(file_path)

    if not urls:
        print("Keine URLs gefunden.")
        sys.exit(1)

    # ===============================
    # Wishboard Engine laden
    # ===============================
    try:
        from wishboard.wishboard_engine import index_urls, INDEX_FILE
    except Exception as e:
        print("Fehler beim Importieren von wishboard_engine:", e)
        sys.exit(1)

    out_path = Path(args.out) if args.out else Path(INDEX_FILE)

    # ===============================
    #Indexieren
    # ===============================
    print(f"Indexiere {len(urls)} URL(s) → {out_path}")

    try:
        index_urls(urls, index_path=out_path)
        print("Fertig.")
    except Exception as e:
        print("Fehler beim Indexieren:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
