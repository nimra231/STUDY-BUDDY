"""
tracker.py
----------
Keeps a small local database of how you've done on quizzes, per document,
so the app can tell you "you keep getting X wrong" instead of forgetting
everything the moment you close the browser tab.

Uses SQLite - a simple, file-based database that needs no separate server,
perfect for a single-user local tool like this.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "progress.db")


def _get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            question TEXT NOT NULL,
            correct INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    return conn


def record_result(source: str, question: str, was_correct: bool):
    """Saves one quiz answer's result."""
    conn = _get_connection()
    conn.execute(
        "INSERT INTO quiz_results (source, question, correct, timestamp) VALUES (?, ?, ?, ?)",
        (source, question, int(was_correct), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_stats_by_source() -> list[dict]:
    """
    Returns accuracy per document, sorted weakest first, e.g.:
    [{"source": "Chapter3.pdf", "attempts": 12, "correct": 5, "accuracy": 0.42}, ...]
    This is what powers the "what to review next" view.
    """
    conn = _get_connection()
    rows = conn.execute("""
        SELECT source,
               COUNT(*) as attempts,
               SUM(correct) as correct
        FROM quiz_results
        GROUP BY source
    """).fetchall()
    conn.close()

    stats = []
    for source, attempts, correct in rows:
        correct = correct or 0
        stats.append({
            "source": source,
            "attempts": attempts,
            "correct": correct,
            "accuracy": round(correct / attempts, 2) if attempts else 0,
        })
    stats.sort(key=lambda s: s["accuracy"])
    return stats


def get_recent_mistakes(source: str = None, limit: int = 10) -> list[dict]:
    """Returns the most recent wrong answers, optionally filtered to one document."""
    conn = _get_connection()
    if source:
        rows = conn.execute(
            "SELECT source, question, timestamp FROM quiz_results WHERE correct=0 AND source=? ORDER BY id DESC LIMIT ?",
            (source, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT source, question, timestamp FROM quiz_results WHERE correct=0 ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [{"source": r[0], "question": r[1], "timestamp": r[2]} for r in rows]
