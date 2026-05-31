# `.claude/` — AI_Learning Companion

Meta folder — shapes how Claude behaves across the three AI projects in this workspace.

## Layout

```
.claude/
├── README.md          # this file
├── settings.json      # permissions and tool config
└── memory/
    └── project-map.md # quick map of all three subprojects
```

## How to work in this repo

Each subproject is self-contained. When working on one:

1. Read its `CLAUDE.md` first — conventions, structure, gotchas are all there.
2. All paths, venvs, and env files are relative to the subproject root.
3. Run servers/notebooks from the subproject root (not from `AI_Learning/`).

## Quick reference

| Task | Where to start |
| --- | --- |
| Run the simple chatbot | `Claude_Chatbot/backend/` → `python app.py` |
| Run the support bot | `AI_Bot/` → `uvicorn backend.api:app --reload` |
| Open notebooks | `JupyterNotebook/` → select kernel `Python (JupyterNotebook .venv)` |
| Add a new AI provider | `AI_Bot/CLAUDE.md` → OCP section |
| Add a new notebook | `JupyterNotebook/CLAUDE.md` → "When adding a new notebook" |

