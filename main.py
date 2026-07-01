# main.py
# ─────────────────────────────────────────────────────────────────────────────
# Entry point — creates the FastAPI app and registers all routers.
# Nothing else lives here; see the app/ package for all logic.
#
# Run:
#   export GEMINI_API_KEY="your-key"
#   .venv/bin/uvicorn main:app --reload --port 8000
#
# Docs: http://127.0.0.1:8000/docs
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI

from app.routes import chat, info, rag, mcp_chat

app = FastAPI(
    title="AI Agent Flow Demo",
    description=(
        "Send a question and observe every internal step the Gemini AI agent takes "
        "— tool calls, search queries, chain-of-thought, and the final answer.\n\n"
        "Visit **GET /flow-explained** to understand the full architecture."
    ),
    version="2.0.0",
)

# Register route modules
app.include_router(info.router)      # GET /,  GET /models,  GET /flow-explained
app.include_router(chat.router)      # POST /chat
app.include_router(rag.router)       # POST /documents, GET /documents, POST /documents/rag-chat
app.include_router(mcp_chat.router)  # POST /mcp-chat
