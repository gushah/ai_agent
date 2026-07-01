# app/routes/multi_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /multi-agent-chat — Multi-Agent Orchestration endpoint.
#
# Runs 3 specialist agents in sequence:
#   1. Research Agent  — Google Search (live internet)
#   2. Knowledge Agent — ChromaDB (your private knowledge base)
#   3. Synthesizer     — combines both outputs into one final answer
#
# See app/agent/multi_runner.py for the full orchestration logic.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter

from app.models.schemas import ChatRequest, MultiAgentResponse
from app.agent.multi_runner import run_multi_agent

router = APIRouter(tags=["Multi-Agent"])


@router.post(
    "/multi-agent-chat",
    response_model=MultiAgentResponse,
    summary="Multi-Agent: 3 specialist agents collaborate to answer your question",
)
async def multi_agent_chat(request: ChatRequest):
    """
    Demonstrates the **multi-agent orchestration pattern**.

    Three specialist agents run in sequence. Each has a different role
    and knowledge source. You can see every agent's individual contribution
    in the response.

    **Agent 1 — Research Agent**
    Uses Google Search to find current information from the internet.
    Same as `/chat` but with a focused "research" prompt.

    **Agent 2 — Knowledge Agent**
    Searches your ChromaDB knowledge base for relevant documents.
    Same as `/rag-chat` but wrapped as a callable agent.

    **Agent 3 — Synthesizer Agent**
    Receives outputs from Agents 1 and 2 and writes one coherent answer.
    Labels each fact: [Internet] or [Knowledge Base].

    **How to read the response:**
    - `multi_agent_summary` — quick 3-line overview of what each agent did
    - `agents[]` — each agent's name, role, answer, and flow steps
    - `final_answer` — the synthesizer's combined output

    **Tip:** Run `/documents/seed` first to give the knowledge_agent something
    to find, then ask "What is RAG?" to see both agents contribute.
    """
    return run_multi_agent(request.message, request.model)
