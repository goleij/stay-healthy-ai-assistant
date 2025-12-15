# python
# File: scripts/index_pdfs.py
"""
CLI: Indexiere alle PDFs in einem Ordner (oder angegebene Dateien).
Usage:
  python scripts/index_pdfs.py /path/to/pdf_folder [--out path/to/index.json] [--chunk 3000]
  python scripts/index_pdfs.py file1.pdf file2.pdf --out path/to/index.json
"""
import sys
from pathlib import Path
import argparse
import json
import os


try:
    from PyPDF2 import PdfReader  # ältere/pip-name: PyPDF2
except Exception:
    try:
        from pypdf import PdfReader  # neuer Paketname: pypdf
    except Exception:
        print("Missing dependency: install with: python -m pip install PyPDF2")
        raise SystemExit(1)


def extract_text_from_pdf(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
        return "\n".join(texts)
    except Exception as e:
        print(f"Fehler beim Lesen {path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int):
    text = " ".join(text.split())
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size].strip()
        if chunk:
            yield chunk, (i // chunk_size) + 1

def main():
    parser = argparse.ArgumentParser(description="Indexiere PDFs für wishboard")
    parser.add_argument("paths", nargs="+", help="Ordner mit PDFs oder einzelne PDF-Dateien")
    parser.add_argument("--out", "-o", help="Ausgabe‑JSON (default: wishboard/wishboard_pdf_index.json)")
    parser.add_argument("--chunk", "-c", type=int, default=3000, help="Chunk-Größe (default 3000 Zeichen)")
    args = parser.parse_args()

    proj_root = Path(__file__).resolve().parents[1]
    default_out = proj_root / "wishboard" / "wishboard_pdf_index.json"
    out_path = Path(args.out) if args.out else default_out

    entries = []
    pdf_paths = []
    for p in args.paths:
        pth = Path(p)
        if pth.is_dir():
            pdf_paths.extend(sorted(pth.glob("*.pdf")))
        else:
            pdf_paths.append(pth)

    if not pdf_paths:
        print("Keine PDFs gefunden.")
        sys.exit(1)

    for pdf in pdf_paths:
        if not pdf.exists():
            print("Datei nicht gefunden:", pdf)
            continue
        txt = extract_text_from_pdf(pdf)
        if not txt.strip():
            print("Keine Textinhalte in:", pdf)
            continue
        for chunk, page in chunk_text(txt, args.chunk):
            entries.append({"source": str(pdf), "page": page, "text": chunk})

    out_dir = out_path.parent
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Index geschrieben: {out_path} ({len(entries)} Einträge)")

if __name__ == "__main__":
    main()
