# storage/file_utils.py
import json
import os


def load_json(path: str) -> dict:
    """Load JSON file and return dict. Return {} if missing/invalid."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_json(path: str, data: dict):
    """Save dict as JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
