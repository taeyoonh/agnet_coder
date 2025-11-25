const state = {
  sessionId: null,
  history: [],
};

const historyEl = document.getElementById("history");
const statusEl = document.getElementById("status");
const formEl = document.getElementById("prompt-form");
const promptEl = document.getElementById("prompt");

bootstrap();
renderHistory();

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = promptEl.value.trim();
  if (!value || !state.sessionId) return;
  toggleForm(true);
  pushEntry("user", value);
  renderHistory();
  try {
    await streamAgent(value);
  } catch (error) {
    pushEntry("assistant", `Agent failed: ${error.message}`, "error");
    renderHistory();
  } finally {
    promptEl.value = "";
    toggleForm(false);
  }
});

async function bootstrap() {
  try {
    const res = await fetch("/api/session", { method: "POST" });
    const data = await res.json();
    state.sessionId = data.sessionId;
    statusEl.textContent = "Agent ready";
  } catch (error) {
    statusEl.textContent = "Session failed";
    console.error(error);
  }
}

function streamAgent(message) {
  return new Promise((resolve, reject) => {
    const url = `/api/agent-stream?sessionId=${encodeURIComponent(
      state.sessionId,
    )}&message=${encodeURIComponent(message)}`;
    const source = new EventSource(url);
    let settled = false;

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.stage === "error") {
        source.close();
        settled = true;
        reject(new Error(payload.content));
        return;
      }

      const stage =
        payload.stage === "complete" ? "summary" : payload.stage || "assistant";
      pushEntry("assistant", payload.content, stage);
      renderHistory();

      if (payload.stage === "complete") {
        source.close();
        settled = true;
        resolve();
      }
    };

    source.onerror = () => {
      if (!settled) {
        source.close();
        settled = true;
        reject(new Error("Stream interrupted"));
      }
    };
  });
}

function pushEntry(role, content, stage) {
  state.history.push({ role, content, stage });
}

function toggleForm(disabled) {
  Array.from(formEl.elements).forEach((element) => {
    element.disabled = disabled;
  });
  statusEl.textContent = disabled ? "Thinking…" : "Agent ready";
}

function renderHistory() {
  if (state.history.length === 0) {
    historyEl.innerHTML =
      "<p class=\"empty\">No conversation yet. Enter a requirement to get started.</p>";
    return;
  }
  historyEl.innerHTML = state.history
    .map((entry) => {
      const title = entry.role === "user" ? "You" : stageLabel(entry.stage);
      if (entry.content.includes("```")) {
        return `<div class="history-entry"><h3>${title}</h3><div class="agent-block">${renderMarkdown(entry.content)}</div></div>`;
      }
      return `<div class="history-entry"><h3>${title}</h3><p>${escapeHtml(entry.content)}</p></div>`;
    })
    .join("");
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderMarkdown(text) {
  const segments = text.split(/```/);
  const parts = [];

  segments.forEach((segment, index) => {
    if (index % 2 === 1) {
      const [firstLine, ...rest] = segment.split("\n");
      const lang = firstLine.trim();
      const code = rest.join("\n");
      parts.push(
        `<pre><code class="language-${lang || "text"}">${escapeHtml(code.trim())}</code></pre>`,
      );
    } else {
      const trimmed = segment.trim();
      if (!trimmed) return;
      const html = escapeHtml(trimmed)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n{2,}/g, "</p><p>")
        .replace(/\n/g, "<br>");
      parts.push(`<p>${html}</p>`);
    }
  });

  if (parts.length === 0) {
    return `<p>${escapeHtml(text)}</p>`;
  }
  return parts.join("");
}

function stageLabel(stage) {
  if (!stage) return "Agent";
  const labels = {
    planner: "Agent · Planner",
    coder: "Agent · Coder",
    reviewer: "Agent · Reviewer",
    summary: "Agent · Summary",
    error: "Agent · Error",
  };
  return labels[stage] || "Agent";
}
