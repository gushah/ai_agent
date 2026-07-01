# mcp_server/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP (Model Context Protocol) Server
# ─────────────────────────────────────────────────────────────────────────────
#
# What is MCP?
#   MCP is an open standard (by Anthropic) that lets LLMs talk to external
#   tools in a standardised way — like a USB-C port for AI tools.
#
#   Instead of the RAG route (where YOU manually search ChromaDB and inject
#   context), the MCP server exposes your ChromaDB as a *tool* that the LLM
#   can autonomously decide to call whenever IT thinks it needs to.
#
# How it works here:
#   1. This server starts on http://localhost:8001
#   2. When POST /mcp-chat is called, Gemini is told:
#        "You have these tools available: google_search + mcp_server at :8001"
#   3. Gemini decides on its own:
#        - Use google_search for live internet data
#        - Use search_knowledge_base to query YOUR ChromaDB
#        - Use both, or neither
#   4. Every tool call is visible in the interaction steps
#
# Run this server separately:
#   .venv/bin/python mcp_server/server.py
#
# It will listen at: http://localhost:8001/mcp
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys

# Make sure app/ is importable when running this file directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP

from app.vectordb.retriever import (
    add_document,
    document_count,
    list_all_documents,
    search,
)

# Create the MCP server — give it a name the LLM will see
mcp = FastMCP(
    name="knowledge_base",
    instructions=(
        "This server gives you access to a local knowledge base stored in "
        "ChromaDB. Use search_knowledge_base when the user asks about topics "
        "that might be covered in the knowledge base (RAG, embeddings, "
        "ChromaDB, AI agents, FastAPI, LLMs). Use add_document_to_kb to store "
        "new information the user provides."
    ),
)


# ── Tool 1: Search the knowledge base ────────────────────────────────────────

@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search the local knowledge base for documents relevant to the query.
    Returns the most semantically similar documents with similarity scores.
    Use this when the user asks about a topic that might be in the knowledge base.

    Args:
        query: The search query — what you want to find
        top_k: How many documents to return (default 3, max 5)
    """
    top_k = min(top_k, 5)
    results = search(query, top_k)

    if not results:
        return "The knowledge base is empty. No documents found."

    lines = [f"Found {len(results)} relevant document(s):\n"]
    for i, doc in enumerate(results, 1):
        lines.append(
            f"[{i}] similarity={doc['similarity_score']:.2f} | "
            f"id={doc['doc_id']}\n"
            f"    {doc['text']}\n"
        )
    return "\n".join(lines)


# ── Tool 2: Add a document ────────────────────────────────────────────────────

@mcp.tool()
def add_document_to_kb(text: str, topic: str = "", source: str = "") -> str:
    """
    Add a new document to the knowledge base so it can be found in future searches.
    Use this when the user provides information they want to remember.

    Args:
        text: The document text to store
        topic: Optional topic label (e.g. "AI", "FastAPI")
        source: Optional source label (e.g. "user input", "manual")
    """
    metadata: dict = {}
    if topic:
        metadata["topic"] = topic
    if source:
        metadata["source"] = source

    doc_id = add_document(text=text, metadata=metadata)
    return f"Document stored successfully. ID: {doc_id}. Total documents in KB: {document_count()}"


# ── Tool 3: Count documents ───────────────────────────────────────────────────

@mcp.tool()
def get_kb_stats() -> str:
    """
    Return how many documents are stored in the knowledge base and a brief summary.
    Use this to check if the knowledge base has been populated.
    """
    count = document_count()
    if count == 0:
        return "Knowledge base is empty. Use POST /documents/seed to add sample documents."

    docs = list_all_documents()
    topics = list({d["metadata"].get("topic", "unknown") for d in docs if d["metadata"]})
    return (
        f"Knowledge base contains {count} document(s).\n"
        f"Topics covered: {', '.join(sorted(topics)) or 'none tagged'}"
    )


# ── Start the server ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting MCP Knowledge Base Server...")
    print("URL: http://localhost:8001/mcp")
    print("Tools exposed to Gemini:")
    print("  • search_knowledge_base(query, top_k)")
    print("  • add_document_to_kb(text, topic, source)")
    print("  • get_kb_stats()")
    print("\nKeep this running while using POST /mcp-chat")
    print("─" * 50)

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
    )
