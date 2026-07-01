# app/agent/runner.py
# ─────────────────────────────────────────────────────────────────────────────
# Calls the Gemini Interactions API and returns parsed steps + final answer.
# This is the only place in the codebase that talks to the LLM.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Any

from fastapi import HTTPException

from app.client import get_client
from app.config import GENERATION_CONFIG, TOOLS
from app.agent.parser import extract_final_answer, parse_step
from app.models.schemas import AgentStep, ChatResponse


def run_agent(message: str, model: str) -> ChatResponse:
    """
    Send `message` to the Gemini agent and return the full ChatResponse.

    Flow inside the Gemini API:
      1. Your message is wrapped in a user_input step.
      2. The LLM may call tools (google_search) one or more times.
      3. Each tool call produces a tool_result step.
      4. The LLM reasons and finally produces a model_output step.
      5. We parse every step and return them all.
    """
    try:
        interaction = get_client().interactions.create(
            model=model,
            input=message,
            tools=TOOLS,
            generation_config=GENERATION_CONFIG,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Gemini API error: {exc}"
        ) from exc

    raw_steps: list[Any] = interaction.steps or []

    parsed_steps: list[AgentStep] = [
        parse_step(i, step) for i, step in enumerate(raw_steps)
    ]

    flow_summary: list[str] = [
        f"[{s.step_index}] {s.role.upper():5} → {s.label}"
        for s in parsed_steps
    ]

    return ChatResponse(
        question=message,
        model_used=model,
        total_steps=len(parsed_steps),
        agent_flow_summary=flow_summary,
        steps=parsed_steps,
        final_answer=extract_final_answer(raw_steps),
    )
