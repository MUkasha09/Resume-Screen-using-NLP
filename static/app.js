const state = {
  file: null,
  sessionId: null,
  chat: [],
};

const elements = Object.fromEntries([
  "resume-file", "drop-zone", "drop-title", "drop-meta", "analyze-button", "upload-status",
  "key-status", "matches-tab", "coach-tab", "matches-view", "coach-view",
  "match-list", "empty-state", "results-toolbar", "result-caption", "match-count",
  "breadcrumb-view", "view-title", "view-subtitle", "review-button", "review-prompt",
  "chat-log", "chat-form", "chat-input", "send-button", "toast",
].map((id) => [id, document.getElementById(id)]));

function setBusy(button, busy, label) {
  button.disabled = busy;
  button.dataset.originalLabel ??= button.innerHTML;
  button.innerHTML = busy ? `${label}<span class="button-spinner" aria-hidden="true">…</span>` : button.dataset.originalLabel;
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { elements.toast.hidden = true; }, 6000);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status}).`);
  return data;
}

function setFile(file) {
  if (!file) return;
  const allowed = /\.(pdf|docx|txt)$/i.test(file.name);
  if (!allowed) {
    showToast("Choose a PDF, DOCX, or TXT file.");
    return;
  }
  if (file.size > 12 * 1024 * 1024) {
    showToast("Keep the resume file under 12 MB.");
    return;
  }
  state.file = file;
  elements["drop-title"].textContent = file.name;
  elements["drop-meta"].textContent = `${(file.size / 1024).toFixed(0)} KB · ready to analyze`;
  elements["analyze-button"].disabled = false;
  elements["upload-status"].textContent = "Ready. Your file is processed in temporary memory.";
}

function appendMessage(role, content, extraClass = "") {
  const message = document.createElement("div");
  message.className = `chat-message ${role} ${extraClass}`.trim();
  message.textContent = content;
  elements["chat-log"].append(message);
  message.scrollIntoView({ block: "nearest", behavior: "smooth" });
  return message;
}

function addChatMessage(role, content) {
  state.chat.push({ role, content });
  appendMessage(role, content);
}

function renderMatches(data) {
  elements["empty-state"].hidden = true;
  elements["results-toolbar"].hidden = false;
  elements["match-count"].textContent = String(data.matches.length).padStart(2, "0");
  elements["result-caption"].textContent = `${data.word_count.toLocaleString()} words analyzed`;
  elements["match-list"].replaceChildren();

  data.matches.forEach((match, index) => {
    const card = document.createElement("article");
    card.className = "match-card";
    const rank = document.createElement("span");
    rank.className = `rank${index === 0 ? " rank-first" : ""}`;
    rank.textContent = String(index + 1).padStart(2, "0");
    const info = document.createElement("div");
    info.className = "match-info";
    const title = document.createElement("h3");
    title.className = "match-title";
    title.textContent = match.title;
    const description = document.createElement("p");
    description.className = "match-description";
    description.textContent = match.description;
    const skills = document.createElement("div");
    skills.className = "skill-list";
    if (match.skills.length) {
      match.skills.forEach((skill) => {
        const tag = document.createElement("span");
        tag.className = "skill-tag";
        tag.textContent = skill;
        skills.append(tag);
      });
    } else {
      const noSkills = document.createElement("span");
      noSkills.className = "no-skills";
      noSkills.textContent = "No direct skill overlap found";
      skills.append(noSkills);
    }
    info.append(title, description, skills);

    const score = document.createElement("div");
    score.className = "score";
    const value = document.createElement("span");
    value.className = "score-value";
    value.textContent = `${match.score}%`;
    const label = document.createElement("span");
    label.className = "score-label";
    label.textContent = "SIMILARITY";
    score.append(value, label);
    card.append(rank, info, score);
    elements["match-list"].append(card);
  });
}

function showView(view) {
  const isCoach = view === "coach";
  elements["matches-view"].hidden = isCoach;
  elements["coach-view"].hidden = !isCoach;
  elements["matches-tab"].classList.toggle("active", !isCoach);
  elements["coach-tab"].classList.toggle("active", isCoach);
  elements["matches-tab"].setAttribute("aria-selected", String(!isCoach));
  elements["coach-tab"].setAttribute("aria-selected", String(isCoach));
  elements["breadcrumb-view"].textContent = isCoach ? "CV COACH" : "MATCHES";
  elements["view-title"].textContent = isCoach ? "A sharper story starts here." : "Resume fit, made legible.";
  elements["view-subtitle"].textContent = isCoach ? "Grounded feedback, based on your CV and role matches." : "A clear starting point for your next move.";
}

async function analyzeResume() {
  if (!state.file) return;
  setBusy(elements["analyze-button"], true, "Reading your CV");
  elements["upload-status"].textContent = "Extracting text and comparing role descriptions…";
  try {
    const form = new FormData();
    form.append("file", state.file);
    const result = await apiRequest("/api/analyze", { method: "POST", body: form });
    state.sessionId = result.session_id;
    state.chat = [];
    elements["chat-log"].replaceChildren();
    elements["coach-tab"].disabled = false;
    elements["chat-input"].disabled = false;
    elements["send-button"].disabled = false;
    renderMatches(result);
    elements["upload-status"].textContent = "Analysis complete. Your session expires after 60 minutes.";
    elements["review-prompt"].hidden = false;
    showView("matches");
  } catch (error) {
    elements["upload-status"].textContent = "Analysis could not be completed.";
    showToast(error.message);
  } finally {
    setBusy(elements["analyze-button"], false);
    elements["analyze-button"].disabled = !state.file;
  }
}

async function requestReview() {
  if (!state.sessionId) return;
  const button = elements["review-button"];
  setBusy(button, true, "Reviewing CV");
  const loading = appendMessage("assistant", "Reading your CV and match results…", "loading");
  try {
    const result = await apiRequest("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
    loading.remove();
    addChatMessage("assistant", result.answer);
    elements["review-prompt"].hidden = true;
    elements["chat-input"].focus();
  } catch (error) {
    loading.remove();
    showToast(error.message);
  } finally {
    setBusy(button, false);
  }
}

async function sendChat(event) {
  event.preventDefault();
  const message = elements["chat-input"].value.trim();
  if (!message || !state.sessionId) return;
  elements["chat-input"].value = "";
  elements["send-button"].disabled = true;
  addChatMessage("user", message);
  const loading = appendMessage("assistant", "Thinking about your question…", "loading");
  try {
    const result = await apiRequest("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        message,
        history: state.chat.slice(0, -1),
      }),
    });
    loading.remove();
    addChatMessage("assistant", result.answer);
  } catch (error) {
    loading.remove();
    showToast(error.message);
  } finally {
    elements["send-button"].disabled = !state.sessionId;
    elements["chat-input"].focus();
  }
}

elements["resume-file"].addEventListener("change", (event) => setFile(event.target.files[0]));
elements["drop-zone"].addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    elements["resume-file"].click();
  }
});
elements["drop-zone"].addEventListener("dragover", (event) => {
  event.preventDefault();
  elements["drop-zone"].classList.add("dragging");
});
elements["drop-zone"].addEventListener("dragleave", () => elements["drop-zone"].classList.remove("dragging"));
elements["drop-zone"].addEventListener("drop", (event) => {
  event.preventDefault();
  elements["drop-zone"].classList.remove("dragging");
  setFile(event.dataTransfer.files[0]);
});
elements["analyze-button"].addEventListener("click", analyzeResume);
elements["matches-tab"].addEventListener("click", () => showView("matches"));
elements["coach-tab"].addEventListener("click", () => showView("coach"));
elements["review-button"].addEventListener("click", requestReview);
elements["chat-form"].addEventListener("submit", sendChat);
apiRequest("/api/health")
  .then((health) => {
    elements["key-status"].textContent = health.ai_configured
      ? "Groq AI is ready. Reviews and chats are available."
      : "Add a newly rotated GROQ_API_KEY to .env.local, then restart the app.";
  })
  .catch(() => showToast("Could not reach the app service. Refresh the page or restart the server."));