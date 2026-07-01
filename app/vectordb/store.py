# app/vectordb/store.py
# ─────────────────────────────────────────────────────────────────────────────
# ChromaDB setup + Gemini embedding function.
#
# What is a vector database?
#   Normal databases store exact values and search with SQL (WHERE name = 'X').
#   A vector database stores numbers (vectors/embeddings) that REPRESENT the
#   MEANING of text, and searches by semantic similarity.
#
#   Example:
#     "dog" and "puppy" are different strings → SQL finds no match
#     "dog" and "puppy" have very similar embeddings → vector DB finds them
#
# What are embeddings?
#   An embedding model converts text into a list of ~768 numbers.
#   Texts with similar meanings produce numbers that are close together
#   in high-dimensional space. We use Gemini's text-embedding-004 model.
#
# ChromaDB:
#   A local vector database — no server, no account, data saved to disk.
#   The collection is like a "table" that stores text + its embedding.
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path
from typing import List

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

from app.client import get_client

# ChromaDB will persist data here (survives server restarts)
CHROMA_DB_PATH = Path(__file__).parent.parent.parent / "chroma_db"

# Name of the ChromaDB collection (like a table name)
COLLECTION_NAME = "knowledge_base"

# Gemini embedding model — converts text → 768-dimension vector
EMBEDDING_MODEL = "text-embedding-004"


# ── Custom Gemini embedding function ─────────────────────────────────────────

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Tells ChromaDB how to convert text into embedding vectors.
    ChromaDB calls this automatically whenever you add or search documents.

    Flow:
      text → Gemini text-embedding-004 → list of 768 floats → stored in ChromaDB
    """

    def __call__(self, input: Documents) -> Embeddings:
        result = get_client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=list(input),
        )
        return [list(e.values) for e in result.embeddings]


# ── ChromaDB client & collection (singletons) ─────────────────────────────────

_chroma_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def get_collection() -> chromadb.Collection:
    """
    Return the ChromaDB collection, creating it on first call.
    The collection persists to disk at CHROMA_DB_PATH.
    """
    global _chroma_client, _collection
    if _collection is None:
        CHROMA_DB_PATH.mkdir(exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=GeminiEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},  # cosine = best for text similarity
        )
    return _collection
