# app/routes/info.py
# ─────────────────────────────────────────────────────────────────────────────
# Informational / utility endpoints:
#   GET /            — health check
#   GET /models      — list supported models
#   GET /flow-explained — learn what each step type means
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health check", tags=["Info"])
def root():
    return {
        "status": "ok",
        "message": "AI Agent Flow API — 4 flows, 12 endpoints. Open /docs for interactive UI.",
        "quick_start": "Step 1: POST /documents/seed  →  Step 2: POST /documents/rag-chat",
        "endpoints": {
            "Info": {
                "GET  /": "This health check",
                "GET  /docs": "Interactive Swagger UI — test all endpoints here",
                "GET  /models": "List supported Gemini model IDs",
                "GET  /flow-explained": "Plain-English guide to agent architecture",
            },
            "Flow 1 — Agent (LLM + Google Search)": {
                "POST /chat": "AI agent with Google Search — see every internal step",
            },
            "Flow 2 — RAG (Your Knowledge Base)": {
                "POST /documents/seed": "Load 7 sample documents into ChromaDB",
                "POST /documents": "Add your own document (text → embedding → ChromaDB)",
                "GET  /documents": "List all stored documents",
                "DELETE /documents/{id}": "Remove a document from ChromaDB",
                "POST /documents/rag-chat": "Ask a question using your knowledge base",
            },
            "Flow 3 — MCP (LLM picks tools autonomously)": {
                "POST /mcp-chat": "LLM chooses Google Search and/or ChromaDB via MCP protocol",
            },
            "Flow 4 — Multi-Agent (Orchestrator pattern)": {
                "POST /multi-agent-chat": "3 agents: research_agent + knowledge_agent + synthesizer",
            },
        },
    }


@router.get("/models", summary="List supported models", tags=["Info"])
def list_models():
    """Returns the model IDs you can pass in the `model` field of POST /chat."""
    return {
        "models": [
            {
                "id": "gemini-2.5-flash",
                "description": "Fast & efficient — recommended for most tasks",
            },
            {
                "id": "gemini-2.5-pro",
                "description": "Most capable Gemini model",
            },
            {
                "id": "gemini-2.0-flash",
                "description": "Previous generation flash model",
            },
        ]
    }


@router.get("/flow-explained", summary="Learn what each step type means", tags=["Info"])
def flow_explained():
    """
    A plain-English guide to AI agent architecture and the meaning of every
    step type returned by POST /chat.  Start here if you're new to AI agents.
    """
    return {
        "how_an_ai_agent_works": (
            "An AI agent is an LLM that can decide to call external tools "
            "(like Google Search) and loop until it has enough information to answer. "
            "POST /chat exposes every step of that internal loop."
        ),
        "architecture": {
            "You (HTTP client)": "Sends a question via POST /chat",
            "FastAPI (this server)": "HTTP layer — routes the request, validates input, returns response",
            "Gemini LLM": "The brain — reasons, decides which tools to call, writes the answer",
            "Tools (google_search)": "External capabilities the LLM can invoke to get live data",
            "google-genai SDK": "Python client that talks to the Gemini Interactions API",
        },
        "step_types": {
            "user_input": {
                "role": "user",
                "description": "Your question — this is what enters the agent.",
                "when": "Always first",
            },
            "thought": {
                "role": "agent (internal, never shown to end-users)",
                "description": (
                    "The LLM's chain-of-thought reasoning. "
                    "It decides WHAT to do next — call a tool or answer directly."
                ),
                "when": "Before every tool call and before the final answer",
            },
            "google_search_call": {
                "role": "agent → tool",
                "description": (
                    "The agent issued Google Search queries to get live web data."
                ),
                "when": "When the question requires current information",
            },
            "google_search_result": {
                "role": "tool → agent",
                "description": (
                    "Raw search results (title, URL, snippet) returned to the LLM. "
                    "The LLM reads these to form its answer."
                ),
                "when": "Immediately after every google_search_call",
            },
            "model_output": {
                "role": "agent",
                "description": (
                    "The LLM's final answer — synthesised from its thoughts "
                    "and all tool results. Show this to users."
                ),
                "when": "Always last",
            },
        },
        "typical_flow": [
            "[0] USER  → user_input              (your question enters)",
            "[1] AGENT → thought                 (LLM: 'I need to search for this')",
            "[2] AGENT → google_search_call      (LLM calls Google Search)",
            "[3] TOOL  → google_search_result    (search results returned to LLM)",
            "[4] AGENT → thought                 (LLM: 'Now I have enough to answer')",
            "[5] AGENT → model_output            (final answer returned to you)",
        ],
    }
