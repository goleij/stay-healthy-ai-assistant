# audio/recipe_llm.py
from llm_utils import get_llm

def generate_recipe_steps(model_name: str, meal_item: str) -> list[str]:
    """
    Generate short cooking steps for a meal.
    This version is SAFE and NEVER blocks Streamlit.
    """

    llm = get_llm(model_name)

    prompt = f"""
You are a helpful cooking assistant.

Give a simple recipe for the following dish.

Rules:
- 5 to 7 steps
- one short sentence per step
- plain text only
- no numbering, no markdown

Dish:
{meal_item}
"""

    chunks = []

    for chunk in llm.stream(prompt):
        chunks.append(chunk)

        # 🔴 HARD STOP – prevents infinite streaming
        if len("".join(chunks)) > 1200:
            break

    text = "".join(chunks).strip()

    if not text:
        return []

    steps = [
        line.strip()
        for line in text.split("\n")
        if len(line.strip()) > 3
    ]

    return steps[:7]
