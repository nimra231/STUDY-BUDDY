"""
server.py
---------
Flask backend for Study Buddy. Serves the frontend and exposes the API
endpoints the UI calls: upload a PDF, ask a question, generate a quiz,
grade a quiz, and fetch progress stats.

This reuses ingest.py / qa.py / quiz.py / tracker.py unchanged - the same
logic that powered the earlier Streamlit version, just called from routes
instead of a Streamlit script.

Run with: python server.py
"""

import os
import tempfile
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

import ingest
import qa
import quiz as quiz_module
import tracker

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def require_api_key():
    """Every route that calls Gemini checks this first and returns a clear error if missing."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return False
    genai.configure(api_key=key)
    return True


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def status():
    """Lets the frontend show a clear banner if no API key is configured yet."""
    return jsonify({"api_key_configured": bool(os.getenv("GEMINI_API_KEY"))})


@app.route("/api/upload", methods=["POST"])
def upload():
    if not require_api_key():
        return jsonify({"error": "No Gemini API key configured on the server (.env)."}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    f = request.files["file"]
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported right now."}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        count = ingest.process_pdf(tmp_path, f.filename)
    finally:
        os.unlink(tmp_path)

    return jsonify({"filename": f.filename, "chunks_added": count, "sources": ingest.list_sources()})


@app.route("/api/sources")
def sources():
    return jsonify({"sources": ingest.list_sources()})


@app.route("/api/ask", methods=["POST"])
def ask():
    if not require_api_key():
        return jsonify({"error": "No Gemini API key configured on the server (.env)."}), 400

    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Question is empty."}), 400

    result = qa.answer_question(question)
    return jsonify(result)


@app.route("/api/quiz/generate", methods=["POST"])
def generate_quiz():
    if not require_api_key():
        return jsonify({"error": "No Gemini API key configured on the server (.env)."}), 400

    data = request.get_json()
    source = (data or {}).get("source")
    num_questions = int((data or {}).get("num_questions", 5))

    if not source:
        return jsonify({"error": "No source document specified."}), 400

    questions = quiz_module.generate_quiz(source, num_questions)
    if not questions:
        return jsonify({"error": "Couldn't generate a quiz from that document. Try re-uploading it."}), 500

    return jsonify({"source": source, "questions": questions})


@app.route("/api/quiz/submit", methods=["POST"])
def submit_quiz():
    data = request.get_json()
    source = (data or {}).get("source")
    results = (data or {}).get("results", [])  # [{"question": ..., "correct": bool}, ...]

    if not source or not results:
        return jsonify({"error": "Missing quiz results."}), 400

    for r in results:
        tracker.record_result(source, r["question"], r["correct"])

    return jsonify({"stats": tracker.get_stats_by_source()})


@app.route("/api/progress")
def progress():
    return jsonify({
        "stats": tracker.get_stats_by_source(),
        "recent_mistakes": tracker.get_recent_mistakes(limit=10),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
