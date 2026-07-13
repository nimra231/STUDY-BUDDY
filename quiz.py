"""
quiz.py
-------
Generates multiple-choice quiz questions from your uploaded material, so you
can test yourself instead of just re-reading notes (which feels productive
but usually isn't - actually recalling information is what makes it stick).
"""

import json
import re
import google.generativeai as genai
from ingest import load_index

QUIZ_MODEL = "models/gemini-flash-latest"

def get_text_for_source(source_name: str) -> str:
    """Pulls all chunk text belonging to one uploaded document, stitched back together."""
    _, chunks = load_index()
    matching = [c["text"] for c in chunks if c["source"] == source_name]
    return "\n\n".join(matching)


DIFFICULTY_GUIDANCE = {
    "Beginner": "Focus on basic definitions and recall. Keep wording simple.",
    "Intermediate": "Mix recall with questions that require connecting two ideas together.",
    "Exam-level": "Write questions at the difficulty of a real university exam - include at least one question that requires applying a concept to a new scenario, not just repeating a definition.",
}


def generate_quiz(source_name: str, num_questions: int = 5, difficulty: str = "Intermediate") -> list[dict]:
    """
    Asks Gemini to write num_questions multiple-choice questions based on one
    document, at the requested difficulty level. Returns a list of dicts:
    {"question": ..., "options": [...], "correct_index": int, "explanation": ...}
    """
    content = get_text_for_source(source_name)
    if not content.strip():
        return []

    difficulty_note = DIFFICULTY_GUIDANCE.get(difficulty, DIFFICULTY_GUIDANCE["Intermediate"])

    prompt = f"""Based on the study material below, write exactly {num_questions}
multiple-choice quiz questions to test understanding.

Difficulty level: {difficulty}. {difficulty_note}

Respond with ONLY valid JSON, no other text, no markdown code fences, in this
exact structure:

[
  {{
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "correct_index": 0,
    "explanation": "one sentence on why this is correct"
  }}
]

STUDY MATERIAL:
{content[:6000]}
"""

    model = genai.GenerativeModel(QUIZ_MODEL)
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Gemini sometimes wraps JSON in ```json fences despite instructions - strip them if present.
    raw = re.sub(r"^```json\s*|\s*```$", "", raw.strip())

    try:
        questions = json.loads(raw)
        return questions
    except json.JSONDecodeError:
        # If parsing fails, return an empty list rather than crashing the app.
        return []
