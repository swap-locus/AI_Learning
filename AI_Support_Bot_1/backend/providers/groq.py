from groq import Groq as GroqClient
from typing import Generator
from backend.config import config
from backend.prompts import SYSTEM_PROMPT

MODEL_SIMPLE  = "llama-3.1-8b-instant"
MODEL_COMPLEX = "llama-3.3-70b-versatile"

_client = GroqClient(api_key=config["GROQ_API_KEY"])


def stream_iter(history: list, complexity: str = "complex") -> Generator:
    """Pure generator — yields one text chunk then a final metadata dict.

    Groq SDK does not support stream_options, so we use a non-streaming call
    and yield the full response as a single chunk to keep the contract consistent.
    """
    model    = MODEL_SIMPLE if complexity == "simple" else MODEL_COMPLEX
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    response = _client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=messages,
        stream=False,
    )
    text          = response.choices[0].message.content or ""
    input_tokens  = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    yield text
    yield {"model": model, "input_tokens": input_tokens, "output_tokens": output_tokens}


def stream(history: list, complexity: str = "complex") -> tuple[str, int, int, str]:
    """CLI wrapper around stream_iter — prints response, returns collected tuple.

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
