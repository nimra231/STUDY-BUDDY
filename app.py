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
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --main: #1F3A32;
        --main-light: #2C5347;
        --accent: #C1531F;
        --accent-glow: #E8935F;
        --text: #151512;
        --bg: #EDE6D6;
        --card: #FFFFFF;
        --muted: #6B6558;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text) !important; }

    /* ---- animated gradient mesh background ---- */
    .stApp {
        background:
            radial-gradient(circle at 15% 20%, rgba(31,58,50,0.16) 0%, transparent 45%),
            radial-gradient(circle at 85% 15%, rgba(193,83,31,0.14) 0%, transparent 40%),
            radial-gradient(circle at 50% 90%, rgba(31,58,50,0.10) 0%, transparent 50%),
            var(--bg);
        background-size: 200% 200%;
        animation: meshMove 18s ease-in-out infinite;
    }
    @keyframes meshMove {
        0%   { background-position: 0% 0%, 100% 0%, 50% 100%; }
        50%  { background-position: 30% 30%, 70% 20%, 40% 80%; }
        100% { background-position: 0% 0%, 100% 0%, 50% 100%; }
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--main) 0%, var(--main-light) 100%);
        box-shadow: 4px 0 24px rgba(0,0,0,0.15);
    }
    section[data-testid="stSidebar"] * { color: #F0EBDD !important; }
    section[data-testid="stSidebar"] h1 { color: #FFFFFF !important; }

    .stButton>button {
        background: linear-gradient(135deg, var(--main) 0%, var(--main-light) 100%);
        color: white; border-radius: 12px;
        border: none; padding: 0.6rem 1.4rem; font-weight: 600; font-family: 'Inter', sans-serif;
        box-shadow: 0 4px 14px rgba(31,58,50,0.25);
        transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-glow) 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(193,83,31,0.35);
    }
    .stButton>button:active { transform: translateY(0px) scale(0.98); }

    /* ---- glassmorphism cards ---- */
    .card {
        background: rgba(255,255,255,0.72);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.5);
        border-radius: 20px; padding: 28px 30px;
        box-shadow: 0 12px 32px rgba(31,58,50,0.10);
        margin-bottom: 22px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 18px 40px rgba(31,58,50,0.16);
    }

    .metric-card {
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.5);
        border-radius: 18px; padding: 22px 24px;
        box-shadow: 0 10px 26px rgba(31,58,50,0.10); text-align:left;
        position: relative; overflow: hidden;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .metric-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, var(--main), var(--accent));
    }
    .metric-card:hover {
        transform: translateY(-5px) scale(1.015);
        box-shadow: 0 16px 34px rgba(31,58,50,0.18);
    }
    .metric-value {
        font-family:'Space Grotesk',sans-serif; font-size:36px; font-weight:700;
        background: linear-gradient(135deg, var(--main), var(--main-light));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .metric-label { font-size:12.5px; color:var(--muted); letter-spacing:1.2px; text-transform:uppercase; font-weight:600; }

    .pill {
        display:inline-block;
        background: linear-gradient(135deg, var(--main), var(--main-light));
        color:white !important; font-size:12px;
        padding:5px 14px; border-radius:100px; margin:3px 6px 3px 0; font-weight:500;
        box-shadow: 0 3px 10px rgba(31,58,50,0.25);
    }
    .pill-accent { background: linear-gradient(135deg, var(--accent), var(--accent-glow)); }

    .citation-box {
        background: rgba(245,240,228,0.85);
        backdrop-filter: blur(8px);
        border-left: 4px solid var(--accent); padding:12px 18px;
        border-radius:10px; font-size:13px; color:var(--muted); margin-top:10px;
    }

    .weak-row {
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(10px);
        border-left: 5px solid var(--accent); padding:14px 18px;
        border-radius:12px; margin-bottom:10px; box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        transition: transform 0.2s ease;
    }
    .weak-row:hover { transform: translateX(4px); }
    .strong-row {
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(10px);
        border-left: 5px solid var(--main); padding:14px 18px;
        border-radius:12px; margin-bottom:10px; box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        transition: transform 0.2s ease;
    }
    .strong-row:hover { transform: translateX(4px); }

    div[data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.65); backdrop-filter: blur(10px);
        border-radius:16px; padding:12px; border: 1.5px dashed rgba(31,58,50,0.25);
    }

    /* ---- hero banner with floating 3D logo ---- */
    .hero-wrap {
        display:flex; align-items:center; gap:22px;
        padding: 26px 32px; border-radius: 22px; margin-bottom: 28px;
        background: linear-gradient(135deg, rgba(31,58,50,0.92) 0%, rgba(44,83,71,0.92) 100%);
        box-shadow: 0 16px 40px rgba(31,58,50,0.28);
        position: relative; overflow: hidden;
    }
    .hero-wrap::after {
        content:''; position:absolute; top:-40%; right:-10%; width:220px; height:220px;
        background: radial-gradient(circle, rgba(193,83,31,0.35) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-logo {
        width: 64px; height: 64px; border-radius: 18px; flex-shrink: 0;
        background: linear-gradient(145deg, var(--accent), var(--accent-glow));
        display:flex; align-items:center; justify-content:center;
        font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:26px; color:white;
        box-shadow:
            0 10px 20px rgba(193,83,31,0.4),
            inset 0 2px 4px rgba(255,255,255,0.3),
            inset 0 -3px 6px rgba(0,0,0,0.2);
        transform: perspective(400px) rotateY(-8deg) rotateX(4deg);
        animation: floatY 4s ease-in-out infinite;
    }
    @keyframes floatY {
        0%, 100% { transform: perspective(400px) rotateY(-8deg) rotateX(4deg) translateY(0px); }
        50% { transform: perspective(400px) rotateY(8deg) rotateX(-2deg) translateY(-6px); }
    }
    .hero-title { color:#FFFFFF; font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:26px; margin:0; position:relative; z-index:2; }
    .hero-sub { color:#C9D6CE; font-size:14px; margin-top:4px; position:relative; z-index:2; }
</style>
""", unsafe_allow_html=True)


def hero_banner(title: str, subtitle: str):
    """A glassy gradient hero banner with a floating 3D-tilted logo mark."""
    st.markdown(f"""
    <div class="hero-wrap">
        <div class="hero-logo">NI</div>
        <div>
            <p class="hero-title">{title}</p>
            <p class="hero-sub">{subtitle}</p>
        </div>
    </div>
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
    hero_banner("Dashboard", "Where things stand right now.")

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
    hero_banner("Study", "Upload your notes, then ask anything about them.")

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
    hero_banner("Quiz Me", "Active recall beats re-reading. Test yourself.")

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
    hero_banner("Progress", "What you actually know vs. what needs another pass.")

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
