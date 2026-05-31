import anthropic as anthropic_sdk
from typing import Generator
from backend.config import config
from backend.prompts import SYSTEM_PROMPT

MODEL_SIMPLE  = "claude-haiku-4-5"   # fastest, cheapest — $1/$5 per MTok
MODEL_COMPLEX = "claude-opus-4-7"    # most capable    — $5/$25 per MTok

_client = anthropic_sdk.Anthropic(api_key=config["ANTHROPIC_API_KEY"])


def stream_iter(history: list, complexity: str = "complex") -> Generator:
    """Pure generator — yields text chunks, then a final metadata dict.

    Callers check isinstance(chunk, dict) to detect the final metadata item.
    No side effects (no printing) — caller decides what to do with chunks.
    """
    model = MODEL_SIMPLE if complexity == "simple" else MODEL_COMPLEX
    with _client.messages.stream(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history,
    ) as s:
        for text in s.text_stream:
            yield text
        usage = s.get_final_message().usage
        yield {"model": model, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}


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
