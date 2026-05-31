"""Claude Chatbot — Flask backend (Anthropic Python SDK edition).

Two responsibilities:
  1. Serve the static frontend (../frontend) at /
  2. Proxy two endpoints to the Anthropic API via the official SDK:
       GET  /api/models  -> anthropic.Anthropic().models.list()
       POST /api/chat    -> anthropic.Anthropic().messages.create(...)

Why a proxy? So the API key never reaches the browser.

Run:
  pip install -r requirements.txt
  python app.py                 # reads .env by default
  python app.py --port 9000     # override port
  open http://localhost:9000
"""

import argparse
import os
import logging
from pathlib import Path

import json

import anthropic
import httpx
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

# Load .env from the repo root (AI_Learning/). Path: backend/ -> Claude_Chatbot/ -> AI_Learning/
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DEFAULT_PORT = 9000

# Frontend lives one level up from backend/
FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("chatbot")

app = Flask(__name__, static_folder=None)  # we manage static serving manually


def _verify_ssl() -> bool:
    """Whether to verify TLS certs when calling Anthropic.

    Defaults to True. Set VERIFY_SSL=false in .env only if you're behind
    a TLS-intercepting proxy (corporate network, local sandbox). Never
    turn this off in production.
    """
    return os.environ.get("VERIFY_SSL", "true").strip().lower() not in (
        "false", "0", "no", "off",
    )


def _get_client() -> anthropic.Anthropic | None:
    """Build an Anthropic SDK client at request time.

    Doing this per-request (rather than a module-level singleton) means:
      - we re-read ANTHROPIC_API_KEY on every call, so you can set it
        after the server boots without a restart;
      - we return None gracefully if the key is missing, so the caller
        can emit a friendly JSON error instead of a crash.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    # Use a custom httpx client only if we need to disable TLS verification
    # (e.g. behind a corporate MITM proxy). Otherwise, let the SDK manage it.
    if not _verify_ssl():
        return anthropic.Anthropic(
            api_key=api_key,
            http_client=httpx.Client(verify=False),
        )
    return anthropic.Anthropic(api_key=api_key)


def _no_key_error():
    return jsonify(error={"type": "proxy_error",
                          "message": "ANTHROPIC_API_KEY not set on the server"}), 401


def _sdk_error(e: anthropic.APIError):
    """Normalize SDK errors to the same shape Anthropic's API returns,
    so the frontend's existing `data.error.message` path keeps working."""
    status = getattr(e, "status_code", 500) or 500
    body = getattr(e, "body", None)
    if isinstance(body, dict) and "error" in body:
        return jsonify(body), status
    return jsonify(error={"type": e.__class__.__name__, "message": str(e)}), status


# -------------------------------------------------------------------- routes

@app.get("/api/models")
def list_models():
    """List models via the SDK, returning the same JSON shape as /v1/models
    so the frontend doesn't need to change."""
    client = _get_client()
    if client is None:
        return _no_key_error()
    try:
        page = client.models.list(limit=100)
    except anthropic.APIError as e:
        return _sdk_error(e)
    except Exception as e:  # network / TLS / etc
        return jsonify(error={"type": "proxy_error", "message": str(e)}), 502

    # SyncPage objects expose `.data` already, but model_dump gives us a
    # plain dict that matches the raw API response exactly.
    return jsonify(page.model_dump()), 200


@app.post("/api/chat")
def chat():
    """Create a message via the SDK. The frontend sends the same JSON the
    raw /v1/messages endpoint expects (model, messages, max_tokens,
    optional system, ...), and we forward those kwargs to the SDK."""
    client = _get_client()
    if client is None:
        return _no_key_error()

    payload = request.get_json(silent=True) or {}

    # Required fields
    model = payload.get("model")
    messages = payload.get("messages")
    max_tokens = payload.get("max_tokens", 1024)
    if not model or not isinstance(messages, list):
        return jsonify(error={"type": "invalid_request_error",
                              "message": "`model` and `messages` are required"}), 400

    use_stream = bool(payload.get("stream", False))

    kwargs = {"model": model, "messages": messages, "max_tokens": int(max_tokens)}
    system = payload.get("system")
    if isinstance(system, str) and system.strip():
        kwargs["system"] = system
    for opt in ("temperature", "top_p", "top_k", "stop_sequences", "metadata", "tools"):
        if opt in payload:
            kwargs[opt] = payload[opt]

    if use_stream:
        def generate():
            try:
                with client.messages.stream(**kwargs) as stream:
                    for text in stream.text_stream:
                        yield f"data: {json.dumps({'type': 'delta', 'text': text})}\n\n"
                    final = stream.get_final_message()
                    yield f"data: {json.dumps({'type': 'done', 'message': final.model_dump()})}\n\n"
            except anthropic.APIError as e:
                body = getattr(e, "body", None)
                err = (body["error"] if isinstance(body, dict) and "error" in body
                       else {"type": e.__class__.__name__, "message": str(e)})
                yield f"data: {json.dumps({'type': 'error', 'error': err})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': {'type': 'proxy_error', 'message': str(e)}})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    try:
        resp = client.messages.create(**kwargs)
    except anthropic.APIError as e:
        return _sdk_error(e)
    except Exception as e:
        return jsonify(error={"type": "proxy_error", "message": str(e)}), 502

    return jsonify(resp.model_dump()), 200


# ---------------------------------------------------------------- static UI

@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename: str):
    if filename.startswith("api/"):
        return jsonify(error={"type": "not_found", "message": "unknown endpoint"}), 404
    return send_from_directory(FRONTEND_DIR, filename)


# ---------------------------------------------------------------------- main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Claude Chatbot backend")
    parser.add_argument("--port", "-p", type=int, default=None,
                        help=f"port to listen on (default: $PORT or {DEFAULT_PORT})")
    parser.add_argument("--host", default="127.0.0.1",
                        help="host to bind (default: 127.0.0.1)")
    parser.add_argument("--insecure", action="store_true",
                        help="skip TLS verification when calling Anthropic "
                             "(only for proxied/sandboxed environments)")
    args = parser.parse_args()

    if args.insecure:
        os.environ["VERIFY_SSL"] = "false"

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("ANTHROPIC_API_KEY is not set. /api/* calls will fail until you set it.")
    if not _verify_ssl():
        log.warning("TLS verification is DISABLED — only use this in trusted local networks.")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    if not FRONTEND_DIR.exists():
        log.warning("Frontend dir not found: %s", FRONTEND_DIR)
    else:
        log.info("Serving frontend from: %s", FRONTEND_DIR)

    # Precedence: --port  >  $PORT  >  DEFAULT_PORT
    port = args.port if args.port is not None else int(os.environ.get("PORT", DEFAULT_PORT))
    log.info("Claude Chatbot listening on http://%s:%d", args.host, port)
    app.run(host=args.host, port=port, debug=False)
