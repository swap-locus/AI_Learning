from pathlib import Path
from dotenv import dotenv_values

# Path: backend/ -> AI_Bot/ -> AI_Learning/ (repo root)
config = dotenv_values(Path(__file__).resolve().parent.parent.parent / ".env")

# Approximate cost per token in USD, keyed by model name.
# Keyed by model (not provider) because simple/complex tiers have very different costs.
# Source: official pricing pages (verified May 2026)
COST_PER_TOKEN: dict[str, dict[str, float]] = {
    # Anthropic — platform.claude.com/docs/en/about-claude/models/overview
    "claude-opus-4-7":   {"input":  5.00 / 1_000_000, "output": 25.00 / 1_000_000},
    "claude-haiku-4-5":  {"input":  1.00 / 1_000_000, "output":  5.00 / 1_000_000},
    # Groq — console.groq.com/docs/models
    "llama-3.3-70b-versatile": {"input": 0.59 / 1_000_000, "output": 0.79 / 1_000_000},
    "llama-3.1-8b-instant":    {"input": 0.05 / 1_000_000, "output": 0.08 / 1_000_000},
    # Gemini — ai.google.dev/gemini-api/docs/models
    "gemini-2.5-flash":      {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gemini-2.5-flash-lite": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
}

