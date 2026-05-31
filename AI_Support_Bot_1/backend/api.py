"""FastAPI application — HTTP + SSE interface for the AI Support Bot.

Endpoints:
  POST /chat          — SSE stream of chat events
  DELETE /session     — clear a session's history
  GET  /health        — liveness probe

SSE event format (newline-delimited, each prefixed with "data: "):
  {"type": "routing",        "complexity": "simple"|"complex"}
  {"type": "chunk",          "text": "..."}
  {"type": "done",           "provider": ..., "model": ..., "complexity": ...,
                              "input_tokens": ..., "output_tokens": ...,
                              "latency_ms": ..., "cost_usd": ...}
  {"type": "provider_error", "provider": ..., "error": "..."}
  {"type": "fatal",          "error": "all providers failed"}
"""

import json
from typing import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.chat import chat_iter
from backend.observability import SessionStats

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Support Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # fine for local dev; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend from /  (must be mounted AFTER routes are defined)
# Mounted at the end of this file.

# ---------------------------------------------------------------------------
# In-memory session store  {session_id -> {history, stats}}
# ---------------------------------------------------------------------------

_sessions: dict[str, dict] = {}


def _get_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {"history": [], "stats": SessionStats()}
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.delete("/session")
async def clear_session(session_id: str = "default"):
    """Reset conversation history for a session."""
    if session_id in _sessions:
        _sessions[session_id]["history"].clear()
    return {"cleared": session_id}


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Stream a chat response as Server-Sent Events."""
    session = _get_session(req.session_id)

    def _sse_generator() -> Generator[str, None, None]:
        for event in chat_iter(req.message, session["history"], session["stats"]):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable Nginx buffering in prod
        },
    )


# ---------------------------------------------------------------------------
# Static frontend files — served at /
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
