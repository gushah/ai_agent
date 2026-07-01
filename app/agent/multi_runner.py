# app/agent/multi_runner.py
# ─────────────────────────────────────────────────────────────────────────────
# Multi-Agent Orchestrator.
#
# What is Multi-Agent?
#   Instead of one LLM trying to do everything, you create SPECIALIST agents —
#   each focused on a single job. An orchestrator coordinates them in sequence.
#
# Architecture (Orchestrator Pattern):
#
#   Your Question
#        │
#        ▼
#   Orchestrator (this module)
#        ├── Agent 1: Research Agent     — searches the INTERNET (Google Search)
#        ├── Agent 2: Knowledge Agent    — searches your CHROMADB knowledge base
#        └── Agent 3: Synthesizer Agent  — COMBINES both outputs into one answer
#
# Why is multi-agent better than one agent?
#   • Each agent is focused on ONE task → produces higher quality on that task
#   • You can see EXACTLY what each agent contributed
#   • Agents can run in parallel (not done here but easy to add with asyncio)
#   • You can swap/add agents without touching the others
#   • Real-world example: one agent reads PDFs, one checks a database, one writes
#
# Key difference from MCP (/mcp-chat):
#   MCP     → ONE LLM decides when to call tools on its own
#   Multi-Agent → YOU (the orchestrator) decide which agents run and in what order
# ─────────────────────────────────────────────────────────────────────────────

from app.client import get_client
from app.config import DEFAULT_MODEL
from app.agent.runner import run_agent
from app.vectordb.retriever import search as db_search
from app.models.schemas import AgentResult, MultiAgentResponse


def run_research_agent(question: str, model: str) -> tuple[str, list[str]]:
    """
    Agent 1 — Research Agent

    Speciality : live internet search via Google Search
    Tool used  : google_search (built-in Gemini tool)
    Job        : find current, up-to-date facts from the web

    Reuses the existing run_agent() — same as POST /chat but with a
    focused prompt so it stays on-task.
    """
    response = run_agent(
        message=(
            f"You are a research agent. Find current, factual information about: "
            f"{question}\n"
            f"Be concise. Focus on key facts. Do not add opinions."
        ),
        model=model,
        tools=[{"type": "google_search"}],
    )
    return response.final_answer, response.agent_flow_summary


def run_knowledge_agent(question: str, model: str) -> tuple[str, list[str]]:
    """
    Agent 2 — Knowledge Agent

    Speciality : private knowledge base search via ChromaDB
    Tool used  : ChromaDB semantic search (no internet access)
    Job        : answer using ONLY documents stored in your knowledge base

    Same pattern as POST /rag-chat — embed question → find similar docs →
    give LLM only those docs as context.
    If the knowledge base is empty, returns a clear "not found" message.
    """
    docs = db_search(question, top_k=3)

    if not docs:
        return (
            "No relevant documents found in the knowledge base for this question. "
            "Tip: use POST /documents/seed to add sample documents first.",
            ["Searched ChromaDB — 0 documents retrieved"],
        )

    context = "\n\n".join(
        f"[Document: {d.doc_id} | similarity: {d.similarity_score:.2f}]\n{d.text}"
        for d in docs
    )

    prompt = (
        "You are a knowledge base expert. Answer using ONLY the documents below.\n"
        "Do NOT use outside knowledge. If the documents lack a good answer, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )

    try:
        response = get_client().models.generate_content(
            model=model,
            contents=prompt,
        )
        answer = response.text or "No answer generated."
    except Exception as exc:
        answer = f"Knowledge agent error: {exc}"

    flow = [
        f"Searched ChromaDB — retrieved {len(docs)} doc(s): "
        + ", ".join(f"{d.doc_id} (score={d.similarity_score:.2f})" for d in docs)
    ]
    return answer, flow


def run_synthesizer_agent(
    question: str,
    research_answer: str,
    knowledge_answer: str,
    model: str,
) -> str:
    """
    Agent 3 — Synthesizer Agent

    Speciality : combining outputs from multiple agents
    Tool used  : none (pure reasoning / writing)
    Job        : merge research_agent + knowledge_agent into one coherent answer,
                 labelling which facts came from which source.

    This is the "final word" — it sees everything the other agents found and
    writes the best possible combined answer.
    """
    prompt = (
        "You are a synthesizer agent. Two specialist agents independently researched the same question.\n"
        "Combine their findings into ONE clear, well-structured answer.\n"
        "Rules:\n"
        "  • Label each fact: [Internet] if it came from research_agent, [Knowledge Base] if from knowledge_agent\n"
        "  • If both sources agree on something, mention that\n"
        "  • If they contradict, point out the difference\n"
        "  • If one source has no relevant info, say so and rely on the other\n\n"
        f"Question: {question}\n\n"
        f"--- Research Agent findings (from the internet) ---\n{research_answer}\n\n"
        f"--- Knowledge Agent findings (from the knowledge base) ---\n{knowledge_answer}\n\n"
        "Combined answer:"
    )

    try:
        response = get_client().models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text or "No synthesis generated."
    except Exception as exc:
        return f"Synthesizer agent error: {exc}"


def run_multi_agent(message: str, model: str = DEFAULT_MODEL) -> MultiAgentResponse:
    """
    Orchestrates 3 specialist agents in sequence and returns every agent's output.

    You can read this function as the "orchestrator":
      Step 1 → dispatch to research_agent
      Step 2 → dispatch to knowledge_agent
      Step 3 → pass both outputs to synthesizer_agent
      Step 4 → assemble the full MultiAgentResponse
    """

    # ── Agent 1: Research Agent ───────────────────────────────────────────────
    research_answer, research_flow = run_research_agent(message, model)

    # ── Agent 2: Knowledge Agent ──────────────────────────────────────────────
    knowledge_answer, knowledge_flow = run_knowledge_agent(message, model)

    # ── Agent 3: Synthesizer Agent ────────────────────────────────────────────
    final_answer = run_synthesizer_agent(message, research_answer, knowledge_answer, model)

    # ── Build the response ────────────────────────────────────────────────────
    agents = [
        AgentResult(
            agent_name="research_agent",
            role="Internet Researcher — uses Google Search to find current information",
            answer=research_answer,
            flow_summary=research_flow,
        ),
        AgentResult(
            agent_name="knowledge_agent",
            role="Knowledge Base Expert — searches your private ChromaDB documents",
            answer=knowledge_answer,
            flow_summary=knowledge_flow,
        ),
        AgentResult(
            agent_name="synthesizer_agent",
            role="Synthesizer — combines both agents' findings into one final answer",
            answer=final_answer,
            flow_summary=[
                "Received: research_agent output + knowledge_agent output",
                "Combined into one answer with [Internet] / [Knowledge Base] labels",
            ],
        ),
    ]

    summary = [
        f"[Agent 1] research_agent     → searched internet for: '{message[:55]}'",
        f"[Agent 2] knowledge_agent    → searched ChromaDB knowledge base",
        f"[Agent 3] synthesizer_agent  → combined both sources → final answer below",
    ]

    return MultiAgentResponse(
        question=message,
        model_used=model,
        multi_agent_summary=summary,
        agents=agents,
        final_answer=final_answer,
    )
