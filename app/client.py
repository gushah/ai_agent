# app/client.py
# ─────────────────────────────────────────────────────────────────────────────
# Gemini SDK client — created once (singleton) on first use.
# Importing this module never raises an error even if the API key is missing;
# the error is raised only when get_client() is actually called at request time.
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Any

from fastapi import HTTPException
from google import genai

_client: Any = None


def get_client() -> Any:
    """Return the shared Gemini client, creating it on first call."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY environment variable is not set.",
            )
        _client = genai.Client(api_key=api_key)
    return _client
