# AI Support Bot

An LLM-powered chatbot built step by step — from a basic CLI bot to a production-grade support assistant with multi-provider resilience, cost-aware routing, observability, and a web UI.

**Stack:** Python · FastAPI · Anthropic (Claude) · Groq (Llama) · Gemini · HTML/CSS/JS

---

## Step-by-Step Progression

The project was built incrementally. Each step builds directly on the previous one.

### Step 0 — Environment Setup
Connect to the Anthropic API. Load key from `.env`, install `anthropic` SDK, send one hardcoded prompt, confirm the response prints.

### Step 1 — Basic Connection
Create `backend/bot.py`. Initialise the Anthropic client, send a hardcoded message (`"Hello, who are you?"`), print the response.

### Step 2 — Input Loop
Wrap the API call in a `while True` loop. Use `input()` to read user queries. Exit cleanly on `quit` / `exit` / `Ctrl+C`.

### Step 3 — Streaming Responses
Switch to the SDK's `stream` context manager. Print each text delta as it arrives — no buffering, output flows in real time.

### Step 4 — System Prompt
Define a system prompt that sets the bot's role, tone, and knowledge domain. Pass it as the `system=` parameter on every API call.

### Step 5 — Conversation Memory
Maintain a `messages` list of `{role, content}` dicts. Append each user query and assistant response. Pass the full list on every call so the model sees full context.

### Step 6 — Multi-Provider Resilience
Add Groq and Gemini as fallback providers. `chat()` tries each in order with try/except — first success wins. Each provider has its own `_stream_*` function handling SDK differences (Anthropic takes `system=` separately; Groq prepends it to the messages list; Gemini uses `GenerateContentConfig(system_instruction=...)`). On total failure, the user message is popped from history.

### Step 7 — Observability Layer
Log per-request metadata: request ID, timestamp, provider, model, token counts, latency, estimated cost, error. Print a session summary on exit: total requests, tokens, cost, avg latency, primary vs. fallback breakdown.

### Step 8 — Cost-Aware Routing
Use a lightweight LLM classifier to label each query `"simple"` or `"complex"`. Route simple queries to cheaper models, complex queries to capable models. System prompt and context stay the same — only the model changes.

### Step 9 — Frontend (Web UI)
Replace CLI with a browser-based chat interface. FastAPI serves a `/chat` SSE endpoint and `frontend/` static files. Vanilla JS sends messages and renders streamed responses.

---

## Current Architecture

```
Browser                FastAPI (uvicorn)            Provider SDKs
  │                        │                              │
  │ POST /chat             │                              │
  │ {message, session_id} ─►                              │
  │                        │  chat_iter() generator       │
  │                        │  ─ classify query            │
  │ ◄─ SSE stream ─────────│  ─ call provider.stream_iter │
  │  data: {type:routing}  │  ─ yield chunk dicts        │◄─ streaming SDK
  │  data: {type:chunk}    │                              │
  │  data: {type:done}     │                              │
```

### File structure

```
AI_Support_Bot/
├── .gitignore
├── README.md
├── backend/
│   ├── __init__.py               # Makes backend a Python package
│   ├── main.py                   # CLI entry point only — no logic
│   ├── api.py                    # FastAPI app — SSE /chat, DELETE /session, GET /health
│   ├── config.py                 # Env loading + cost constants (keyed by model)
│   ├── prompts.py                # SYSTEM_PROMPT + CLASSIFICATION_PROMPT
│   ├── chat.py                   # Orchestration — chat() CLI + chat_iter() SSE generator
│   ├── observability.py          # RequestLog dataclass + SessionStats
│   ├── classifiers/
│   │   ├── __init__.py           # STRATEGIES registry + get_classifier() factory
│   │   ├── base.py               # ClassifierStrategy ABC
│   │   ├── keyword.py            # KeywordClassifier — no API call
│   │   ├── heuristic.py          # HeuristicClassifier — structure-based, no API call
│   │   └── llm.py                # LLMClassifier — Groq → Haiku → Heuristic → Keyword
│   └── providers/
│       ├── __init__.py           # PROVIDERS registry
│       ├── anthropic.py          # Anthropic — stream_iter() + stream(), simple + complex
│       ├── groq.py               # Groq — non-streaming (SDK limitation), simple + complex
│       └── gemini.py             # Gemini — stream_iter() + stream(), simple + complex
└── frontend/
    ├── index.html                # Chat UI shell (sidebar + messages + input bar)
    ├── style.css                 # Dark-theme, typing indicator, meta badges
    └── app.js                    # Fetch + ReadableStream SSE consumer
```

---

## Design Principles

### Single Responsibility Principle

Each file has exactly one job:

