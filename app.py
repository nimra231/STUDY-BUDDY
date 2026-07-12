"""
app.py
------
The Streamlit interface: a sidebar-navigated app with a Dashboard, Study,
Quiz, and Progress page - styled to match the Nimra Iftikhar portfolio
identity kit (Space Grotesk headings, Inter body, deep green + burnt orange).

Run with:  streamlit run app.py
"""

import os
import tempfile
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

import ingest
import qa
import quiz as quiz_module
import tracker

load_dotenv()

st.set_page_config(page_title="Study Buddy", page_icon="📘", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# THEME - matches the identity kit: Space Grotesk / Inter, deep green + burnt orange
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --main: #1F3A32;
        --main-light: #2C5347;
        --accent: #C1531F;
        --text: #151512;
        --bg: #EDE6D6;
        --card: #FFFFFF;
        --muted: #6B6558;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text) !important; }

    .stApp { background-color: var(--bg); }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--main) 0%, var(--main-light) 100%);
    }
    section[data-testid="stSidebar"] * { color: #F0EBDD !important; }
    section[data-testid="stSidebar"] h1 { color: #FFFFFF !important; }

    .stButton>button {
        background-color: var(--main); color: white; border-radius: 10px;
        border: none; padding: 0.55rem 1.3rem; font-weight: 600; font-family: 'Inter', sans-serif;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover { background-color: var(--accent); color: white; }

    .card {
        background: var(--card); border-radius: 18px; padding: 26px 28px;
        box-shadow: 0 10px 26px rgba(31,58,50,0.08); margin-bottom: 22px;
    }

    .metric-card {
        background: var(--card); border-radius: 16px; padding: 20px 24px;
        box-shadow: 0 8px 20px rgba(31,58,50,0.08); text-align:left;
    }
    .metric-value { font-family:'Space Grotesk',sans-serif; font-size:34px; font-weight:700; color:var(--main); }
    .metric-label { font-size:13px; color:var(--muted); letter-spacing:1px; text-transform:uppercase; font-weight:600; }

    .pill {
        display:inline-block; background: var(--main); color:white !important; font-size:12px;
        padding:4px 12px; border-radius:100px; margin:2px 4px 2px 0; font-weight:500;
    }
    .pill-accent { background: var(--accent); }

    .citation-box {
        background:#F5F0E4; border-left: 4px solid var(--accent); padding:10px 16px;
        border-radius:8px; font-size:13px; color:var(--muted); margin-top:10px;
    }

    .weak-row {
        background: var(--card); border-left: 5px solid var(--accent); padding:14px 18px;
        border-radius:10px; margin-bottom:10px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    .strong-row {
        background: var(--card); border-left: 5px solid var(--main); padding:14px 18px;
        border-radius:10px; margin-bottom:10px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }

    div[data-testid="stFileUploader"] { background:var(--card); border-radius:14px; padding:10px; }
</style>
""", unsafe_allow_html=True)


def init_gemini():
    """Sets up the Gemini API key from .env, or asks for it in the sidebar if missing."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        key = st.session_state.get("api_key", "")
    if key:
        genai.configure(api_key=key)
        return True
    return False


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("# 📘 Study Buddy")
    st.caption("Your notes. Your questions. Your progress.")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "📥 Study", "📝 Quiz Me", "📊 Progress"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if not os.getenv("GEMINI_API_KEY"):
        st.text_input("Gemini API key", type="password", key="api_key",
                       help="Free key at aistudio.google.com/app/apikey")

ready = init_gemini()
if not ready:
    st.warning("Add your Gemini API key in the sidebar to get started.")
    st.stop()

sources = ingest.list_sources()
stats = tracker.get_stats_by_source()

# ---------------------------------------------------------------------------
# PAGE: DASHBOARD
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard":
    st.title("Dashboard")
    st.caption("Where things stand right now.")

    total_attempts = sum(s["attempts"] for s in stats)
    total_correct = sum(s["correct"] for s in stats)
    overall_acc = round(total_correct / total_attempts * 100) if total_attempts else 0
    weakest = stats[0]["source"] if stats else "—"

    c1, c2, c3, c4 = st.columns(4)
    for col, value, label in zip(
        [c1, c2, c3, c4],
        [len(sources), total_attempts, f"{overall_acc}%", weakest],
        ["Documents Uploaded", "Quiz Questions Attempted", "Overall Accuracy", "Needs Review"],
    ):
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    colA, colB = st.columns([3, 2])

    with colA:
        st.markdown("#### Your material")
        if sources:
            st.markdown('<div class="card">' + "".join(f'<span class="pill">{s}</span>' for s in sources) + '</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card">No documents yet — head to the <b>Study</b> page to upload your first one.</div>', unsafe_allow_html=True)

    with colB:
        st.markdown("#### Quick actions")
        st.markdown('<div class="card">Go to <b>Study</b> to upload notes or ask a question.<br><br>Go to <b>Quiz Me</b> to test yourself on anything you\'ve uploaded.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: STUDY
# ---------------------------------------------------------------------------
elif page == "📥 Study":
    st.title("Study")
    st.caption("Upload your notes, then ask anything about them.")

    st.markdown("#### Add material")
    uploaded_file = st.file_uploader(
        "Upload PDF, Word, PowerPoint, or plain text",
        type=["pdf", "docx", "pptx", "txt"],
    )
    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        if st.button("Process this document"):
            with st.spinner(f"Reading and indexing {uploaded_file.name}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                count = ingest.process_document(tmp_path, uploaded_file.name, file_type)
                os.unlink(tmp_path)
            st.success(f"Added {uploaded_file.name} — {count} sections indexed.")
            st.rerun()

    if sources:
        st.markdown('<div class="card"><b>Uploaded so far:</b><br>' +
                     "".join(f'<span class="pill">{s}</span>' for s in sources) +
                     '</div>', unsafe_allow_html=True)

    st.markdown("#### Ask a question")
    question = st.text_input("Ask anything about your uploaded notes", label_visibility="collapsed",
                              placeholder="e.g. What's the difference between supervised and unsupervised learning?")

    if question:
        if not sources:
            st.info("Upload a document first — there's nothing to search yet.")
        else:
            with st.spinner("Searching your notes..."):
                result = qa.answer_question(question)
            st.markdown(f'<div class="card">{result["answer"]}</div>', unsafe_allow_html=True)
            if result["sources"]:
                st.markdown('<div class="citation-box">📎 <b>Sources:</b> ' +
                             " · ".join(result["sources"]) + '</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: QUIZ ME
# ---------------------------------------------------------------------------
elif page == "📝 Quiz Me":
    st.title("Quiz Me")
    st.caption("Active recall beats re-reading. Test yourself.")

    if not sources:
        st.info("Upload a document on the Study page before generating a quiz.")
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            chosen_source = st.selectbox("Quiz me on", sources)
        with c2:
            difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Exam-level"], index=1)
        with c3:
            num_q = st.slider("Questions", 3, 10, 5)

        if st.button("Generate quiz"):
            with st.spinner("Writing your quiz..."):
                st.session_state["quiz"] = quiz_module.generate_quiz(chosen_source, num_q, difficulty)
                st.session_state["quiz_source"] = chosen_source
                st.session_state["quiz_answers"] = {}
                st.session_state["quiz_submitted"] = False

        if st.session_state.get("quiz"):
            quiz_data = st.session_state["quiz"]
            st.write("")
            for i, q in enumerate(quiz_data):
                st.markdown(f'<div class="card"><b>Q{i+1}. {q["question"]}</b></div>', unsafe_allow_html=True)
                choice = st.radio("Choose one:", q["options"], key=f"q_{i}", index=None, label_visibility="collapsed")
                if choice is not None:
                    st.session_state["quiz_answers"][i] = q["options"].index(choice)

            if st.button("Submit quiz"):
                st.session_state["quiz_submitted"] = True

            if st.session_state.get("quiz_submitted"):
                correct_count = 0
                st.write("")
                st.markdown("#### Results")
                for i, q in enumerate(quiz_data):
                    user_answer = st.session_state["quiz_answers"].get(i)
                    is_correct = user_answer == q["correct_index"]
                    correct_count += int(is_correct)
                    tracker.record_result(st.session_state["quiz_source"], q["question"], is_correct)

                    if is_correct:
                        st.success(f"Q{i+1}: Correct — {q['explanation']}")
                    else:
                        correct_option = q["options"][q["correct_index"]]
                        st.error(f"Q{i+1}: Not quite. Correct answer: **{correct_option}** — {q['explanation']}")

                pct = int(correct_count / len(quiz_data) * 100)
                st.markdown(f"""<div class="metric-card" style="margin-top:16px;">
                    <div class="metric-value">{correct_count}/{len(quiz_data)} ({pct}%)</div>
                    <div class="metric-label">Your Score</div>
                </div>""", unsafe_allow_html=True)
                st.session_state["quiz"] = None

# ---------------------------------------------------------------------------
# PAGE: PROGRESS
# ---------------------------------------------------------------------------
elif page == "📊 Progress":
    st.title("Progress")
    st.caption("What you actually know vs. what needs another pass.")

    if not stats:
        st.info("Take a quiz first — this fills in once you have real results.")
    else:
        for s in stats:
            pct = int(s["accuracy"] * 100)
            css_class = "weak-row" if s["accuracy"] < 0.7 else "strong-row"
            st.markdown(f"""
            <div class="{css_class}">
                <b>{s['source']}</b> — {pct}% correct ({s['correct']}/{s['attempts']} attempts)
            </div>
            """, unsafe_allow_html=True)

        weakest = stats[0]
        if weakest["accuracy"] < 0.7:
            st.warning(f"Your weakest area right now: **{weakest['source']}** ({int(weakest['accuracy']*100)}%). Worth another quiz round.")

        st.write("")
        st.markdown("#### Recent mistakes")
        mistakes = tracker.get_recent_mistakes(limit=8)
        if mistakes:
            for m in mistakes:
                st.markdown(f'<div class="card" style="padding:12px 20px;"><i>{m["question"]}</i><br><span style="color:var(--muted); font-size:13px;">{m["source"]}</span></div>', unsafe_allow_html=True)
        else:
            st.caption("No mistakes logged yet — or you're getting everything right.")
