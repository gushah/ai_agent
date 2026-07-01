# app/config.py
# ─────────────────────────────────────────────────────────────────────────────
# All constants for the AI agent.
# Change tool settings or generation parameters here — nowhere else.
# ─────────────────────────────────────────────────────────────────────────────

# Tools the LLM agent is allowed to call
TOOLS: list[dict] = [
    {"type": "google_search"},
]

# Parameters that control how the LLM generates text
GENERATION_CONFIG: dict = {
    "temperature": 1,
    "max_output_tokens": 8192,
    "top_p": 0.95,
}

# Default model used when the caller does not specify one
DEFAULT_MODEL = "gemini-2.5-flash"