| File | Responsibility |
|------|---------------|
| `main.py` | CLI input loop — nothing else |
| `api.py` | FastAPI routes, CORS, session store, SSE response |
| `config.py` | Load `.env` and define cost constants |
| `prompts.py` | `SYSTEM_PROMPT` and `CLASSIFICATION_PROMPT` constants |
| `chat.py` | Orchestrate one turn: classify → try providers → log. Exposes `chat()` (CLI) and `chat_iter()` (SSE) |
| `observability.py` | `RequestLog` dataclass, `SessionStats`, summary printer |
| `classifiers/base.py` | `ClassifierStrategy` ABC — defines the classify contract |
| `classifiers/*.py` | One classification strategy per file |
| `providers/*.py` | One provider's SDK calls per file |

### Open/Closed Principle

The system is open for extension, closed for modification.

**Adding a new provider** — touch only three places:
1. Create `backend/providers/<name>.py` with `MODEL_SIMPLE`, `MODEL_COMPLEX`, `stream_iter()`, `stream()`
2. Add one entry to `PROVIDERS` in `backend/providers/__init__.py`
3. Add cost entries to `COST_PER_TOKEN` in `config.py`

**Adding a new classifier** — touch only three places:
1. Create `backend/classifiers/<name>.py` implementing `ClassifierStrategy`
2. Add it to `STRATEGIES` in `backend/classifiers/__init__.py`
3. Set `_ACTIVE_STRATEGY = "<name>"` to activate

Nothing else changes in either case.

### Separation of Concerns

- Provider SDKs (`anthropic`, `groq`, `google.genai`) are never imported outside `providers/`
- `chat.py` does not know which SDK is running — it only calls `provider.stream(history, complexity)`
- `observability.py` receives data — it does not collect or trigger it
- Classifiers classify — no knowledge of providers or history

---

## Providers and Models

| Provider | Simple model | Complex model | Notes |
|----------|-------------|---------------|-------|
| Anthropic | `claude-haiku-4-5` | `claude-opus-4-7` | Native streaming via `messages.stream()` |
| Groq | `llama-3.1-8b-instant` | `llama-3.3-70b-versatile` | No `stream_options` — yields single chunk |
| Gemini | `gemini-2.5-flash-lite` | `gemini-2.5-flash` | Role names: `"model"` not `"assistant"` |

Provider fallback order: Anthropic → Groq → Gemini. On total failure, the user message is popped from history to keep it clean.

### Provider contract

Every `providers/*.py` module must expose exactly:

```python
MODEL_SIMPLE:  str   # model ID for simple queries
MODEL_COMPLEX: str   # model ID for complex queries

def stream_iter(history: list, complexity: str = "complex") -> Generator:
    # Yields str text chunks, then a final metadata dict:
    # {"model": ..., "input_tokens": ..., "output_tokens": ...}
    # No side effects (no printing). Used by api.py for SSE.

def stream(history: list, complexity: str = "complex") -> tuple[str, int, int, str]:
    # CLI wrapper — calls stream_iter, prints chunks, returns:
    # (reply, input_tokens, output_tokens, model_used)
```

### History format

Universal format, shared across all providers. Each provider converts internally — callers never deal with SDK-specific types:

```python
[
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."},
]
```

Provider-specific conversions (internal):
- **Anthropic**: history passed as-is; system prompt via separate `system=` param
- **Groq**: system prompt prepended as `{"role": "system", ...}` to messages list
- **Gemini**: role `"assistant"` → `"model"`, content wrapped in `parts=[Part(text=...)]`

Both `chat()` and `chat_iter()` mutate the history list in place — callers must pass the same list reference across turns.

---

## Classifier and Routing

Before every request, the classifier labels the query `"simple"` or `"complex"`, selecting the cheaper or more capable model tier.

| Classifier | API call | Latency | Accuracy | Best for |
|-----------|----------|---------|----------|---------|
| `KeywordClassifier` | No | ~0ms | Good for known phrases | Predictable, zero-cost |
| `HeuristicClassifier` | No | ~0ms | Moderate, structure-based | No maintenance |
| `LLMClassifier` | Yes (Groq) | ~200ms | Best, understands intent | When accuracy matters |

**LLMClassifier fallback chain:**
```
Groq llama-3.1-8b-instant   ← primary (~$0.0000175/call — cheapest at scale)
    ↓ fails
Anthropic claude-haiku-4-5  ← secondary (~$0.000355/call — 20x costlier)
    ↓ fails
HeuristicClassifier         ← structure-based, no API
    ↓ fails
KeywordClassifier           ← hardcoded sets, last resort
```

Internals: `max_tokens=5`, `temperature=0` — one deterministic word expected. `_validate()` ensures the response is `"simple"` or `"complex"`; falls to heuristic if not. Self-healing by design — never crashes the system.

Swap the active strategy with one line: `_ACTIVE_STRATEGY = "keyword"`. Nothing else changes.

---

## SSE Event Protocol

`POST /chat` returns `text/event-stream`. Events emitted by `chat_iter()`:

