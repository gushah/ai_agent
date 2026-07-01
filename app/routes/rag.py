# app/routes/rag.py
# ─────────────────────────────────────────────────────────────────────────────
# RAG (Retrieval Augmented Generation) endpoints.
#
# What is RAG?
#   Instead of relying on the LLM's training data (which has a cutoff date
#   and doesn't know your private documents), RAG lets you:
#     1. Store YOUR documents in a vector database (ChromaDB)
#     2. At query time, find the most relevant documents by meaning
#     3. Inject them as context into the LLM prompt
#     4. The LLM answers using YOUR documents as its source of truth
#
# Endpoints:
#   POST /documents         — add a document to ChromaDB
#   POST /documents/seed    — load sample AI documents to test with
#   GET  /documents         — list all stored documents
#   DELETE /documents/{id}  — remove a document
#   POST /rag-chat          — ask a question (RAG flow)
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException

from app.client import get_client
from app.models.schemas import DocumentIn, RagRequest, RagResponse, RetrievedDoc
from app.vectordb.retriever import (
    add_document,
    add_documents,
    delete_document,
    document_count,
    list_all_documents,
    search,
)

router = APIRouter(prefix="/documents", tags=["RAG — Vector Database"])

# ── Sample documents to seed the knowledge base for learning ──────────────────
SAMPLE_DOCUMENTS = [
    {
        "doc_id": "rag-001",
        "text": (
            "RAG stands for Retrieval Augmented Generation. It is a technique that "
            "combines a vector database with a large language model. Instead of the LLM "
            "relying only on its training data, RAG retrieves relevant documents from a "
            "database at query time and injects them as context into the prompt. This "
            "lets the LLM answer questions about private or recent information it was "
            "never trained on."
        ),
        "metadata": {"topic": "RAG", "source": "AI glossary"},
    },
    {
        "doc_id": "vec-001",
        "text": (
            "A vector database stores text as high-dimensional numerical vectors called "
            "embeddings. When you search, your query is also converted to a vector and "
            "the database finds stored vectors that are mathematically close — meaning "
            "semantically similar. ChromaDB, Pinecone, and pgvector are popular vector "
            "databases. ChromaDB runs entirely locally with no external service required."
        ),
        "metadata": {"topic": "vector database", "source": "AI glossary"},
    },
    {
        "doc_id": "emb-001",
        "text": (
            "An embedding is a list of numbers (a vector) that represents the meaning "
            "of a piece of text in a high-dimensional space. Similar texts produce "
            "vectors that are close together. For example, 'dog' and 'puppy' will have "
            "similar embeddings even though they are different words. Gemini's "
            "text-embedding-004 model produces 768-dimensional embeddings."
        ),
        "metadata": {"topic": "embeddings", "source": "AI glossary"},
    },
    {
        "doc_id": "agent-001",
        "text": (
            "An AI agent is an LLM that can take actions by calling tools. Unlike a "
            "simple chatbot that just responds, an agent can decide to call Google "
            "Search, run code, or query a database. The agent loops — it thinks, acts, "
            "observes the result, thinks again — until it has enough information to "
            "give a final answer. This loop is called the ReAct pattern "
            "(Reasoning + Acting)."
        ),
        "metadata": {"topic": "AI agents", "source": "AI glossary"},
    },
    {
        "doc_id": "llm-001",
        "text": (
            "A Large Language Model (LLM) is a neural network trained on vast amounts "
            "of text to predict the next token. At inference time, the model takes a "
            "prompt (input text) and generates a response token by token. Modern LLMs "
            "like Gemini 2.5 Flash have context windows of 1 million tokens and can "
            "reason, write code, summarise documents, and call external tools."
        ),
        "metadata": {"topic": "LLM", "source": "AI glossary"},
    },
    {
        "doc_id": "chroma-001",
        "text": (
            "ChromaDB is an open-source vector database that runs locally in Python "
            "with no external service. You can store documents with their embeddings "
            "and query by semantic similarity. ChromaDB supports pluggable embedding "
            "functions — in this project we use Gemini's text-embedding-004 model. "
            "Data is persisted to a local folder called chroma_db/."
        ),
        "metadata": {"topic": "ChromaDB", "source": "project docs"},
    },
    {
        "doc_id": "fastapi-001",
        "text": (
            "FastAPI is a modern Python web framework for building APIs. It uses Python "
            "type hints and Pydantic models to automatically validate request/response "
            "data and generate OpenAPI documentation. FastAPI is asynchronous-first and "
            "one of the fastest Python frameworks. In this project, FastAPI is the HTTP "
            "layer that sits between the user and the Gemini LLM."
        ),
        "metadata": {"topic": "FastAPI", "source": "project docs"},
    },
]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/seed", summary="Load sample AI documents to test with")
def seed_documents():
    """
    Populate ChromaDB with 7 sample AI-related documents.
    Run this once so you can immediately test POST /rag-chat.
    Skips documents that already exist (safe to call multiple times).
    """
    collection_count_before = document_count()
    existing_ids = {d["doc_id"] for d in list_all_documents()}
    to_add = [d for d in SAMPLE_DOCUMENTS if d["doc_id"] not in existing_ids]

    if not to_add:
        return {
            "message": "All sample documents already exist — nothing added.",
            "total_in_db": document_count(),
        }

    ids = add_documents(to_add)
    return {
        "message": f"Added {len(ids)} sample documents.",
        "added_ids": ids,
        "total_in_db": document_count(),
        "tip": "Now try POST /rag-chat with a question like 'What is RAG?'",
    }


