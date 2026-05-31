from . import anthropic, groq, gemini

# Provider registry — tried in order by chat.py, first success wins.
#
# Each entry: (provider_name, provider_module)
# provider_module must expose: MODEL_SIMPLE, MODEL_COMPLEX, stream(history, complexity)
#
# To add a new provider:
#   1. Create backend/providers/<name>.py with MODEL_SIMPLE, MODEL_COMPLEX, stream()
#   2. Import and add one entry here — nothing else changes.
PROVIDERS = [
    ("anthropic", anthropic),
    ("groq",      groq),
    ("gemini",    gemini),
]
