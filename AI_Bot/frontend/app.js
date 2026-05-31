/**
 * AI Support Bot — frontend logic
 *
 * Flow:
 *  1. User submits message → POST /chat with {message, session_id}
 *  2. Response is an SSE stream. We read it with ReadableStream + TextDecoder.
 *  3. Each "data: {...}" line is parsed and handled by type:
 *       routing       → (ignored visually)
 *       chunk         → accumulate text, re-render full markdown into bot bubble
 *       done          → fill in metadata badge (model + tokens)
 *       provider_error→ show a small warning (non-fatal, next provider tried)
 *       fatal         → show error bubble
 *
 * Markdown rendering: marked.js (loaded via CDN in index.html).
 * Bot bubbles render innerHTML from marked.parse(fullText).
 * User bubbles stay as escaped plain text (no markdown needed).
 */

// Configure marked — open all links in a new tab
const renderer = new marked.Renderer();
renderer.link = (href, title, text) =>
  `<a href="${href}" target="_blank" rel="noopener noreferrer"${title ? ` title="${title}"` : ""}>${text}</a>`;

marked.setOptions({ breaks: true, gfm: true, renderer });

const SESSION_ID  = "default";   // single-session for now
const API_BASE    = "";           // same origin (FastAPI serves frontend too)

// ---- DOM refs ----
const messagesEl  = document.getElementById("messages");
const chatForm    = document.getElementById("chat-form");
const inputEl     = document.getElementById("user-input");
const sendBtn     = document.getElementById("send-btn");
const typingEl    = document.getElementById("typing");
const btnClear    = document.getElementById("btn-clear");

// ---- Auto-grow textarea ----
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 150) + "px";
});

// Send on Enter (Shift+Enter = newline)
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// ---- Clear session ----
btnClear.addEventListener("click", async () => {
  await fetch(`${API_BASE}/session?session_id=${SESSION_ID}`, { method: "DELETE" });
  // Remove all messages except the welcome bubble
  const msgs = messagesEl.querySelectorAll(".msg");
  msgs.forEach((m, i) => { if (i > 0) m.remove(); });
});

// ---- Submit handler ----
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  appendUserBubble(text);
  inputEl.value = "";
  inputEl.style.height = "auto";
  setInputDisabled(true);
  showTyping(true);

  const { bubbleEl, metaEl, warnEl } = appendBotBubble();
  let replyText = "";   // accumulates raw markdown as chunks arrive

  try {
    await streamChat(text, bubbleEl, metaEl, warnEl, replyText, (t) => { replyText = t; });
  } catch (err) {
    bubbleEl.textContent = "⚠️ Network error: " + err.message;
  } finally {
    showTyping(false);
    setInputDisabled(false);
    inputEl.focus();
  }
});

// ---- Core streaming function ----
async function streamChat(message, bubbleEl, metaEl, warnEl, replyText, setReplyText) {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: SESSION_ID }),
  });

  if (!resp.ok) {
    bubbleEl.textContent = `Server error ${resp.status}`;
    return;
  }

  const reader  = resp.body.getReader();
  const decoder = new TextDecoder();
  let   buffer  = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();           // keep incomplete line

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;

      let event;
      try { event = JSON.parse(raw); }
      catch { continue; }

      // Pass replyText by closure via setter
      if (event.type === "chunk") {
        replyText += event.text;
        setReplyText(replyText);
      }
      handleEvent(event, bubbleEl, metaEl, warnEl, replyText);
    }
  }
}

// ---- SSE event handler ----
function handleEvent(event, bubbleEl, metaEl, warnEl, replyText) {
  switch (event.type) {

    case "routing":
      // nothing shown while streaming
      break;

    case "chunk":
      showTyping(false);            // hide dots once text starts arriving
      bubbleEl.innerHTML = marked.parse(replyText);
      scrollToBottom();
      break;

    case "done":
      // Final render — ensures last chunk is fully parsed
      bubbleEl.innerHTML = marked.parse(replyText);
      metaEl.innerHTML = buildMeta(event);
      scrollToBottom();
      break;

    case "provider_error":
      warnEl.textContent += `⚠️ ${event.provider} failed — trying next…  `;
      break;

    case "fatal":
      bubbleEl.textContent = "❌ All providers failed. Please try again.";
      break;
  }
}

// ---- DOM helpers ----
function appendUserBubble(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `
    <div class="avatar">🧑</div>
    <div class="bubble">${escapeHtml(text)}</div>
  `;
  messagesEl.appendChild(div);
  scrollToBottom();
}

function appendBotBubble() {
  const div = document.createElement("div");
  div.className = "msg bot";

  const bubble  = document.createElement("div");
  bubble.className = "bubble";

  const meta    = document.createElement("div");
  meta.className = "meta-badge";

  const warn    = document.createElement("div");
  warn.className = "provider-warn";

  const wrap = document.createElement("div");
  wrap.style.display = "flex";
  wrap.style.flexDirection = "column";
  wrap.appendChild(bubble);
  wrap.appendChild(warn);
  wrap.appendChild(meta);

  div.innerHTML = `<div class="avatar">🤖</div>`;
  div.appendChild(wrap);
  messagesEl.appendChild(div);
  scrollToBottom();

  return { bubbleEl: bubble, metaEl: meta, warnEl: warn };
}

function buildMeta(event) {
  return `
    <span class="tag">${event.model}</span>
    <span class="tag">⬆ ${event.input_tokens} ⬇ ${event.output_tokens}</span>
  `;
}

function routingTag(complexity) {
  return `<span class="tag ${complexity}">${complexity}</span>`;
}

function showTyping(visible) {
  typingEl.classList.toggle("hidden", !visible);
}

function setInputDisabled(disabled) {
  inputEl.disabled = disabled;
  sendBtn.disabled = disabled;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