| Event type | When | Key fields |
|-----------|------|-----------|
| `routing` | After classification | `complexity` |
| `chunk` | While streaming | `text` |
| `done` | After last chunk | `provider`, `model`, `complexity`, `input_tokens`, `output_tokens`, `latency_ms`, `cost_usd` |
| `provider_error` | Provider fails, next tried | `provider`, `error` |
| `fatal` | All providers exhausted | `error` |

`app.js` reads the stream with `resp.body.getReader()` (not `EventSource`, which only supports GET). Each `data: {...}` line is parsed and dispatched to `handleEvent()`.

### chat_iter() vs chat()

Both live in `chat.py` and share the same classify → provider fallback → log flow:

| Function | Used by | Calls | Yields/Returns |
|----------|---------|-------|----------------|
| `chat()` | `main.py` CLI | `provider.stream()` — prints chunks | `(reply, in_tokens, out_tokens, model)` |
| `chat_iter()` | `api.py` SSE | `provider.stream_iter()` — pure generator | SSE dicts (`routing`, `chunk`, `done`, ...) |

---

## Cost Tracking

`config.py` holds a cost table keyed by **model name** (not provider — simple vs. complex tiers differ significantly):

| Model | Input ($/M) | Output ($/M) |
|-------|------------|-------------|
| `claude-opus-4-7` | $5.00 | $25.00 |
| `claude-haiku-4-5` | $1.00 | $5.00 |
| `llama-3.3-70b-versatile` | $0.59 | $0.79 |
| `llama-3.1-8b-instant` | $0.05 | $0.08 |
| `gemini-2.5-flash` | $0.15 | $0.60 |
| `gemini-2.5-flash-lite` | $0.10 | $0.40 |

Every request logs: `request_id`, `provider`, `model`, `complexity`, `input_tokens`, `output_tokens`, `latency_ms`, `estimated_cost_usd`, `is_fallback`, `error`. On CLI exit, `SessionStats.print_summary()` prints aggregate totals.

---

## Session Handling

In-memory dict keyed by `session_id` (default `"default"`). Each session holds its own `history` list and `SessionStats`. `DELETE /session?session_id=X` clears history for that session. State does not survive server restarts.

---

## Known SDK Differences and Gotchas

### Groq — no `stream_options`
Groq SDK does not support `stream_options={"include_usage": True}` — passing it raises `unexpected keyword argument`. Fix: Groq provider uses non-streaming (`stream=False`) to get accurate token counts from `response.usage`. The full response yields as a single chunk; the provider contract is still honored.

### Gemini — role naming
Gemini uses `"model"` not `"assistant"` for AI turns. Content must be wrapped: `parts=[types.Part(text=...)]`. System prompt passed via `GenerateContentConfig(system_instruction=...)`.

### Anthropic — system prompt separation
Anthropic takes system prompt as a separate `system=` parameter, not inside the messages list. Do not use `{"role": "system", ...}` — that format is not supported by the Anthropic SDK.

### Gemini — deprecated models
`gemini-2.0-flash` and `gemini-2.0-flash-lite` shut down June 1, 2026. Use `gemini-2.5-flash` and `gemini-2.5-flash-lite`.

---

## Environment Variables

Keys are read from `AI_Learning/.env` at the repo root — no project-level `.env` needed. `config.py` loads it via `dotenv_values(Path(__file__).resolve().parent.parent.parent / ".env")`.

| Key | Required | Provider | Get it from |
|-----|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Primary | console.anthropic.com |
| `GROQ_API_KEY` | Yes | 2nd fallback | console.groq.com |
| `GEMINI_API_KEY` | Yes | 3rd fallback | aistudio.google.com |

---

## Running

**From repo root (recommended):**
```bash
make install            # one-time setup
make support-bot        # web UI at http://localhost:8001
make support-cli        # CLI mode in terminal
```

**Manual (no Makefile):**
```bash
# Always run from AI_Support_Bot/ root — required for package imports
cd AI_Support_Bot/
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

python -m backend.main                              # CLI
uvicorn backend.api:app --reload --port 8001        # web UI
```

`python -m backend.main` — not `python backend/main.py`. The `-m` flag runs the file as part of the `backend` package so relative imports resolve correctly.

`backend.api:app` = the `app` object in `backend/api.py`. FastAPI serves `frontend/` at `/` via `StaticFiles`.

---

## What NOT to do

- Do not import provider SDKs (`anthropic`, `groq`, `google.genai`) outside `providers/`
- Do not add business logic to `main.py`
- Do not mix observability and chat logic in the same function
- Do not hardcode model names outside their respective provider file
- Do not key `COST_PER_TOKEN` by provider name — always by model name
- Do not swallow exceptions inside `stream()` — let `chat.py` handle fallback
- Do not run from inside `backend/` — always run from `AI_Support_Bot/` root
- Do not commit `.env`
