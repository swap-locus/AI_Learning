from google import genai
from google.genai import types
from typing import Generator
from backend.config import config
from backend.prompts import SYSTEM_PROMPT

MODEL_SIMPLE  = "gemini-2.5-flash-lite"  # fast, cheap  (2.0 deprecated June 2026)
MODEL_COMPLEX = "gemini-2.5-flash"       # capable      (2.0 deprecated June 2026)

_client = genai.Client(api_key=config["GEMINI_API_KEY"])


def stream_iter(history: list, complexity: str = "complex") -> Generator:
    """Pure generator — yields text chunks, then a final metadata dict.

    Gemini uses role "model" instead of "assistant" and wraps content in "parts".
    System prompt is passed via GenerateContentConfig.
    """
    model = MODEL_SIMPLE if complexity == "simple" else MODEL_COMPLEX
    gemini_contents = [
        types.Content(
            role="model" if msg["role"] == "assistant" else "user",
            parts=[types.Part(text=msg["content"])],
        )
        for msg in history
    ]
    response = _client.models.generate_content_stream(
        model=model,
        contents=gemini_contents,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    input_tokens = output_tokens = 0
    for chunk in response:
        text = chunk.text or ""
        if text:
            yield text
        if chunk.usage_metadata:
            input_tokens  = chunk.usage_metadata.prompt_token_count or 0
            output_tokens = chunk.usage_metadata.candidates_token_count or 0

    yield {"model": model, "input_tokens": input_tokens, "output_tokens": output_tokens}


def stream(history: list, complexity: str = "complex") -> tuple[str, int, int, str]:
    """CLI wrapper around stream_iter — prints chunks, returns collected tuple.

    Returns: (reply, input_tokens, output_tokens, model_used)
    """
    reply = ""
    meta  = {}
    for chunk in stream_iter(history, complexity):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
            reply += chunk
        else:
            meta = chunk
    return reply, meta["input_tokens"], meta["output_tokens"], meta["model"]
