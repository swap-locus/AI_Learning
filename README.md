# AI Learning — Hands-On AI Engineering with the Anthropic API

A progressive series of AI engineering projects built on the Anthropic Claude API. Each subproject teaches a distinct layer of complexity — from a minimal chatbot proxy to a production-grade multi-provider support bot, interactive Jupyter labs, an MCP (Model Control Protocol) chat client/server, and a set of Claude API feature labs.

---

## Quick Start

Most projects install into a single root venv; `MCP_Learning` manages its own venv via `uv`. One setup command installs everything, then `make <project>` runs anything.

```bash
# 1. Add your API keys
cp .env.example .env        # fill in ANTHROPIC_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, VOYAGE_API_KEY, CLAUDE_MODEL

# 2. Install everything (root .venv + MCP_Learning uv env)
make install

# 3. Run whichever project you want
make chatbot                # Claude Chatbot   → http://localhost:9000
make support-bot            # AI Support Bot   → http://localhost:9001
make support-cli            # AI Support Bot   → terminal (CLI mode)
make jupyter                # JupyterNotebook  → JupyterLab in browser
make claude-features        # Claude Features  → JupyterLab in browser
make mcp-chat               # MCP Chat         → terminal (CLI mode)
```

---

## Repository Structure

```
AI_Learning/
├── .env                     # All API keys — single source of truth, never commit
├── .env.example             # Template — copy to .env and fill in keys
├── .gitignore
├── requirements.txt         # Combined dependencies for the root-venv projects
├── Makefile                 # install + run targets for every project
├── Claude_Chatbot/          # Minimal chatbot — Flask proxy, SSE streaming, model picker
├── AI_Bot/          # Production bot — multi-provider, classifier routing, cost tracking
├── JupyterNotebook/         # Interactive labs — evals, RAG pipeline, tool use, prompt techniques
├── ClaudeFeatures/          # Claude API feature labs — thinking, images, PDFs, caching, code execution
└── MCP_Learning/            # MCP chat CLI — uv-managed stdio client/server, tools, resources, prompts
```

A single `.env` at the repo root supplies API keys to **all** subprojects. A single `.venv` at the repo root runs every project **except** `MCP_Learning`, which keeps its own `uv`-managed `.venv` (it ships a `pyproject.toml` + `uv.lock`).

---

## Environment Setup

```bash
cp .env.example .env    # then fill in your keys
make install            # creates .venv, installs all deps, registers Jupyter kernel
```

| Key | Required by |
|-----|------------|
| `ANTHROPIC_API_KEY` | all projects |
| `GROQ_API_KEY` | AI_Bot |
| `GEMINI_API_KEY` | AI_Bot |
| `VOYAGE_API_KEY` | JupyterNotebook (RAG series) |
| `CLAUDE_MODEL` | MCP_Learning (model id passed to the Claude service) |
| `USE_UV` | MCP_Learning (optional — spawn the MCP server via `uv run` (`1`) or `python` (`0`)) |

---

## Learning Progression

Start with `Claude_Chatbot` to understand the API proxy pattern and streaming. Move to `JupyterNotebook` to explore embeddings, RAG, and tool use interactively, and `ClaudeFeatures` to exercise individual Claude API capabilities. Then learn the Model Control Protocol with `MCP_Learning`. Finish with `AI_Bot` to see production patterns: strategy routing, multi-provider fallback, cost tracking, and observability.

| Step | Project | Core Skill |
|------|---------|-----------|
| 1 | `Claude_Chatbot` | API proxy, SSE streaming, model picker UI |
| 2 | `JupyterNotebook` | Prompt evals, RAG from scratch, tool use patterns |
| 3 | `ClaudeFeatures` | Extended thinking, vision, PDFs, prompt caching, code execution |
| 4 | `MCP_Learning` | MCP stdio client/server — tools, resources, prompts, CLI chat |
| 5 | `AI_Bot` | Multi-provider fallback, classifier routing, cost tracking |

---

## Project 1: Claude Chatbot

**Stack:** Python, Flask, Anthropic SDK, vanilla HTML/CSS/JS
**Location:** `Claude_Chatbot/`

A security-conscious minimal chatbot demonstrating the core API proxy pattern: the API key lives server-side only and the browser never sees it. The Flask backend proxies to the Anthropic API; a single `index.html` is the complete frontend with no build step.

### What it teaches

