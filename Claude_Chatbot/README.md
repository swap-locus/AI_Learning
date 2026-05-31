# Claude Chatbot

A minimal end-to-end chatbot: Flask backend proxies the Anthropic SDK, single-file HTML frontend. The API key lives server-side only — the browser never sees it.

**Stack:** Python · Flask · Anthropic SDK · vanilla HTML/CSS/JS

---

## How it works

```
Browser                     Flask (app.py)              Anthropic SDK
  │                              │                            │
  │  GET /api/models             │                            │
  │ ─────────────────────────►  │  models.list()  ──────────►│
  │ ◄─────────────────────────  │  ◄──────────────────────── │
  │                              │                            │
  │  POST /api/chat              │                            │
  │  {model, messages, system}  ─►                            │
  │                              │  messages.create() ───────►│
  │ ◄── SSE stream ─────────────│  ◄── text stream ──────────│
```

1. Browser loads `index.html`, which fetches `GET /api/models`
2. Flask calls `client.models.list()` and returns model list sorted newest-first
3. User types a message → frontend POSTs it to `/api/chat` with full conversation history
4. Flask calls `client.messages.create()` and streams or returns the response
5. Reply is appended to the in-memory `messages` array for multi-turn context

**Why a proxy backend?** The API key would be visible in page source if the browser called the API directly. CORS also blocks browser requests to `api.anthropic.com`. Flask solves both.

---

## File structure

```
Claude_Chatbot/
├── backend/
│   ├── app.py            # Flask server — all logic lives here
│   └── requirements.txt
└── frontend/
    └── index.html        # Full UI — HTML + CSS + JS, no build step
```

---

## API endpoints

| Route | Method | What it does |
|-------|--------|-------------|
| `/api/models` | GET | Calls `client.models.list()`, returns JSON |
| `/api/chat` | POST | Calls `client.messages.create()`, supports `stream: true` and non-streaming |
| `/` and `/<path>` | GET | Serves `frontend/index.html` and static files |

`POST /api/chat` accepts: `{model, messages, system?, max_tokens, temperature, stream, top_p?, top_k?, stop_sequences?}`

---

## SSE streaming

When `stream: true` is in the POST body, `app.py` returns `Content-Type: text/event-stream`:

| Event type | Payload |
|-----------|---------|
| `delta` | `{type: "delta", text: "..."}` — one token |
| `done` | `{type: "done", message: {...}}` — final message object |
| `error` | `{type: "error", error: {...}}` — SDK or proxy error |

The frontend reads with `response.body.getReader()` — not `EventSource`, which only supports GET.

---

## UI features

- **Model dropdown** — populated live from `/api/models`, sorted newest-first
- **Max tokens** — number input (1–8192, default 1024)
- **Temperature** — slider (0–1, step 0.01) with live value display
- **Stream toggle** — switches between SSE streaming and non-streaming mode
- **System prompt** — collapsible panel, persisted to `localStorage` across reloads
- **Reset** — clears conversation history; preserves system prompt
- **Status line** — shows model name and token usage (input/output) per turn
- **Enter** sends; **Shift+Enter** inserts a newline

---

## Environment variables

All keys are read from `AI_Learning/.env` at the repo root (3 levels up from `backend/`).

| Key | Required | Notes |
|-----|----------|-------|
| `ANTHROPIC_API_KEY` | Yes | Read from `AI_Learning/.env` at repo root |
| `PORT` | No | Overrides default 8080; also settable via `--port` CLI arg |
| `VERIFY_SSL` | No | Set to `false` only behind a TLS-intercepting corporate proxy |

---

## Setup and run

**From repo root (recommended):**
```bash
make install        # one-time setup — creates root .venv, installs all deps
make chatbot        # starts on port 8080
```

**Custom port:**
```bash
cd Claude_Chatbot/backend && ../../.venv/bin/python app.py --port 9000
```

**Manual (no Makefile):**
```bash
cd Claude_Chatbot/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8080`.

`app.py` must be run from inside `backend/` — it resolves the `frontend/` path relative to its own location.

---

## Developer notes

**Per-request client instantiation** — `_get_client()` creates a new Anthropic SDK client on each request rather than a module-level singleton. This allows the API key to be re-read from the environment without a server restart and avoids shared state in multi-user scenarios.

**SSL verification toggle** — `_verify_ssl()` reads `VERIFY_SSL` env var. Default: `true`. Set to `false` only behind a corporate TLS-intercepting proxy.

**Pydantic serialisation** — SDK response objects are converted to plain dicts via `.model_dump()` before JSON serialisation. This ensures the response shape exactly matches the Anthropic REST API contract.

**System prompt design** — the system prompt is never stored in the `messages` array; it is sent as the top-level `system=` parameter on every request. This allows changing it mid-conversation without re-sending previous turns.

### What NOT to do

- Do not import `anthropic` anywhere except `app.py`
- Do not put business logic in `__main__` — it only parses args and calls `app.run`
- Do not run `app.py` from the `Claude_Chatbot/` root — paths resolve relative to `backend/`
- Do not commit `.env` or any file containing the API key

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `"ANTHROPIC_API_KEY not set"` | Ensure `AI_Learning/.env` exists and contains the key |
| Models show "failed to load" | Key is wrong or server can't reach `api.anthropic.com` — verify key in Postman |
| Port already in use | Run with `--port 9001` or `PORT=9001 python app.py` |
| CORS errors in browser | Should not happen — Flask proxy handles it; check the server is actually running |
