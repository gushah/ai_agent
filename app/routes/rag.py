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

import asyncio

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

# ── Sample documents — Acme Corp business policies (realistic scenario) ───────
SAMPLE_DOCUMENTS = [
    {
        "doc_id": "acme-return-001",
        "text": (
            "Acme Corp Return Policy: Customers may return any unused item within 30 days "
            "of purchase for a full refund. Items must be in their original packaging. "
            "Electronics have a shorter 15-day return window. To start a return, visit "
            "acmecorp.com/returns or call 1-800-ACME-123. Refunds are processed within "
            "5-7 business days to the original payment method. Sale items are final sale "
            "and cannot be returned under any circumstances."
        ),
        "metadata": {"topic": "returns", "department": "customer_service", "source": "Acme Corp Policy v2.1"},
    },
    {
        "doc_id": "acme-shipping-002",
        "text": (
            "Acme Corp Shipping Information: Standard shipping takes 5-7 business days "
            "and costs $4.99 for orders under $50. Orders over $50 qualify for free "
            "standard shipping automatically. Express shipping (2-3 days) costs $12.99. "
            "Overnight shipping costs $24.99 and must be placed before 2pm EST. "
            "International shipping is available to 45 countries starting at $19.99. "
            "All orders are dispatched within 1 business day of purchase."
        ),
        "metadata": {"topic": "shipping", "department": "logistics", "source": "Acme Corp Policy v2.1"},
    },
    {
        "doc_id": "acme-warranty-003",
        "text": (
            "Acme Corp Warranty: All Acme products include a 1-year limited warranty "
            "covering manufacturing defects. Premium Electronics carry a 2-year warranty. "
            "The warranty does not cover accidental damage, water damage, or normal wear "
            "and tear. To make a warranty claim, email support@acmecorp.com with your "
            "order number and a photo of the issue. Approved claims receive a free "
            "replacement or repair at no cost to the customer."
        ),
        "metadata": {"topic": "warranty", "department": "customer_service", "source": "Acme Corp Policy v2.1"},
    },
    {
        "doc_id": "acme-refund-004",
        "text": (
            "Acme Corp Refund Process: Refunds are issued to the original payment method "
            "within 5-7 business days after the returned item is received at our warehouse. "
            "Store credit is available immediately upon return approval if preferred. "
            "Gift card purchases are refunded as store credit only. Partial refunds may "
            "be issued for items returned without original packaging. If your refund has "
            "not appeared after 10 business days, contact billing@acmecorp.com."
        ),
        "metadata": {"topic": "refunds", "department": "billing", "source": "Acme Corp Policy v2.1"},
    },
    {
        "doc_id": "acme-support-005",
        "text": (
            "Acme Corp Customer Support Hours: Our support team is available Monday to "
            "Friday 9am-6pm EST and Saturday 10am-4pm EST. We are closed on Sundays and "
            "public holidays. Contact us by phone at 1-800-ACME-123, by email at "
            "support@acmecorp.com, or via live chat at acmecorp.com/chat. Average email "
            "response time is 4 hours during business hours. For urgent issues, phone "
            "or live chat is recommended. Our team speaks English, Spanish, and French."
        ),
        "metadata": {"topic": "support", "department": "customer_service", "source": "Acme Corp Support Guide"},
    },
    {
        "doc_id": "acme-membership-006",
        "text": (
            "Acme Corp Premium Membership: The Acme Premium plan costs $9.99 per month "
            "or $89 per year (save 26%). Benefits include: free express shipping on all "
            "orders, 10% discount on every purchase, early access to sales and new "
            "products, priority support with 1-hour response time, and a free birthday "
            "gift every year. Members earn 3x reward points on every purchase compared "
            "to 1x for standard accounts. Cancel anytime with no cancellation fees."
        ),
        "metadata": {"topic": "membership", "department": "marketing", "source": "Acme Corp Premium Guide"},
    },
    {
        "doc_id": "acme-orders-007",
        "text": (
            "Acme Corp Order Tracking and Cancellation: After placing an order you will "
            "receive a confirmation email within 15 minutes. Once shipped, a tracking "
            "number is sent by email within 24 hours. Track your order at "
            "acmecorp.com/track or via the Acme mobile app. Orders can be cancelled "
            "within 1 hour of placement for a full refund. If your order shows 'delayed' "
            "for more than 3 business days, contact support for a free shipping upgrade "
            "on your next order."
        ),
        "metadata": {"topic": "orders", "department": "logistics", "source": "Acme Corp Order Guide"},
    },
]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/seed", summary="Load sample AI documents to test with")
async def seed_documents():
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
        "message": f"Added {len(ids)} Acme Corp business policy documents.",
        "added_ids": ids,
        "total_in_db": document_count(),
        "tip": "Now try POST /rag-chat with: 'What is the return policy?' or 'How much does shipping cost?'",
    }


@router.post("", summary="Add a document to the knowledge base")
async def add_doc(doc: DocumentIn):
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
async def get_documents():
    """Return all documents currently stored in ChromaDB."""
    docs = list_all_documents()
    return {
        "total": len(docs),
        "documents": docs,
    }


@router.delete("/{doc_id}", summary="Remove a document from the knowledge base")
async def remove_document(doc_id: str):
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
async def rag_chat(request: RagRequest):
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
    # search() calls the Gemini embedding API — run in a thread
    raw_results = await asyncio.to_thread(search, request.question, request.top_k)

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
        response = await asyncio.to_thread(
            get_client().models.generate_content,
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
