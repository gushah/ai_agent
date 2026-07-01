# app/routes/chat.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /chat — the main endpoint.
# Accepts a user question and returns the full agent reasoning chain.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException

from app.agent.runner import run_agent
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the AI agent — see the full internal flow",
    tags=["Agent"],
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the Gemini AI agent.

    Returns **every internal step** the agent took:

    | step_type | role | meaning |
    |---|---|---|
    | `user_input` | user | your question entered the system |
    | `thought` | agent | LLM's internal reasoning (hidden from users) |
    | `google_search_call` | agent | LLM called Google Search |
    | `google_search_result` | tool | search results returned to LLM |
    | `model_output` | agent | LLM's final synthesised answer |

    Use `agent_flow_summary` for a quick one-liner overview of the chain,
    and `steps` for full detail on each step.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    return run_agent(message=request.message, model=request.model)
