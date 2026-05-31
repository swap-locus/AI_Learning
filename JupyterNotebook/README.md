# JupyterNotebook — AI Engineering Labs

Hands-on notebooks for learning the Anthropic API and building AI systems from scratch. Four self-contained series, each building progressively. All notebooks share a single `.venv`.

---

## Setup

**From repo root (recommended):**
```bash
make install        # one-time — creates root .venv, installs all deps, registers kernel
make jupyter        # opens JupyterLab in browser
```

**Manual (no Makefile):**
```bash
cd JupyterNotebook/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name ai-learning-venv \
    --display-name "Python (AI_Learning .venv)"
```

API keys come from `AI_Learning/.env` at the repo root — `load_dotenv(find_dotenv())` searches upward automatically. Required keys: `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` (RAG series only).

In VS Code / Cursor: always select kernel **Python (AI_Learning .venv)** before running any notebook.

---

## Conventions

- **No framework dependencies** — `VectorIndex`, `BM25Index`, `Retriever` use only Python stdlib + `math`. Internals are fully visible.
- **Self-contained notebooks** — common helpers (`add_user_message`, `add_assistant_message`, `chat`) are copied into each notebook. Never import from outside; each notebook must run standalone.
- **Prefill for structured output** — `add_assistant_message(messages, "```json")` + `stop_sequences=["```"]` forces reliable JSON without post-processing.
- **Agentic tool loop** — `while True` → call API → check `stop_reason == "tool_use"` → run tools → feed results back → repeat until `end_turn`.
- **Batch embeddings** — always use `add_documents()` instead of looping `add_document()` to avoid VoyageAI rate limits.

---

## Models Used

| Series | Model |
|--------|-------|
| PromptEvaluation | `claude-haiku-4-5` |
| Prompt_Techniques | `claude-haiku-4-5` |
| RAG_Agentic_Search | VoyageAI `voyage-3-large` (embeddings only) |
| ToolsUse | `claude-haiku-4-5`, `claude-sonnet-4-5`, `claude-opus-4-7` |

---

## Series 1 — Prompt Evaluation (`PromptEvaluation/`)

Basic LLM-as-judge eval pipeline.

| Notebook | What it does |
|----------|-------------|
| `001_prompt_evals.ipynb` | Generates an AWS-task dataset, runs a prompt against each case, grades with LLM + syntax validation |

**Key concepts:** prefill technique (`add_assistant_message`), stop sequences, LLM-as-judge pattern, syntax validators (`ast.parse`, `json.loads`, `re.compile`).

---

## Series 2 — Prompt Techniques (`Prompt_Techniques/`)

Demonstrates how prompt quality directly affects eval scores.

| Notebook | What it does |
|----------|-------------|
| `001_prompting.ipynb` | Full `PromptEvaluator` class — concurrent execution with `ThreadPoolExecutor`, HTML report with score badges. Naive prompt → avg score **4.67** |
| `002_prompting_completed.ipynb` | Same evaluator, improved prompt with XML tags + `<sample_input>/<ideal_output>` examples → avg score **7.0** |

**Key concepts:** `PromptEvaluator` class, `render()` template engine, `concurrent.futures.ThreadPoolExecutor`, HTML report generation, mandatory vs. secondary grading criteria.

**Progression:** `001` → `002` is a concrete before/after of prompt engineering impact (+2.33 points).

---

## Series 3 — RAG Agentic Search (`RAG_Agentic_Search/`)

Builds a full hybrid RAG pipeline from scratch — no external vector DB libraries. Knowledge base: `report.md` (synthetic annual report).

| Notebook | What it builds |
|----------|---------------|
| `001_chunking.ipynb` | Three chunking strategies: by characters (with overlap), by sentences (with overlap), by markdown `##` sections |
| `002_embeddings.ipynb` | VoyageAI client + `generate_embedding()` using `voyage-3-large` |
| `003_vectordb.ipynb` | `VectorIndex` — cosine and Euclidean distance, `add_vector`, `add_document`, `add_documents`, `search` |
| `004_bm25.ipynb` | `BM25Index` — tokenizer, IDF calculation, BM25 scoring formula, score normalization |
| `005_hybrid.ipynb` | `Retriever` — combines `VectorIndex` + `BM25Index` with Reciprocal Rank Fusion (RRF, k=60) |

**Key concepts:** chunking strategies, dense vs. sparse retrieval, cosine similarity, BM25 (k1=1.5, b=0.75, IDF), RRF score fusion `1/(k+rank)`, `SearchIndex` Protocol.

**Progression:** `001` → `005` builds layer by layer into a production-style hybrid retriever.

---

## Series 4 — Tool Use (`ToolsUse/`)

Progressive series on Anthropic tool use — from basic calling to built-in Claude tools.

| Notebook | What it demonstrates |
|----------|---------------------|
| `001_tools.ipynb` | Basic tool schema, single tool call, manual `tool_result` message construction |
| `001_tools_007.ipynb` | Multi-tool agentic loop: `run_tools()` dispatcher, multi-step chains (date calc → set reminder) |
| `003_FineGrained_ToolCalling.ipynb` | Beta `fine-grained-tool-streaming-2025-05-14`, `tool_choice`, streaming `input_json_delta` |
| `005_text_editor_tool.ipynb` | Built-in `str_replace_based_edit_tool`, custom `TextEditorTool` (view / str_replace / create / insert / undo_edit) with path validation and auto-backup |
| `006_web_search_complete.ipynb` | Built-in `web_search_20250305` with `max_uses` and `allowed_domains` filter |

**Key concepts:** tool schema (`input_schema`), `tool_use` / `tool_result` message flow, agentic loop (`stop_reason == "tool_use"`), `tool_choice`, streaming `input_json_delta` deltas, built-in tools.

---

## Common Patterns

```python
# Client setup
from dotenv import load_dotenv, find_dotenv
from anthropic import Anthropic
load_dotenv(find_dotenv())
client = Anthropic()

# Message helpers (copied into each notebook)
def add_user_message(messages, text): messages.append({"role": "user", "content": text})
def add_assistant_message(messages, text): messages.append({"role": "assistant", "content": text})

# Prefill for structured output
add_assistant_message(messages, "```json")
response = chat(messages, stop_sequences=["```"])
data = json.loads(response)

# Agentic tool loop
while True:
    response = client.messages.create(..., tools=tools)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason != "tool_use":
        break
    tool_results = run_tools(response)
    messages.append({"role": "user", "content": tool_results})
```

---

## Adding a New Notebook

1. Place it in the appropriate series folder
2. Copy common helpers from a sibling notebook — do not import from outside
3. Start with `load_dotenv(find_dotenv())` and client setup as the first cell; select **Python (AI_Learning .venv)** kernel
4. Add a row to the relevant series table in this README

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named pip` | `.venv/bin/python -m ensurepip --upgrade`, then restart kernel |
| `No module named dotenv` | Wrong kernel selected — pick **Python (AI_Learning .venv)** |
| VoyageAI rate limit errors | Use `add_documents()` batch method instead of looping `add_document()` |
| `No module named voyageai` | `.venv/bin/python -m pip install voyageai`, then restart kernel |
| Keys not loading | Confirm `AI_Learning/.env` exists with `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` |