@router.post("", summary="Add a document to the knowledge base")
def add_doc(doc: DocumentIn):
    """
    Store one document in ChromaDB.

    ChromaDB will:
      1. Call Gemini text-embedding-004 to convert your text → vector
      2. Store the vector + text + metadata on disk (persists across restarts)
    """
    doc_id = add_document(
        text=doc.text,
        metadata=doc.metadata,
        doc_id=doc.doc_id,
    )
    return {
        "message": "Document stored successfully.",
        "doc_id": doc_id,
        "total_in_db": document_count(),
    }


@router.get("", summary="List all documents in the knowledge base")
def get_documents():
    """Return all documents currently stored in ChromaDB."""
    docs = list_all_documents()
    return {
        "total": len(docs),
        "documents": docs,
    }


@router.delete("/{doc_id}", summary="Remove a document from the knowledge base")
def remove_document(doc_id: str):
    """Delete a document from ChromaDB by its ID."""
    try:
        delete_document(doc_id)
        return {"message": f"Document '{doc_id}' deleted.", "total_in_db": document_count()}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Document not found: {exc}") from exc


@router.post(
    "/rag-chat",
    response_model=RagResponse,
    summary="Ask a question using your knowledge base (RAG)",
    tags=["RAG — Vector Database"],
)
def rag_chat(request: RagRequest):
    """
    The full RAG flow — visible step by step:

    **Step 1 — Embed your question**
    Your question is converted to a vector using Gemini text-embedding-004.

    **Step 2 — Search ChromaDB**
    The vector is compared to all stored document vectors using cosine similarity.
    The most semantically similar documents are retrieved.

    **Step 3 — Build context**
    Retrieved documents are formatted into a context block.

    **Step 4 — LLM answers with context**
    The LLM receives: *"Answer using ONLY this context: {docs}\\n\\nQuestion: {q}"*
    It cannot make up information — it must use what was retrieved.

    **Step 5 — Return everything**
    You see the retrieved docs, similarity scores, context used, and the final answer.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty.")

    total = document_count()
    if total == 0:
        raise HTTPException(
            status_code=400,
            detail="Knowledge base is empty. Call POST /documents/seed first, or add your own documents via POST /documents.",
        )

    # ── Step 1 & 2: embed question + search ChromaDB ──────────────────────────
    raw_results = search(question=request.question, top_k=request.top_k)

    retrieved = [
        RetrievedDoc(
            doc_id=r["doc_id"],
            text=r["text"],
            metadata=r["metadata"],
            similarity_score=r["similarity_score"],
        )
        for r in raw_results
    ]

    # ── Step 3: build context block ───────────────────────────────────────────
    context_parts = []
    for i, doc in enumerate(retrieved, 1):
        context_parts.append(
            f"[Document {i} | similarity: {doc.similarity_score:.2f}]\n{doc.text}"
        )
    context_used = "\n\n".join(context_parts)

    # ── Step 4: ask the LLM (with context injected in the prompt) ────────────
    prompt = (
        f"You are a helpful assistant. Answer the question using ONLY the context "
        f"provided below. If the context does not contain enough information to "
        f"answer, say so clearly — do not make up information.\n\n"
        f"CONTEXT:\n{context_used}\n\n"
        f"QUESTION: {request.question}"
    )

    try:
        response = get_client().models.generate_content(
            model=request.model,
            contents=prompt,
        )
        answer = response.text or "No answer generated."
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {exc}") from exc

    # ── Step 5: build a human-readable flow summary ───────────────────────────
    flow_summary = [
        f"[1] Embedded question using Gemini text-embedding-004",
        f"[2] Searched {total} documents in ChromaDB → retrieved top {len(retrieved)}",
        *[
            f"    • Doc '{d.doc_id}' (similarity: {d.similarity_score:.2f}) — {d.text[:60]}..."
            for d in retrieved
        ],
        f"[3] Built context block from {len(retrieved)} retrieved document(s)",
        f"[4] Sent prompt to {request.model} with context injected",
        f"[5] LLM answered using ONLY the retrieved context (no internet, no training data)",
    ]

    return RagResponse(
        question=request.question,
        model_used=request.model,
        total_docs_in_db=total,
        retrieved_documents=retrieved,
        context_used=context_used,
        rag_flow_summary=flow_summary,
        answer=answer,
    )
