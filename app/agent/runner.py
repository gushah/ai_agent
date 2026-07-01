# app/agent/runner.py
# ─────────────────────────────────────────────────────────────────────────────
# Calls the Gemini Interactions API and returns parsed steps + final answer.
# This is the only place in the codebase that talks to the LLM.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Any

import logging

from fastapi import HTTPException

from app.client import get_client
from app.config import GENERATION_CONFIG, TOOLS
from app.agent.parser import extract_final_answer, parse_step
from app.models.schemas import AgentStep, ChatResponse

logger = logging.getLogger(__name__)


def run_agent(message: str, model: str, tools: list | None = None) -> ChatResponse:
    """
    Send `message` to the Gemini agent and return the full ChatResponse.

    Args:
        tools: Override the default tools list. If None, uses config.TOOLS
               (google_search only). Pass custom tools to add MCP servers.

    Flow inside the Gemini API:
      1. Your message is wrapped in a user_input step.
      2. The LLM may call tools (google_search, mcp_server, etc.) one or more times.
      3. Each tool call produces a tool_result step.
      4. The LLM reasons and finally produces a model_output step.
      5. We parse every step and return them all.
    """
    active_tools = tools if tools is not None else TOOLS
    logger.info("Calling Gemini (%s) ...", model)
    try:
        interaction = get_client().interactions.create(
            model=model,
            input=message,
            tools=active_tools,
            generation_config=GENERATION_CONFIG,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Gemini API error: {exc}"
        ) from exc

    raw_steps: list[Any] = interaction.steps or []
    logger.info("Got %d steps from Gemini", len(raw_steps))

    parsed_steps: list[AgentStep] = []
    for i, raw_step in enumerate(raw_steps):
        step = parse_step(i, raw_step)
        parsed_steps.append(step)

        extra = ""
        if step.step_type == "google_search_call":
            queries = step.data.get("queries", [])
            extra = f"  queries={queries}"
        elif step.step_type == "google_search_result":
            count = len(step.data.get("results", []))
            extra = f"  ({count} result(s))"
        elif step.step_type in ("model_output", "thought"):
            text = step.data.get("text", "")
            extra = f"  ({len(text)} chars)"
        elif step.step_type in ("mcp_server_tool_call", "function_call"):
            extra = f"  tool={step.data.get('name', '')}"

        logger.info("  [%d] %-6s → %s%s", i, step.role, step.label, extra)

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
