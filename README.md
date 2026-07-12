# Study Buddy — Full-Stack Web App

An AI study assistant that answers questions from *your own* uploaded notes
(not generic internet knowledge), auto-generates quizzes to test yourself,
and tracks your real progress over time. Built with a Flask backend and a
custom-designed frontend (no template kit) matching my portfolio identity.

## What's actually working right now

- **Upload** PDF lecture notes/slides — text is extracted, chunked, embedded,
  and indexed locally with FAISS.
- **Ask** questions in a chat-style interface — answers are generated using
  only your uploaded material (RAG), with a citation card showing which
  document the answer came from.
- **Quiz Me** — auto-generates multiple-choice quizzes from a chosen document,
  grades them instantly, and shows an explanation per question.
- **Progress dashboard** — circular mastery rings per document, accuracy bars,
  and a running list of your most recent mistakes, all persisted in a local
  SQLite database across sessions.

## What's on the roadmap, not built (being honest about scope)

This started from a much bigger spec — accounts/login, DOCX/PPTX/TXT support,
page-number citations, flashcards, PDF export, dark mode, and long-term
conversational memory. Building all of that properly is realistically weeks
of work, not a single project sprint. What's here is the **real, working
core** of that vision: upload → ask with citations → quiz → track progress.
The rest is documented here as genuine next steps, not silently skipped:

- User accounts / login (currently single-user, local only)
- DOCX, PPTX, TXT upload (PDF only for now)
- Page-number-level citations (currently cites the document, not the page)
- Flashcards and exam-note PDF export
- Conversational memory across separate sessions (chat history is per-session only)
- Dark mode

## Tech stack, and why

- **Flask** (Python backend) — same language as the ML/data-processing code,
  no need to juggle two ecosystems, and it's a stack I already know from
  OfficeBridge Pro.
- **Gemini API** (`gemini-1.5-flash` + `text-embedding-004`) — free tier,
  no cost to run.
- **FAISS** — fast local vector search, no external database needed.
- **SQLite** — lightweight, file-based, appropriate for a single-user tool.
- **Custom HTML/CSS/JS frontend** — no UI framework/template; built to match
  my own portfolio identity kit (Space Grotesk + Inter, deep green + burnt
  clay palette) so it looks like one coherent piece of work, not a generic
  Bootstrap dashboard.

## Setup

1. **Get a free Gemini API key**: https://aistudio.google.com/app/apikey

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API key**:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and paste your real key in place of `your_key_here`.

4. **Run it**:
   ```bash
   python server.py
   ```
   Open `http://localhost:5000` in your browser.

## Project structure

```
study_buddy_web/
├── server.py           # Flask app: routes + API endpoints
├── ingest.py            # PDF -> chunks -> embeddings -> FAISS index
├── qa.py                 # RAG: retrieval + Gemini answer generation
├── quiz.py               # Auto quiz generation from notes
├── tracker.py            # SQLite progress tracking
├── templates/
│   └── index.html        # App structure (dashboard, upload, ask, quiz, progress)
├── static/
│   ├── styles.css        # Full custom design system
│   └── app.js             # Frontend logic, API calls, rendering
├── requirements.txt
├── .env.example
└── data/                  # Created automatically: FAISS index, chunks, progress.db
```

## How the core pipeline works (for interviews / explaining this)

1. A PDF is uploaded → `ingest.py` extracts text, splits it into overlapping
   chunks (so no idea gets cut in half at a boundary), and calls Gemini's
   embedding model on each chunk — turning text into a list of numbers that
   captures its meaning.
2. Those vectors go into a FAISS index — a fast structure for "find the
   chunks most similar in meaning to X."
3. When you ask a question, it's embedded the same way, FAISS finds the
   closest chunks from your notes, and those chunks (not the whole
   document) are handed to Gemini with an instruction: answer using only
   this context, and say so honestly if the answer isn't in here.
4. Quiz generation works the same way — it pulls all chunks for one
   document and asks Gemini to write questions from that specific content.
5. Every quiz answer is logged to SQLite (`tracker.py`), which is what
   powers the mastery rings and accuracy bars on the dashboard.

## Known limitations (worth saying upfront, not overclaiming)

- PDF text extraction won't work well on scanned/image-only PDFs (no OCR).
- Quiz quality depends on how much real text was in the source document.
- Single-user, local-only — not deployed, no authentication.
- Correct answers are sent to the frontend before grading (fine for a
  personal local tool; a production version would hide `correct_index`
  server-side until submission).
