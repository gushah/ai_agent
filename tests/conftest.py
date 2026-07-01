# tests/conftest.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared pytest fixtures used by all test files.
#
# KEY IDEA: We don't want tests to call the real Gemini API or write to the
# real chroma_db/ folder. So we:
#   1. Replace GeminiEmbeddingFunction with FakeEmbeddingFn (no API key needed)
#   2. Use chromadb.EphemeralClient() — in-memory only, discarded after each test
#   3. Patch get_collection() in the retriever to return our test collection
#
# This means every test runs fast, in isolation, and with no side effects.
# ─────────────────────────────────────────────────────────────────────────────

import uuid

import chromadb
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class FakeEmbeddingFn:
    """
    Returns deterministic 768-dimension vectors without calling Gemini.

    Each text produces a unique vector based on its hash, so ChromaDB
    similarity search still works (returns the exact document you added).
    Using Gemini here would require a real API key and add ~1-2s per test.

    chromadb 1.5.9 calls __call__ when ADDING documents and embed_query
    when SEARCHING — both must be implemented.
    """

    def __call__(self, input):
        return self._vectorize(input)

    def embed_query(self, input):
        """
        Called by chromadb 1.5.9 during collection.query() with a list of strings.
        Must return a list of vectors (same shape as __call__).
        """
        return self._vectorize(input)

    def _vectorize(self, texts):
        vectors = []
        for text in texts:
            seed = hash(text)
            vec = [(seed + i * 31) % 1000 / 1000.0 for i in range(768)]
            vectors.append(vec)
        return vectors


@pytest.fixture
def chroma_collection():
    """
    Fresh in-memory ChromaDB collection for each test.
    EphemeralClient = stored only in RAM, gone when the test ends.
    No chroma_db/ folder is touched.

    We use a UUID-based name because chromadb 1.5.9 uses a shared Rust backend
    for all EphemeralClient instances in the same process. Using the same name
    across tests would cause "collection already exists" errors.
    """
    client = chromadb.EphemeralClient()
    return client.create_collection(
        name=f"test_kb_{uuid.uuid4().hex}",
        embedding_function=FakeEmbeddingFn(),
        metadata={"hnsw:space": "cosine"},  # match production config in store.py
    )


@pytest.fixture
def app_client(chroma_collection):
    """
    FastAPI TestClient with isolated ChromaDB and fake embeddings.

    How the patch works:
      app/vectordb/retriever.py does: from app.vectordb.store import get_collection
      That creates a LOCAL reference called retriever.get_collection.
      We patch THAT reference so every call to get_collection() inside
      the retriever returns our in-memory test collection instead.

    For LLM calls (generate_content, interactions.create) we patch per-test
    so each test controls exactly what the LLM "returns".
    """
    with patch("app.vectordb.retriever.get_collection", return_value=chroma_collection):
        from main import app
        yield TestClient(app)
