"""
qa.py
-----
Answers a question using only the content you've uploaded (this is called
"RAG" - Retrieval-Augmented Generation). Instead of letting the model answer
from its general training, we:
1. Find the chunks of YOUR notes most relevant to the question.
2. Hand those chunks to Gemini and say "answer using only this."
This keeps answers grounded in your actual material, not generic textbook
knowledge that might not match how your professor taught it.
"""

import numpy as np
import google.generativeai as genai
from ingest import load_index, EMBED_MODEL

ANSWER_MODEL = "models/gemini-1.5-flash"
TOP_K = 4  # how many chunks to retrieve per question


def embed_query(query: str) -> np.ndarray:
    """Turns the question itself into an embedding, using the same model as the documents."""
    result = genai.embed_content(model=EMBED_MODEL, content=query, task_type="retrieval_query")
    return np.array([result["embedding"]], dtype="float32")


def retrieve_relevant_chunks(query: str, k: int = TOP_K):
    """Finds the k chunks whose meaning is closest to the question."""
    index, chunks = load_index()
    if index is None or len(chunks) == 0:
        return []

    query_vector = embed_query(query)
    k = min(k, len(chunks))
    distances, indices = index.search(query_vector, k)
    return [chunks[i] for i in indices[0]]


def answer_question(query: str) -> dict:
    """
    Full RAG pipeline: retrieve relevant chunks, then ask Gemini to answer
    using only those chunks. Returns the answer text plus which sources were used,
    so you can double-check it against your actual notes.
    """
    relevant = retrieve_relevant_chunks(query)

    if not relevant:
        return {
            "answer": "I don't have any study material uploaded yet - upload a PDF first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(
        f"[From: {c['source']}, p.{c.get('page', '?')}]\n{c['text']}" for c in relevant
    )

    prompt = f"""You are a study assistant helping a student review their own lecture notes.

Answer the question using ONLY the context below. If the context doesn't contain
the answer, say so honestly instead of making something up - the student needs to
know if this wasn't covered in their notes, not get a confident wrong answer.

Keep the answer clear and exam-focused, not overly long.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""

    model = genai.GenerativeModel(ANSWER_MODEL)
    response = model.generate_content(prompt)

    sources_used = sorted(set(f"{c['source']}, p.{c.get('page', '?')}" for c in relevant))
    return {"answer": response.text.strip(), "sources": sources_used}
