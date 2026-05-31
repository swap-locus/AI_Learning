import uuid
import time
from datetime import datetime
from typing import Generator

from backend.providers import PROVIDERS
from backend.observability import RequestLog, SessionStats
from backend.classifiers import get_classifier
from backend.config import COST_PER_TOKEN

_classifier = get_classifier()


def chat_iter(user_input: str, history: list, stats: SessionStats) -> Generator:
    """Generator version of chat for API / SSE streaming.

    Yields dicts that map directly to SSE event payloads:
      {"type": "routing",  "complexity": "simple"|"complex"}
      {"type": "chunk",    "text": "..."}
      {"type": "done",     "provider": ..., "model": ..., ...}
      {"type": "provider_error", "provider": ..., "error": "..."}
      {"type": "fatal",    "error": "all providers failed"}

    History is mutated in-place (same contract as chat()).
    """
    complexity = _classifier.classify(user_input)
    history.append({"role": "user", "content": user_input})
    yield {"type": "routing", "complexity": complexity}

    is_fallback = False
    for provider_name, provider in PROVIDERS:
        start = time.time()
        try:
            reply = ""
            meta: dict = {}
            for chunk in provider.stream_iter(history, complexity):
                if isinstance(chunk, str):
                    reply += chunk
                    yield {"type": "chunk", "text": chunk}
                else:
                    meta = chunk

            latency_ms = (time.time() - start) * 1000
            model_used    = meta["model"]
            input_tokens  = meta["input_tokens"]
            output_tokens = meta["output_tokens"]
            cost_rates    = COST_PER_TOKEN.get(model_used, {"input": 0, "output": 0})
            cost = (
                input_tokens  * cost_rates["input"] +
                output_tokens * cost_rates["output"]
            )
            stats.add(RequestLog(
                request_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now().isoformat(),
                provider=provider_name,
                model=model_used,
                complexity=complexity,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=cost,
                is_fallback=is_fallback,
            ))
            history.append({"role": "assistant", "content": reply})
            yield {
                "type": "done",
                "provider": provider_name,
                "model": model_used,
                "complexity": complexity,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms),
                "cost_usd": round(cost, 6),
            }
            return

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            stats.add(RequestLog(
                request_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now().isoformat(),
                provider=provider_name,
                model=provider.MODEL_SIMPLE if complexity == "simple" else provider.MODEL_COMPLEX,
                complexity=complexity,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                estimated_cost_usd=0.0,
                is_fallback=is_fallback,
                error=str(e),
            ))
            yield {"type": "provider_error", "provider": provider_name, "error": str(e)}
            is_fallback = True

    history.pop()
    yield {"type": "fatal", "error": "all providers failed"}


def chat(user_input: str, history: list, stats: SessionStats) -> None:
    """Orchestrate a single chat turn across providers.

    1. Classify the query as simple or complex.
    2. Try each provider in order — first success wins.
    3. Log every attempt (success or failure) into SessionStats.
    4. If all providers fail, pop the user message from history to keep it clean.
    """
    complexity = _classifier.classify(user_input)
    history.append({"role": "user", "content": user_input})
    print(f"\n[routing: {complexity}]")

    is_fallback = False
    for provider_name, provider in PROVIDERS:
        start = time.time()
        try:
            reply, input_tokens, output_tokens, model_used = provider.stream(history, complexity)
            latency_ms = (time.time() - start) * 1000
            cost_rates = COST_PER_TOKEN.get(model_used, {"input": 0, "output": 0})
            cost = (
                input_tokens  * cost_rates["input"] +
                output_tokens * cost_rates["output"]
            )
            stats.add(RequestLog(
                request_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now().isoformat(),
                provider=provider_name,
                model=model_used,
                complexity=complexity,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=cost,
                is_fallback=is_fallback,
            ))
            print(f"\n[{provider_name}/{model_used} | {complexity} | in={input_tokens} out={output_tokens} | {latency_ms:.0f}ms | ${cost:.5f}]\n")
            history.append({"role": "assistant", "content": reply})
            return

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            stats.add(RequestLog(
                request_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now().isoformat(),
                provider=provider_name,
                model=provider.MODEL_SIMPLE if complexity == "simple" else provider.MODEL_COMPLEX,
                complexity=complexity,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                estimated_cost_usd=0.0,
                is_fallback=is_fallback,
                error=str(e),
            ))
            print(f"\n[{provider_name} failed — trying next]\n")
            is_fallback = True

    history.pop()
    print("[all providers failed]\n")
