# app/vectordb/retriever.py
# ─────────────────────────────────────────────────────────────────────────────
# Add documents to ChromaDB and search by semantic similarity.
#
# How similarity search works:
#   1. Your question is embedded → becomes a vector (list of numbers)
#   2. ChromaDB computes cosine similarity between your vector and all stored vectors
#   3. The most similar documents are returned (closest in meaning)
#
# Cosine similarity score:
#   1.0  = identical meaning
#   0.8+ = very similar
#   0.5  = somewhat related
#   0.0  = completely unrelated
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from typing import Any

from app.vectordb.store import get_collection


def add_document(text: str, metadata: dict | None = None, doc_id: str | None = None) -> str:
    """
    Add one document to ChromaDB.

    ChromaDB will automatically:
      1. Call GeminiEmbeddingFunction to convert text → vector
      2. Store the vector + original text + metadata on disk

    Returns the doc_id (auto-generated UUID if not provided).
    """
    collection = get_collection()
    doc_id = doc_id or str(uuid.uuid4())
    collection.add(
        documents=[text],
        metadatas=[metadata] if metadata else None,
        ids=[doc_id],
    )
    return doc_id


def add_documents(items: list[dict[str, Any]]) -> list[str]:
    """
    Batch-add multiple documents.
    Each item should have: {"text": str, "metadata": dict, "doc_id": str (optional)}
    """
    collection = get_collection()
    texts, raw_metas, ids = [], [], []
    for item in items:
        texts.append(item["text"])
        raw_metas.append(item.get("metadata") or None)
        ids.append(item.get("doc_id") or str(uuid.uuid4()))

    # Only pass metadatas when at least one document has metadata.
    # ChromaDB 1.5.9 rejects empty dicts and mixed-None lists.
    effective_metas = raw_metas if any(raw_metas) else None
    collection.add(documents=texts, metadatas=effective_metas, ids=ids)
    return ids


def search(question: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Find the top_k most semantically similar documents to `question`.

    Steps happening internally:
      1. question → embedded via Gemini (GeminiEmbeddingFunction)
      2. ChromaDB computes cosine similarity against all stored vectors
      3. Returns top_k closest matches with their similarity scores

    Returns a list of dicts with: doc_id, text, metadata, similarity_score
    """
    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    docs = []
    for i, doc_id in enumerate(results["ids"][0]):
        # ChromaDB returns cosine distance (0=identical, 2=opposite)
        # Convert to similarity score: 1 - (distance / 2) → 0.0 to 1.0
        distance = results["distances"][0][i]
        similarity = round(1.0 - (distance / 2), 4)

        docs.append({
            "doc_id": doc_id,
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] or {},
            "similarity_score": similarity,
        })

    return docs


def list_all_documents() -> list[dict[str, Any]]:
    """Return all documents currently stored in the collection."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.get(include=["documents", "metadatas"])
    docs = []
    for i, doc_id in enumerate(results["ids"]):
        docs.append({
            "doc_id": doc_id,
            "text": results["documents"][i],
            "metadata": results["metadatas"][i],
        })
    return docs


def delete_document(doc_id: str) -> None:
    """Remove a document from ChromaDB by its ID."""
    get_collection().delete(ids=[doc_id])


def document_count() -> int:
    """Return how many documents are stored."""
    return get_collection().count()
