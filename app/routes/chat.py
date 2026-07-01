# app/routes/chat.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /chat — the main endpoint.
# Accepts a user question and returns the full agent reasoning chain.
#
# Conversation memory: pass `session_id` in subsequent requests to continue
# a conversation. The last 5 turns are injected as context into each request.
# Omit `session_id` for a stateless one-off question.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.agent.runner import run_agent
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory conversation store: session_id → list of {user, assistant} turns.
# Resets on server restart — production apps use Redis or a database.
_conversations: dict[str, list[dict]] = {}
MAX_HISTORY_TURNS = 5


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the AI agent — see the full internal flow",
    tags=["Agent"],
)
async def chat(request: ChatRequest) -> ChatResponse:
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

    **Conversation memory:** include `session_id` from the previous response to
    continue a multi-turn conversation. The last 5 turns are used as context.
    Omit `session_id` (or set it to `null`) for a stateless one-off question.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    # Use the caller's session_id, or create a new one for this conversation.
    session_id = request.session_id or str(uuid4())
    history = _conversations.get(session_id, [])

    logger.info("▶  message=%r  session=%s  history=%d turns",
                request.message[:80], "new" if not request.session_id else session_id[:8], len(history))

    # Inject prior turns so the LLM has context for follow-up questions.
    if history:
        turns = "\n".join(
            f"User: {t['user']}\nAssistant: {t['assistant']}"
            for t in history[-MAX_HISTORY_TURNS:]
        )
        full_message = (
            f"Previous conversation:\n{turns}\n\n"
            f"Current question: {request.message}"
        )
    else:
        full_message = request.message

    # run_agent calls the Gemini SDK synchronously — run in a thread to avoid
    # blocking the event loop.
    response = await asyncio.to_thread(run_agent, full_message, request.model)

    # Return the original (unaugmented) question and attach the session_id.
    response.question = request.message
    response.session_id = session_id

    logger.info("✓  %d steps  |  answer: %s",
                response.total_steps, response.final_answer[:100])

    # Persist this turn and cap history length.
    _conversations.setdefault(session_id, []).append(
        {"user": request.message, "assistant": response.final_answer}
    )
    _conversations[session_id] = _conversations[session_id][-MAX_HISTORY_TURNS:]

    return response
