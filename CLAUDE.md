# AI_Learning — Claude Guide

Hands-on AI engineering projects using the Anthropic API. Three subprojects at different levels of complexity.

## Structure

```
AI_Learning/
├── .env                 # All API keys — single source of truth, never commit
├── .env.example         # Template — copy to .env and fill in keys
├── .gitignore
├── Claude_Chatbot/      # Minimal chatbot — Flask + Anthropic SDK, single-file UI
├── AI_Bot/      # Production-grade multi-provider support bot with classifiers
└── JupyterNotebook/     # AI engineering labs — prompt evals, RAG pipeline, tool use
```

## Subprojects at a glance

| Project | Stack | What it teaches |
| --- | --- | --- |
| `Claude_Chatbot/` | Flask, Anthropic SDK, HTML/JS | API proxy pattern, SSE streaming, model picker UI |
| `AI_Bot/` | FastAPI, multi-provider (Anthropic + Groq + Gemini), HTML/JS | Strategy pattern, classifier routing, cost-aware provider fallback, observability |
| `JupyterNotebook/` | Jupyter, Anthropic SDK, VoyageAI | Prompt engineering, RAG from scratch, tool use, prompt evals |

## Learning progression

1. `Claude_Chatbot` — simplest entry point: one file, one provider, one endpoint
2. `JupyterNotebook` — explore the API interactively, understand embeddings and tool use
3. `AI_Bot` — production patterns: multi-provider, classification, streaming, cost tracking

## Subproject documentation

Each subproject's `README.md` is the source of truth for architecture, running instructions, design patterns, conventions, SDK gotchas, and developer notes:

- [`Claude_Chatbot/README.md`](Claude_Chatbot/README.md) — architecture diagram, API endpoints, SSE events, env vars, what NOT to do
- [`AI_Bot/README.md`](AI_Bot/README.md) — step progression, SRP/OCP principles, provider contract, classifier routing, SDK gotchas, cost tracking
- [`JupyterNotebook/README.md`](JupyterNotebook/README.md) — conventions, all four series, common patterns, adding new notebooks

## Conventions

- Each subproject has its own `venv` — never share environments across projects.
- A single `.env` at the repo root (`AI_Learning/.env`) supplies API keys to all subprojects — never commit it.
- No emojis in code or prose.

## When starting any task here

1. Read the target subproject's `README.md`.
2. Activate that subproject's `.venv` before running anything.
3. Confirm `AI_Learning/.env` at the repo root has the required keys for that subproject.
