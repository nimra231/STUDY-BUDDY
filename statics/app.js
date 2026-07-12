// ============================================================
// Study Buddy — frontend logic
// Talks to the Flask API (server.py) for everything real.
// ============================================================

const API = {
  status: () => fetch("/api/status").then(r => r.json()),
  upload: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch("/api/upload", { method: "POST", body: fd }).then(r => r.json());
  },
  sources: () => fetch("/api/sources").then(r => r.json()),
  ask: (question) => fetch("/api/ask", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  }).then(r => r.json()),
  generateQuiz: (source, num_questions) => fetch("/api/quiz/generate", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, num_questions }),
  }).then(r => r.json()),
  submitQuiz: (source, results) => fetch("/api/quiz/submit", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, results }),
  }).then(r => r.json()),
  progress: () => fetch("/api/progress").then(r => r.json()),
};

// ---------- Navigation ----------
function goTo(viewName) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById("view-" + viewName).classList.add("active");
  document.querySelector(`.nav-item[data-view="${viewName}"]`).classList.add("active");

  if (viewName === "dashboard") loadDashboard();
  if (viewName === "upload") loadSources();
  if (viewName === "quiz") loadQuizSetup();
  if (viewName === "progress") loadProgress();
}

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => goTo(item.dataset.view));
});

// ---------- API key banner ----------
API.status().then(s => {
  if (!s.api_key_configured) {
    document.getElementById("apiKeyBanner").style.display = "block";
  }
});

// ---------- Mastery ring helper ----------
function ringSVG(pct, size = 96, stroke = 8) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - pct);
  return `
    <div class="ring-wrap">
      <svg width="${size}" height="${size}">
        <circle class="ring-bg" cx="${size/2}" cy="${size/2}" r="${r}"/>
        <circle class="ring-fg" cx="${size/2}" cy="${size/2}" r="${r}"
                stroke-dasharray="${c}" stroke-dashoffset="${offset}"/>
      </svg>
      <div class="ring-label">${Math.round(pct * 100)}%</div>
    </div>`;
}

// ---------- Dashboard ----------
function loadDashboard() {
  API.progress().then(data => {
    const grid = document.getElementById("masteryGrid");
    if (!data.stats || data.stats.length === 0) {
      grid.innerHTML = `<div class="empty-state"><div class="icon">&#128218;</div><p>Upload a document and take a quiz to see your mastery here.</p></div>`;
      return;
    }
    grid.innerHTML = data.stats.map(s => `
      <div class="mastery-item">
        ${ringSVG(s.accuracy)}
        <div class="mastery-name" title="${s.source}">${s.source}</div>
      </div>
    `).join("");
  });
}

// ---------- Upload ----------
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleUpload(fileInput.files[0]);
});

function handleUpload(file) {
  const statusEl = document.getElementById("uploadStatus");
  statusEl.innerHTML = `<span class="spinner" style="border-top-color:var(--color-main); border-color:rgba(31,58,50,0.2);"></span> Processing ${file.name}...`;

  API.upload(file).then(res => {
    if (res.error) {
      statusEl.innerHTML = `<span style="color:var(--color-danger);">${res.error}</span>`;
      return;
    }
    statusEl.innerHTML = `<span style="color:var(--color-success);">Added ${res.filename} — ${res.chunks_added} sections indexed.</span>`;
    loadSources();
  });
}

function loadSources() {
  API.sources().then(res => {
    const el = document.getElementById("sourcesList");
    if (!res.sources || res.sources.length === 0) {
      el.innerHTML = `<span style="color:var(--color-text-soft); font-size:14px;">Nothing uploaded yet.</span>`;
      return;
    }
    el.innerHTML = res.sources.map(s => `<span class="source-chip">&#128196; ${s}</span>`).join("");
  });
}

// ---------- Ask ----------
const chatLog = document.getElementById("chatLog");
const askInput = document.getElementById("askInput");
const askBtn = document.getElementById("askBtn");

function sendQuestion() {
  const q = askInput.value.trim();
  if (!q) return;

  if (chatLog.querySelector(".empty-state")) chatLog.innerHTML = "";

  chatLog.innerHTML += `<div class="msg-question">${escapeHtml(q)}</div>`;
  const loadingId = "loading-" + Date.now();
  chatLog.innerHTML += `<div class="msg-answer-wrap" id="${loadingId}"><div class="msg-answer"><span class="spinner" style="border-top-color:var(--color-main); border-color:rgba(31,58,50,0.2);"></span> Thinking...</div></div>`;
  chatLog.scrollTop = chatLog.scrollHeight;
  askInput.value = "";
  askBtn.disabled = true;

  API.ask(q).then(res => {
    const node = document.getElementById(loadingId);
    const citations = (res.sources || []).map(s => `<div class="citation-card">&#128278; ${s}</div>`).join("");
    node.innerHTML = `
      <div class="msg-answer">${escapeHtml(res.answer).replace(/\n/g, "<br>")}</div>
      ${citations}
    `;
    chatLog.scrollTop = chatLog.scrollHeight;
    askBtn.disabled = false;
  });
}

