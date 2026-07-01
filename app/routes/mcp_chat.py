# app/routes/mcp_chat.py
# ─────────────────────────────────────────────────────────────────────────────
# POST /mcp-chat — AI Agent that can use BOTH Google Search AND your ChromaDB
#                  knowledge base as tools via the MCP protocol.
#
# Difference from /chat (google search only) and /rag-chat (manual RAG):
#
#   /chat          → LLM can call Google Search (you gave it that tool)
#   /rag-chat      → YOU manually search ChromaDB, inject context, ask LLM
#   /mcp-chat      → LLM can call Google Search OR ChromaDB on its own —
#                    it decides which tool to use and when
#
# The MCP server (mcp_server/server.py) must be running on port 8001.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agent.runner import run_agent
from app.config import DEFAULT_MODEL

router = APIRouter(tags=["MCP — Model Context Protocol"])

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8001/mcp")

# Tools passed to Gemini — both Google Search AND our MCP server
MCP_TOOLS = [
    {"type": "google_search"},
    {
        "type": "mcp_server",
        "name": "knowledge_base",
        "url": MCP_SERVER_URL,
    },
]


class McpChatRequest(BaseModel):
    message: str
    model: str = DEFAULT_MODEL

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What is RAG? Also search for any recent news about it.",
            }
        }
    }


@router.post(
    "/mcp-chat",
    summary="Agent with Google Search + your ChromaDB knowledge base (MCP)",
)
async def mcp_chat(request: McpChatRequest):
    """
    The most powerful endpoint — the LLM agent has access to TWO tools:

    | Tool | What it does |
    |---|---|
    | `google_search` | Live internet search |
    | `knowledge_base` (MCP) | Search YOUR ChromaDB documents |

    The LLM autonomously decides which tool to use and when.
    You see every step: `mcp_server_tool_call` and `mcp_server_tool_result`
    appear in the steps alongside `google_search_call`.

    **Requires:** `mcp_server/server.py` running on port 8001.
    Start it with: `.venv/bin/python mcp_server/server.py`
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    try:
        return await asyncio.to_thread(
            run_agent,
            request.message,
            request.model,
            MCP_TOOLS,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Error: {exc}. "
                "Make sure the MCP server is running: "
                ".venv/bin/python mcp_server/server.py"
            ),
        ) from exc
