# app/models/schemas.py
# ─────────────────────────────────────────────────────────────────────────────
# All Pydantic models (request bodies and response shapes) for the API.
# Covers both the agent/chat flow and the RAG (vector database) flow.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Any

from pydantic import BaseModel

from app.config import DEFAULT_MODEL


class ChatRequest(BaseModel):
    """Body of POST /chat."""

    message: str
    model: str = DEFAULT_MODEL

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What are the latest breakthroughs in AI agents?"
            }
        }
    }


class AgentStep(BaseModel):
    """
    One step in the agent's internal reasoning chain.

    step_type values you will see:
        user_input          — your question entered the agent
        thought             — LLM's internal reasoning (hidden from end-users)
        google_search_call  — agent called Google Search
        google_search_result— search results returned to the LLM
        model_output        — the LLM's final answer
        function_call       — agent called a custom tool
        function_result     — custom tool returned a result
    """

    step_index: int
    step_type: str        # exact SDK discriminator, e.g. "google_search_call"
    role: str             # "user" | "agent" | "tool"
    label: str            # short human-readable label
    detail: str           # plain-English explanation of what happened
    data: dict[str, Any]  # structured data extracted from this step


class ChatResponse(BaseModel):
    """Full response from POST /chat — includes every internal agent step."""

    question: str
    model_used: str
    total_steps: int
    agent_flow_summary: list[str]  # one-liner per step, e.g. "[0] USER → User Question"
    steps: list[AgentStep]         # full detail of every step
    final_answer: str              # text from the last model_output step


# ── RAG (Retrieval Augmented Generation) models ───────────────────────────────
# Used by POST /documents and POST /rag-chat


class DocumentIn(BaseModel):
    """A document to store in ChromaDB."""

    text: str
    doc_id: str | None = None          # auto-generated UUID if omitted
    metadata: dict = {}                # optional tags, e.g. {"source": "manual", "topic": "AI"}

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "RAG stands for Retrieval Augmented Generation. It lets an LLM answer questions using your own documents instead of its training data.",
                "metadata": {"source": "AI glossary", "topic": "RAG"},
            }
        }
    }


class RetrievedDoc(BaseModel):
    """One document returned by the vector similarity search."""

    doc_id: str
    text: str
    metadata: dict
    similarity_score: float   # 0.0 (unrelated) → 1.0 (identical meaning)


class RagRequest(BaseModel):
    """Body of POST /rag-chat."""

    question: str
    top_k: int = 3             # how many similar documents to retrieve
    model: str = "gemini-2.5-flash"

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What is RAG and why is it useful?",
                "top_k": 3,
            }
        }
    }


class RagResponse(BaseModel):
    """
    Full response from POST /rag-chat.

    Shows the complete RAG flow:
      1. question → embedded
      2. ChromaDB searched → retrieved_documents
      3. context_used built from those docs
      4. LLM answers using the context → answer
    """

    question: str
    model_used: str
    total_docs_in_db: int
    retrieved_documents: list[RetrievedDoc]   # what ChromaDB returned
    context_used: str                          # the text fed to the LLM as context
    rag_flow_summary: list[str]               # step-by-step what happened
    answer: str