- API proxy pattern — keep secrets server-side
- Server-Sent Events (SSE) for real-time token streaming
- Non-streaming vs. streaming mode toggle
- Dynamic model picker populated live from `/v1/models`
- System prompt persisted in `localStorage`
- Per-request client instantiation for key hot-reloading

### Architecture

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

**Why a proxy backend?** `ANTHROPIC_API_KEY` must never reach the browser. Flask sits in between — the key is invisible to the client.

### File structure

```
Claude_Chatbot/
├── backend/
│   ├── app.py            # Flask server — all logic lives here
│   └── requirements.txt
└── frontend/
    └── index.html        # Full UI — HTML + CSS + JS, no build step
```

### API endpoints

| Route | Method | What it does |
|-------|--------|-------------|
| `/api/models` | GET | Calls `client.models.list()`, returns JSON sorted newest-first |
| `/api/chat` | POST | Calls `client.messages.create()`, supports `stream: true` and non-streaming |
| `/` and `/<path>` | GET | Serves `frontend/index.html` and static files |

### SSE streaming

When `stream: true` is in the POST body, `app.py` returns a `text/event-stream` response:

| Event type | Payload |
|-----------|---------|
| `delta` | `{type: "delta", text: "..."}` — one token |
| `done` | `{type: "done", message: {...}}` — final message object |
| `error` | `{type: "error", error: {...}}` — SDK or proxy error |

The frontend reads with `response.body.getReader()` — not `EventSource`, which only supports GET.

### UI controls

Model dropdown, max tokens (1–8192), temperature slider (0–1, step 0.01), stream toggle, reset button, collapsible system prompt panel (persisted to `localStorage`), token usage display per turn.

### Environment variables

| Key | Required | Notes |
|-----|----------|-------|
| `ANTHROPIC_API_KEY` | Yes | Read from `AI_Learning/.env` at repo root |
| `PORT` | No | Overrides default 9000; also settable via `--port` CLI arg |
| `VERIFY_SSL` | No | Set to `false` only behind a TLS-intercepting corporate proxy |

### How to run

```bash
make chatbot                # from repo root — starts on port 9000
```

Custom port: `cd Claude_Chatbot/backend && ../../.venv/bin/python app.py --port 9000`

Open `http://localhost:9000`.

### What NOT to do

- Do not import `anthropic` anywhere except `app.py`
- Do not put business logic in `__main__` — it only parses args and calls `app.run`
- Do not run `app.py` from `Claude_Chatbot/` root — paths resolve relative to `backend/`
- Do not commit `.env`

---

## Project 2: JupyterNotebook Labs

**Stack:** Python, Jupyter, Anthropic SDK, VoyageAI
**Location:** `JupyterNotebook/`

Eleven notebooks in four series. Each notebook is fully self-contained — no cross-imports, no shared modules. Data structures (vector database, BM25 index, RAG pipeline) are built from scratch using only stdlib to keep internals fully visible.

### Conventions

- **No framework dependencies** — `VectorIndex`, `BM25Index`, `Retriever` use only Python stdlib + `math`
- **Self-contained notebooks** — common helpers (`add_user_message`, `add_assistant_message`, `chat`) are copied into each notebook; never imported from outside
- **Prefill pattern** for structured output: `add_assistant_message(messages, "```json")` + `stop_sequences=["```"]`
- **Agentic tool loop**: `while True` → call API → check `stop_reason == "tool_use"` → run tools → feed results back → repeat
- **Batch embeddings** — always use `add_documents()` instead of looping `add_document()` to avoid VoyageAI rate limits
- Keys are loaded from `AI_Learning/.env` via `load_dotenv()` which searches upward through parent directories automatically

### Models used

| Series | Model |
|--------|-------|
| PromptEvaluation | `claude-haiku-4-5` |
| Prompt_Techniques | `claude-haiku-4-5` |
| RAG_Agentic_Search | VoyageAI `voyage-3-large` (embeddings only) |
| ToolsUse | `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-opus-4-7` |

### Series 1 — Prompt Evaluation (`PromptEvaluation/`)

**`001_prompt_evals.ipynb`** — LLM-as-judge evaluation pipeline

Builds a complete eval loop: generate a test dataset via LLM, run a candidate prompt on each case, grade the output with a second LLM call, report average score. Uses the **prefill technique** for reliable JSON extraction:

```python
add_assistant_message(messages, "```json")   # force JSON start
chat(messages, stop_sequences=["```"])        # stop at closing backtick
```

Also implements syntax validators using `ast.parse()`, `json.loads()`, and `re.compile()` for Python, JSON, and Regex output formats.

### Series 2 — Prompt Techniques (`Prompt_Techniques/`)

**`001_prompting.ipynb`** — `PromptEvaluator` class with concurrent execution and HTML reporting

Full evaluation harness with template rendering, `ThreadPoolExecutor`-based concurrency, and HTML report generation (color-coded score badges, scrollable result tables). Baseline naive prompt; average score: **4.67/10**.

**`002_prompting_completed.ipynb`** — Same harness, improved prompt

Adds XML structural tags (`<sample_input>/<ideal_output>`), concrete examples, mandatory vs. secondary criteria, and explicit scoring guidelines. Average score: **7.0/10** — a concrete demonstration of prompt engineering impact.

### Series 3 — RAG Agentic Search (`RAG_Agentic_Search/`)

Builds a complete RAG pipeline from scratch, using a synthetic annual report (`report.md`) as the knowledge base. Each notebook adds one layer on top of the previous.

**`001_chunking.ipynb`** — Three chunking strategies

- `chunk_by_char(text, chunk_size=150, chunk_overlap=20)` — fixed character windows with overlap
- `chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1)` — sentence-level windows
- `chunk_by_section(text)` — markdown section splits (used by all subsequent RAG notebooks)

**`002_embeddings.ipynb`** — VoyageAI embedding generation

```python
client.embed(texts, model="voyage-3-large", input_type="query")
# returns result.embeddings — list of float vectors
```

**`003_vectordb.ipynb`** — Vector database from scratch

`VectorIndex` class, stdlib only, two distance metrics:

```
add_document(doc)   → embeds + stores
add_documents(docs) → batch version (use this to avoid rate limits)
search(query, k=1)  → [(document, distance)] sorted by similarity
```

Cosine: `1 - dot_product / (mag1 * mag2)`. Euclidean: `sqrt(sum((p-q)^2))`.

**`004_bm25.ipynb`** — Sparse retrieval (BM25) from scratch

`BM25Index` with configurable `k1` (term-frequency saturation) and `b` (length normalization). Implements IDF and the full BM25 scoring formula. Complements dense retrieval for keyword-heavy queries.

**`005_hybrid.ipynb`** — Hybrid retrieval with Reciprocal Rank Fusion

`Retriever` accepts any number of `SearchIndex`-compliant indexes and fuses their rankings with RRF:

```python
rrf_score = sum(1.0 / (k_rrf + rank) for rank in ranks)  # k_rrf=60
```

Combines dense (semantic) and sparse (keyword) signals without tuning per-index weights.

### Series 4 — Tool Use (`ToolsUse/`)

**`001_tools.ipynb`** — Basic tool calling

Tool schema construction, `ToolUseBlock` extraction, and `tool_result` message construction. Single tool; single-turn.

**`001_tools_007.ipynb`** — Multi-tool agentic loop

`run_tools()` dispatcher extracts all `ToolUseBlock` items, executes each, returns `tool_result` messages. Loop runs until `stop_reason != "tool_use"`. Demonstrates multi-step reasoning: compute a date, then use it in a subsequent tool call.

**`003_FineGrained_ToolCalling.ipynb`** — Fine-grained streaming

Uses beta `fine-grained-tool-streaming-2025-05-14`. Streams tool argument JSON character-by-character via `input_json_delta` deltas. Also covers `tool_choice`: `{"type": "none"}` disables tools; `{"type": "tool", "name": "..."}` forces a specific tool.

**`005_text_editor_tool.ipynb`** — `str_replace_based_edit_tool` (built-in)

`TextEditorTool` wrapper with five commands: `view`, `str_replace`, `create`, `insert`, `undo_edit`. Path validation prevents directory traversal; automatic file backup before every modification.

**`006_web_search_complete.ipynb`** — `web_search_20250305` (built-in)

Built-in web search with `max_uses` and `allowed_domains` restrictions:

```python
{"type": "web_search_20250305", "name": "web_search", "max_uses": 5, "allowed_domains": ["nih.gov"]}
```

### How to run

```bash
make jupyter                # from repo root — opens JupyterLab in browser
```

In VS Code / Cursor: select kernel **Python (AI_Learning .venv)**. If `No module named 'dotenv'` appears, the wrong kernel is selected — change it, do not reinstall.

Run series in order: PromptEvaluation → Prompt_Techniques → RAG_Agentic_Search → ToolsUse.

### Adding a new notebook

1. Place it in the appropriate series folder
2. Copy common helpers (`add_user_message`, `add_assistant_message`, `chat`) from a sibling notebook — do not import from outside
3. Start with `load_dotenv(find_dotenv())` and client setup as the first cell
4. Add a row to the relevant series table in this README

---

## Project 3: AI Support Bot

**Stack:** Python, FastAPI, Anthropic + Groq + Gemini SDKs, vanilla HTML/CSS/JS
**Location:** `AI_Bot/`

A production-grade support chatbot for coding challenges (codingchallenges.fyi). Demonstrates multi-provider resilience, cost-aware classifier routing, SSE streaming, and per-session observability. Built incrementally (Steps 0–9), so the git history is itself a learning progression.

### Architecture

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

### File responsibilities (Single Responsibility Principle)

Every file has exactly one job:

| File | Responsibility |
|------|---------------|
| `main.py` | CLI input loop — nothing else |
| `api.py` | FastAPI routes, CORS, session store, SSE response |
| `config.py` | Load `.env` and define cost constants |
| `prompts.py` | `SYSTEM_PROMPT` and `CLASSIFICATION_PROMPT` constants |
| `chat.py` | Orchestrate one turn: classify → try providers → log. Exposes `chat()` (CLI) and `chat_iter()` (SSE generator) |
| `observability.py` | `RequestLog` dataclass, `SessionStats`, summary printer |
| `classifiers/base.py` | `ClassifierStrategy` ABC — defines the classify contract |
| `classifiers/*.py` | One classification strategy per file |
| `providers/*.py` | One provider's SDK calls per file |

### Extending the system (Open/Closed Principle)

**Adding a new provider** — touch only three places:
1. Create `backend/providers/<name>.py` with `MODEL_SIMPLE`, `MODEL_COMPLEX`, `stream_iter()`, `stream()`
2. Add one entry to `PROVIDERS` in `backend/providers/__init__.py`
3. Add cost entries to `COST_PER_TOKEN` in `config.py`

**Adding a new classifier** — touch only three places:
1. Create `backend/classifiers/<name>.py` implementing `ClassifierStrategy`
2. Add it to `STRATEGIES` in `backend/classifiers/__init__.py`
3. Set `_ACTIVE_STRATEGY = "<name>"` to activate

Nothing else changes in either case. Provider SDKs are never imported outside `providers/`.

### Providers and models

| Provider | Simple model | Complex model | Notes |
|----------|-------------|---------------|-------|
| Anthropic | `claude-haiku-4-5` | `claude-opus-4-7` | Native streaming via `messages.stream()` |
| Groq | `llama-3.1-8b-instant` | `llama-3.3-70b-versatile` | No `stream_options` — yields single chunk |
| Gemini | `gemini-2.5-flash-lite` | `gemini-2.5-flash` | Role names: `"model"` not `"assistant"` |

Provider fallback order: Anthropic → Groq → Gemini. On total failure, the user message is popped from history to keep it clean.

### Provider contract

Every provider module must expose exactly:

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

### Classifier and routing

Before every request, the classifier labels the query `"simple"` or `"complex"`, selecting the cheaper or more capable model tier.

| Classifier | API call | Latency | Accuracy | Best for |
|-----------|----------|---------|----------|---------|
| `KeywordClassifier` | No | ~0ms | Good for known phrases | Predictable, zero-cost |
| `HeuristicClassifier` | No | ~0ms | Moderate, structure-based | No maintenance |
| `LLMClassifier` | Yes (Groq) | ~200ms | Best, understands intent | When accuracy matters |

**LLMClassifier fallback chain:**
```
Groq llama-3.1-8b-instant   (~$0.0000175/call — primary, cheapest at scale)
  → Anthropic claude-haiku-4-5  (fallback on Groq failure — 20x costlier)
  → HeuristicClassifier          (structure-based, no API)
  → KeywordClassifier            (hardcoded sets, last resort)
```

Groq runs first because classification executes before every request. At 1,000 requests: Groq ≈ $0.02 vs. Haiku ≈ $0.35. LLMClassifier internals: `max_tokens=5`, `temperature=0` — one deterministic word expected. `_validate()` ensures response is `"simple"` or `"complex"`; falls to heuristic if not. Self-healing by design — never crashes the system.

Swap the active classifier with one line: `_ACTIVE_STRATEGY = "keyword"`. Nothing else changes.

### SSE event protocol

`POST /chat` returns `text/event-stream`. Events emitted by `chat_iter()`:

| Event type | When | Key fields |
|-----------|------|-----------|
| `routing` | After classification | `complexity` |
| `chunk` | While streaming | `text` |
| `done` | After last chunk | `provider`, `model`, `complexity`, `input_tokens`, `output_tokens`, `latency_ms`, `cost_usd` |
| `provider_error` | Provider fails, next tried | `provider`, `error` |
| `fatal` | All providers exhausted | `error` |

### chat_iter() vs chat()

Both live in `chat.py` (same SRP: orchestration) and share the same classify → provider fallback → log flow:

| Function | Used by | Calls | Yields/Returns |
|----------|---------|-------|----------------|
| `chat()` | `main.py` CLI | `provider.stream()` — prints chunks | `(reply, in_tokens, out_tokens, model)` |
| `chat_iter()` | `api.py` SSE | `provider.stream_iter()` — pure generator | SSE dicts (`routing`, `chunk`, `done`, ...) |

### Cost tracking

`config.py` holds a cost table keyed by **model name** (not provider — simple vs. complex tiers within the same provider differ significantly):

| Model | Input ($/M) | Output ($/M) |
|-------|------------|-------------|
| `claude-opus-4-7` | $5.00 | $25.00 |
| `claude-haiku-4-5` | $1.00 | $5.00 |
| `llama-3.3-70b-versatile` | $0.59 | $0.79 |
| `llama-3.1-8b-instant` | $0.05 | $0.08 |
| `gemini-2.5-flash` | $0.15 | $0.60 |
| `gemini-2.5-flash-lite` | $0.10 | $0.40 |

Every request logs: `request_id`, `provider`, `model`, `complexity`, `input_tokens`, `output_tokens`, `latency_ms`, `estimated_cost_usd`, `is_fallback`, and `error`. On CLI exit, `SessionStats.print_summary()` prints aggregate totals.

### Session handling

In-memory dict keyed by `session_id` (default `"default"`). Each session holds its own `history` list and `SessionStats`. `DELETE /session?session_id=X` clears history for that session. State does not survive server restarts.

### Known SDK differences and gotchas

**Groq — no `stream_options`**

Groq SDK is OpenAI-compatible but does not support `stream_options={"include_usage": True}`. Passing it raises `unexpected keyword argument`. Fix: Groq provider uses non-streaming (`stream=False`) to get accurate token counts from `response.usage`. The full response yields as a single chunk — the provider contract is still honored.

**Gemini — role naming**

Gemini uses `"model"` not `"assistant"` for AI turns. Content must be wrapped: `parts=[types.Part(text=...)]`. System prompt passed via `GenerateContentConfig(system_instruction=...)`.

**Anthropic — system prompt separation**

Anthropic takes system prompt as a separate `system=` parameter, not inside the messages list. Do not use `{"role": "system", ...}` — that format is not supported by the Anthropic SDK.

**History mutation**

Both `chat()` and `chat_iter()` mutate the history list in place: user message appended before calling providers, assistant message appended on success, user message popped on total failure. Callers must pass the same list reference across turns.

### How to run

```bash
make support-bot            # from repo root — web UI at http://localhost:9001
make support-cli            # from repo root — CLI mode in terminal
```

`python -m backend.main` (not `python backend/main.py`) — the `-m` flag is required so package-relative imports inside `backend/` resolve correctly. The Makefile handles this automatically.

### What NOT to do

- Do not import provider SDKs (`anthropic`, `groq`, `google.genai`) outside `providers/`
- Do not add business logic to `main.py`
- Do not mix observability and chat logic in the same function
- Do not hardcode model names outside their respective provider file
- Do not key `COST_PER_TOKEN` by provider name — always by model name
- Do not swallow exceptions inside `stream()` — let `chat.py` handle fallback
- Do not run from inside `backend/` — always run from `AI_Bot/` root
- Do not commit `.env`

---

## Project 4: Claude Features Labs

**Stack:** Python, Jupyter, Anthropic SDK
**Location:** `ClaudeFeatures/`

A set of focused notebooks, each exercising one Claude API capability in isolation. Like `JupyterNotebook`, every notebook is self-contained and loads keys from the root `.env`. Runs on the shared root `.venv` and the **Python (AI_Learning .venv)** kernel.

### Notebooks

| Notebook | Feature |
|----------|---------|
| `001_thinking_complete.ipynb` | Extended thinking — `thinking` blocks and budget control |
| `002_images.ipynb` | Vision — sending images as content blocks |
| `003_pdf.ipynb` | PDF input — document understanding (`earth.pdf` sample) |
| `004_caching.ipynb` | Prompt caching — `cache_control` breakpoints and cost savings |
| `005_code_execution.ipynb` | Code execution tool — running model-generated code |

Supporting assets in the folder: `earth.pdf`, `images/`, `streaming.csv`.

### How to run

```bash
make claude-features        # from repo root — opens JupyterLab in browser
```

In VS Code / Cursor, select kernel **Python (AI_Learning .venv)**. Keys load from `AI_Learning/.env`.

---

## Project 5: MCP Chat

**Stack:** Python, Anthropic SDK, `mcp[cli]`, prompt-toolkit, managed by `uv`
**Location:** `MCP_Learning/`

A command-line chat application demonstrating the **Model Control Protocol (MCP)**: a Claude-powered CLI client talks to an MCP server over stdio, consuming the server's tools, resources, and prompts. Unlike the other projects, `MCP_Learning` manages its own `uv`-based environment (`pyproject.toml` + `uv.lock`, pinned to Python 3.13 via `.python-version`) while still reading keys from the single root `.env`.

### Architecture

```
Terminal              main.py (CliApp)            mcp_server.py (FastMCP)
  │                       │                              │
  │  > prompt             │  Claude.messages.create()    │
  │ ────────────────────► │  ── tools from server ──────►│  read_doc_contents
  │                       │                              │  edit_document
  │                       │  ◄── stdio (MCP) ────────────│  docs:// resources
  │ ◄── response ─────────│                              │  format prompt
```

The client (`main.py`) loads `ANTHROPIC_API_KEY` and `CLAUDE_MODEL` from `AI_Learning/.env`, then spawns the MCP server as a stdio subprocess (`uv run mcp_server.py` when `USE_UV=1`, else `python mcp_server.py`).

### File structure

```
MCP_Learning/
├── main.py              # Entry point — loads root .env, wires client + CLI
├── mcp_server.py        # FastMCP server — in-memory docs, tools, resources, prompts
├── mcp_client.py        # MCPClient — stdio session, tool/resource/prompt calls
├── core/
│   ├── claude.py        # Anthropic SDK wrapper (Claude service)
│   ├── chat.py          # Base chat loop
│   ├── cli_chat.py      # Chat with @document and /command support
│   ├── cli.py           # prompt-toolkit CLI app (autocomplete)
│   └── tools.py         # Tool execution helpers
├── pyproject.toml       # uv project definition
├── uv.lock              # Pinned dependency lockfile
└── .python-version      # Pins Python 3.13
```

### What the MCP server exposes

| Kind | Name | What it does |
|------|------|-------------|
| Tool | `read_doc_contents` | Read a document's contents by id |
| Tool | `edit_document` | Replace a string inside a document |
| Resource | `docs://documents` | List all document ids (JSON) |
| Resource | `docs://documents/{doc_id}` | Fetch one document's contents (text) |
| Prompt | `format` | Rewrite a document in Markdown via the edit tool |

Documents are an in-memory dict in `mcp_server.py` (`deposition.md`, `report.pdf`, `financials.docx`, etc.) — edit that dict to add more.

### CLI usage

| Input | Effect |
|-------|--------|
| Plain text | Chat with Claude |
| `@deposition.md` | Inject a document's contents into the query (Tab-completes) |
| `/format deposition.md` | Run a server-defined prompt/command (Tab-completes) |

### How to run

```bash
make mcp-install            # from repo root — uv sync the MCP_Learning env (once)
make mcp-chat               # from repo root — start the MCP Chat CLI
make mcp-inspect            # from repo root — launch the MCP Inspector web UI
```

`make install` runs `mcp-install` automatically as part of full setup.

### MCP Inspector

`make mcp-inspect` runs the server under the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) (`uv run mcp dev mcp_server.py --with-editable .`) — a browser UI for calling the server's tools, reading its resources, and running its prompts without Claude in the loop. It serves a proxy on `localhost:6277` and the UI on `localhost:6274`. Requires Node.js / `npx` on PATH.

### What NOT to do

- Do not add keys to a local `MCP_Learning/.env` — the root `AI_Learning/.env` is the single source of truth
- Do not share the root `.venv` — this project uses its own `uv`-managed environment
- Do not commit `.env`

---

## Common Patterns Across Projects

### API proxy pattern

The browser never holds an API key. Flask or FastAPI receives the request, adds the key server-side, proxies to the Anthropic API, and streams the response back. This is why both projects have a backend at all — a pure frontend app would expose the key.

### SSE over EventSource

All three projects use `fetch()` + `response.body.getReader()` instead of the browser's `EventSource` API. `EventSource` only supports GET requests and cannot send a JSON body — `fetch()` with manual `ReadableStream` parsing is the right tool for POST-initiated streams.

### Message history format

Universal format, shared across all providers. Each provider converts internally to its SDK format — callers never deal with SDK-specific types:

```python
[
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."},
]
```

Provider-specific conversions (internal to each `providers/*.py`):
- **Anthropic**: history passed as-is; system prompt via separate `system=` param
- **Groq**: system prompt prepended as `{"role": "system", ...}` to messages list
- **Gemini**: role `"assistant"` → `"model"`, content wrapped in `parts=[Part(text=...)]`

### Prefill for structured output

```python
add_assistant_message(messages, "```json")
response = chat(messages, stop_sequences=["```"])
data = json.loads(response)
```

Forcing the assistant to start with ` ```json ` and stopping at the closing fence gives reliable, parse-ready JSON without post-processing heuristics.

### Agentic tool loop

```python
while True:
    response = client.messages.create(..., tools=tools)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason != "tool_use":
        break
    tool_results = execute_tools(response)
    messages.append({"role": "user", "content": tool_results})
```

The loop runs until the model produces a final text response (`stop_reason == "end_turn"`). Each tool result is fed back as a user-role message, preserving the multi-turn history.

### Error handling — fail-fast providers

In `AI_Bot`, provider `stream()` raises exceptions on failure — never swallows them. `chat.py` catches, logs the failed attempt with full error detail, then tries the next provider. This makes fallback explicit and observable rather than silent.

---

## Running on Windows

The Python code (Flask, FastAPI, all providers, notebooks) is fully cross-platform and works on Windows. The `Makefile` and the `DYLD_LIBRARY_PATH` workaround are macOS-only. On Windows, Python from python.org installs without any such issues.

Two options:

---

### Option A — WSL (recommended)

Install [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install), then clone the repo inside WSL. Everything works exactly as on macOS:

```bash
cp .env.example .env    # fill in your keys
make install
make chatbot            # http://localhost:9000
make support-bot        # http://localhost:9001
make support-cli
make jupyter
make claude-features
make mcp-chat
```

No extra setup needed — `make`, Python, `uv`, and all paths resolve identically inside WSL.

---

### Option B — Native Windows (PowerShell)

No `make` or `DYLD_LIBRARY_PATH` needed. Run commands directly in PowerShell from the `AI_Learning\` root.

**One-time setup:**

```powershell
cp .env.example .env    # fill in your keys

python -m venv .venv
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m ipykernel install --user --name ai-learning-venv `
    --display-name "Python (AI_Learning .venv)"
```

**Run Claude Chatbot** → http://localhost:9000

```powershell
cd Claude_Chatbot\backend
..\..\venv\Scripts\python app.py
```

**Run AI Support Bot — web UI** → http://localhost:9001

```powershell
cd AI_Bot
..\venv\Scripts\uvicorn backend.api:app --reload --port 9001
```

**Run AI Support Bot — CLI**

```powershell
cd AI_Bot
..\venv\Scripts\python -m backend.main
```

**Run JupyterLab** (JupyterNotebook or ClaudeFeatures)

```powershell
cd JupyterNotebook        # or: cd ClaudeFeatures
..\venv\Scripts\jupyter lab
```

In VS Code / Cursor: select kernel **Python (AI_Learning .venv)** when opening any notebook.

**Run MCP Chat** (uses its own `uv` environment, not the root `.venv`)

```powershell
# Install uv once: https://docs.astral.sh/uv/getting-started/installation/
cd MCP_Learning
uv sync
uv run main.py
```

**Stop any running server:** `Ctrl+C` in the terminal where it is running.

