---
name: ai-learning-project-map
description: Quick map of all three AI_Learning subprojects — stack, entry points, key files
metadata:
  type: project
---

Three subprojects under AI_Learning/:

**Shared `.env`** — single `AI_Learning/.env` at repo root supplies keys to all subprojects. No project-level `.env` files.

**Claude_Chatbot** — minimal Flask + Anthropic SDK chatbot
- Entry point: `backend/app.py` → run from `backend/`, `python app.py` (port 9000)
- Frontend: `frontend/index.html` (served statically by Flask)
- Key feature: API proxy so browser never sees the key, SSE streaming
- Needs: `ANTHROPIC_API_KEY`

**AI_Bot** — multi-provider support bot with classifier routing
- Entry point: `uvicorn backend.api:app --reload` from `AI_Bot/` root
- CLI: `python -m backend.main` (must use `-m` flag for package imports)
- Frontend: `frontend/` (served by FastAPI)
- Key features: Strategy pattern classifiers (keyword/heuristic/LLM), provider fallback (Anthropic → Groq → Gemini), cost tracking, SSE
- Needs: `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`

**JupyterNotebook** — AI engineering labs
- Shared venv: `JupyterNotebook/.venv`, kernel name: `jupyternotebook-venv`
- Needs: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY` (from root `.env`, found via `find_dotenv()`)
- Four series: PromptEvaluation, Prompt_Techniques, RAG_Agentic_Search, ToolsUse

