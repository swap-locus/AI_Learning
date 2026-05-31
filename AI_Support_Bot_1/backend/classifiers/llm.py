import anthropic as anthropic_sdk
from groq import Groq as GroqClient

from backend.config import config
from backend.prompts import CLASSIFICATION_PROMPT
from backend.classifiers.base import ClassifierStrategy
from backend.classifiers.heuristic import HeuristicClassifier
from backend.classifiers.keyword import KeywordClassifier

# ---------------------------------------------------------------------------
# Clients (initialised once at import time)
# ---------------------------------------------------------------------------

_groq_client      = GroqClient(api_key=config["GROQ_API_KEY"])
_anthropic_client = anthropic_sdk.Anthropic(api_key=config["ANTHROPIC_API_KEY"])

# ---------------------------------------------------------------------------
# Pricing rationale — why Groq is primary, Anthropic Haiku is secondary
#
#   Model                       Input $/MTok   Output $/MTok   ~Cost/call*
#   llama-3.1-8b-instant        $0.05          $0.08           $0.0000175
#   claude-haiku-4-5            $1.00          $5.00           $0.000355
#
#   * ~350 input tokens, 1 output token per classification call
#   Groq is ~20x cheaper on input, ~62x cheaper on output.
#   Classification runs before every request — cost compounds at scale.
#   Haiku is kept as a reliable fallback, not the primary.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# No-API fallbacks (used when both LLM providers fail)
# ---------------------------------------------------------------------------

_heuristic_fallback = HeuristicClassifier()
_keyword_fallback   = KeywordClassifier()


class LLMClassifier(ClassifierStrategy):
    """Classifies query complexity using a small, cheap LLM API call.

    Fallback chain (in order):
      1. Groq llama-3.1-8b-instant  — cheapest (~$0.0000175/call), fastest (~200ms)
      2. Anthropic claude-haiku-4-5 — reliable fallback (~$0.000355/call, ~20x costlier)
      3. HeuristicClassifier        — structure-based, no API call
      4. KeywordClassifier          — keyword matching, no API call (last resort)

    Why Groq first?
      Groq is ~20x cheaper on input and ~62x cheaper on output vs Anthropic Haiku.
      Since classification runs before every request, cost compounds at scale.
    """

    def classify(self, user_input: str) -> str:
        # --- 1. Try Groq ---
        try:
            return self._call_groq(user_input)
        except Exception as e:
            print(f"[llm-classifier: groq failed ({e}) — trying anthropic haiku]")

        # --- 2. Try Anthropic Haiku ---
        try:
            return self._call_anthropic(user_input)
        except Exception as e:
            print(f"[llm-classifier: anthropic haiku failed ({e}) — falling back to heuristic]")

        # --- 3. HeuristicClassifier ---
        try:
            return _heuristic_fallback.classify(user_input)
        except Exception as e:
            print(f"[llm-classifier: heuristic failed ({e}) — falling back to keyword]")

        # --- 4. KeywordClassifier (last resort) ---
        return _keyword_fallback.classify(user_input)

    def _call_groq(self, user_input: str) -> str:
        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=5,
            temperature=0,
            messages=[
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {"role": "user",   "content": user_input},
            ],
        )
        result = response.choices[0].message.content.strip().lower()
        return self._validate(result, user_input, "groq")

    def _call_anthropic(self, user_input: str) -> str:
        response = _anthropic_client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=5,
            system=CLASSIFICATION_PROMPT,
            messages=[{"role": "user", "content": user_input}],
        )
        result = response.content[0].text.strip().lower()
        return self._validate(result, user_input, "anthropic-haiku")

    def _validate(self, result: str, user_input: str, source: str) -> str:
        """Ensure the model returned a valid label. Falls back to heuristic if not."""
        if result in ("simple", "complex"):
            return result
        print(f"[llm-classifier: {source} returned unexpected '{result}' — falling back to heuristic]")
        return _heuristic_fallback.classify(user_input)