askBtn.addEventListener("click", sendQuestion);
askInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendQuestion(); });

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------- Quiz ----------
let currentQuiz = null;
let currentAnswers = {};

function loadQuizSetup() {
  API.sources().then(res => {
    const select = document.getElementById("quizSourceSelect");
    if (!res.sources || res.sources.length === 0) {
      select.innerHTML = `<option>Upload a document first</option>`;
      return;
    }
    select.innerHTML = res.sources.map(s => `<option value="${s}">${s}</option>`).join("");
  });
  document.getElementById("quizArea").innerHTML = "";
}

document.getElementById("generateQuizBtn").addEventListener("click", () => {
  const source = document.getElementById("quizSourceSelect").value;
  const num = parseInt(document.getElementById("quizCountSelect").value, 10);
  const quizArea = document.getElementById("quizArea");

  quizArea.innerHTML = `<div class="card"><span class="spinner" style="border-top-color:var(--color-main); border-color:rgba(31,58,50,0.2);"></span> Writing your quiz...</div>`;

  API.generateQuiz(source, num).then(res => {
    if (res.error) {
      quizArea.innerHTML = `<div class="card" style="color:var(--color-danger);">${res.error}</div>`;
      return;
    }
    currentQuiz = res;
    currentAnswers = {};
    renderQuiz();
  });
});

function renderQuiz() {
  const quizArea = document.getElementById("quizArea");
  const letters = ["A", "B", "C", "D", "E"];

  const questionsHtml = currentQuiz.questions.map((q, qi) => `
    <div class="card quiz-question-card" data-qi="${qi}">
      <div class="quiz-question-text">${qi + 1}. ${escapeHtml(q.question)}</div>
      ${q.options.map((opt, oi) => `
        <div class="option-row" data-qi="${qi}" data-oi="${oi}" onclick="selectOption(${qi}, ${oi})">
          <div class="option-badge">${letters[oi]}</div>
          <div>${escapeHtml(opt)}</div>
        </div>
      `).join("")}
      <div class="explanation-box" id="explain-${qi}" style="display:none;"></div>
    </div>
  `).join("");

  quizArea.innerHTML = questionsHtml + `
    <button class="btn btn-accent" id="submitQuizBtn">Submit quiz</button>
    <div id="scoreArea"></div>
  `;

  document.getElementById("submitQuizBtn").addEventListener("click", submitQuiz);
}

function selectOption(qi, oi) {
  currentAnswers[qi] = oi;
  document.querySelectorAll(`.option-row[data-qi="${qi}"]`).forEach(el => {
    el.classList.toggle("selected", parseInt(el.dataset.oi, 10) === oi);
  });
}

function submitQuiz() {
  const letters = ["A", "B", "C", "D", "E"];
  let correctCount = 0;
  const results = [];

  currentQuiz.questions.forEach((q, qi) => {
    const userAnswer = currentAnswers[qi];
    const isCorrect = userAnswer === q.correct_index;
    if (isCorrect) correctCount++;
    results.push({ question: q.question, correct: isCorrect });

    document.querySelectorAll(`.option-row[data-qi="${qi}"]`).forEach(el => {
      const oi = parseInt(el.dataset.oi, 10);
      if (oi === q.correct_index) el.classList.add("correct");
      else if (oi === userAnswer) el.classList.add("incorrect");
      el.style.pointerEvents = "none";
    });

    const explainEl = document.getElementById(`explain-${qi}`);
    explainEl.style.display = "block";
    explainEl.textContent = q.explanation;
  });

  document.getElementById("submitQuizBtn").style.display = "none";
  document.getElementById("scoreArea").innerHTML = `
    <div class="score-banner">
      <div>Your score</div>
      <div class="score-num">${correctCount} / ${currentQuiz.questions.length}</div>
    </div>
  `;

  API.submitQuiz(currentQuiz.source, results);
}

// ---------- Progress ----------
function loadProgress() {
  API.progress().then(data => {
    const statsEl = document.getElementById("progressStats");
    const mistakesEl = document.getElementById("recentMistakes");

    if (!data.stats || data.stats.length === 0) {
      statsEl.innerHTML = `<div class="empty-state"><div class="icon">&#128202;</div><p>Take a quiz to start building your progress history.</p></div>`;
    } else {
      statsEl.innerHTML = data.stats.map(s => `
        <div class="stat-row">
          <div>
            <div class="stat-source">${s.source}</div>
            <div class="stat-meta">${s.correct}/${s.attempts} correct</div>
          </div>
          <div class="bar-track"><div class="bar-fill" style="width:${s.accuracy*100}%;"></div></div>
        </div>
      `).join("");
    }

    if (!data.recent_mistakes || data.recent_mistakes.length === 0) {
      mistakesEl.innerHTML = `<div class="empty-state"><p>No mistakes logged yet.</p></div>`;
    } else {
      mistakesEl.innerHTML = data.recent_mistakes.map(m => `
        <div class="mistake-item">
          ${escapeHtml(m.question)}
          <div class="mistake-source">${m.source}</div>
        </div>
      `).join("");
    }
  });
}

// ---------- Init ----------
loadDashboard();
