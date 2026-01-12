from llm_utils import get_llm

def generate_workout_steps(model_name: str, workout_text: str, profile: dict) -> list[str]:
    llm = get_llm(model_name)

    limitations = profile.get("limitations", [])
    health = profile.get("health_conditions", [])

    is_wheelchair = any("wheelchair" in str(x).lower() for x in limitations)

    prompt = f"""
You are a supportive fitness coach guiding a live workout (like a real trainer).

Turn the workout below into 6–10 short voice lines.

Rules:
- One short sentence per line
- Plain text only
- No numbering, no markdown
- Mix exercise instructions with motivation:
  - Include 2–3 motivational lines total (not more).
  - Put them between exercise lines, not all at the end.
  - Motivational lines must be short, like:
    "You can do this."
    "Great job, keep going."
    "Stay strong and breathe."
- Do NOT just read the workout text. Rephrase it like coaching someone live.
- Keep the tone friendly and energizing, but not cringe.

Safety:
- MUST respect these limitations: {limitations}
- MUST respect these health conditions: {health}
- Wheelchair user: {is_wheelchair}
- If Wheelchair user is true: EVERYTHING must be seated; never say stand, walk, squat, lunge, jump.

Workout text:
{workout_text}
"""


    chunks = []
    for c in llm.stream(prompt):
        chunks.append(c)
        if len("".join(chunks)) > 1500:
            break

    text = "".join(chunks).strip()
    steps = [line.strip() for line in text.split("\n") if len(line.strip()) > 3]
    return steps[:10]
