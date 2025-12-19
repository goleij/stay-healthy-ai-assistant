# audio/recipe_parser.py
import re

def split_meals(day_body: str) -> dict[str, str]:
    """
    Teilt den Tages-Text in einzelne Meals auf:
    Breakfast, Lunch, Dinner, Snacks
    """
    meals = {}
    current_meal = None
    buffer = []

    for line in day_body.splitlines():
        line_stripped = line.strip()

        # Meal-Überschriften erkennen
        if line_stripped.startswith("### "):
            if current_meal and buffer:
                meals[current_meal] = "\n".join(buffer).strip()
                buffer = []

            current_meal = line_stripped.replace("### ", "")
            continue

        if current_meal:
            buffer.append(line)

    if current_meal and buffer:
        meals[current_meal] = "\n".join(buffer).strip()

    return meals


def extract_meal_item(meal_block: str) -> str | None:
    """
    Extrahiert den Namen des Gerichts aus einem Meal-Block.
    """
    if not meal_block:
        return None

    for line in meal_block.splitlines():
        line = line.strip()

        # Bullet-Zeichen entfernen
        line = line.lstrip("•- ").strip()

        # Macros-Zeile ignorieren
        if line.lower().startswith("macros"):
            continue

        # Kalorien entfernen
        line = re.sub(r"\(.*?kcal.*?\)", "", line, flags=re.IGNORECASE).strip()

        if len(line.split()) >= 2:
            return line

    return None
