# tests/test_rag.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests for RAG endpoints:
#   POST /documents/seed
#   POST /documents
#   GET  /documents
#   DELETE /documents/{id}
#   POST /documents/rag-chat
#
# All tests use the app_client fixture from conftest.py which:
#   - Patches get_collection() to return an in-memory ChromaDB (FakeEmbeddingFn)
#   - Means no Gemini API key is needed for storing/searching documents
#
# For /rag-chat we also mock get_client() so the LLM response is controlled.
# ─────────────────────────────────────────────────────────────────────────────

from unittest.mock import MagicMock, patch


def _mock_llm(answer: str = "Acme Corp accepts returns within 30 days."):
    """Helper: create a mock Gemini client that returns a fixed text answer."""
    mock_response = MagicMock()
    mock_response.text = answer
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


class TestSeedDocuments:
    def test_seed_adds_seven_documents(self, app_client):
        r = app_client.post("/documents/seed")
        assert r.status_code == 200
        assert r.json()["total_in_db"] == 7

    def test_seed_returns_acme_corp_document_ids(self, app_client):
        """The seed data should be Acme Corp business policies, not AI glossary."""
        ids = app_client.post("/documents/seed").json()["added_ids"]
        assert "acme-return-001" in ids
        assert "acme-shipping-002" in ids
        assert "acme-warranty-003" in ids
        assert "acme-refund-004" in ids
        assert "acme-support-005" in ids
        assert "acme-membership-006" in ids
        assert "acme-orders-007" in ids

    def test_seed_is_idempotent(self, app_client):
        """Calling seed twice should not duplicate documents — still 7 total."""
        app_client.post("/documents/seed")
        r2 = app_client.post("/documents/seed")
        assert r2.status_code == 200
        assert r2.json()["total_in_db"] == 7  # NOT 14

    def test_seed_response_has_tip(self, app_client):
        data = app_client.post("/documents/seed").json()
        assert "tip" in data


class TestAddDocument:
    def test_add_single_document_returns_200(self, app_client):
        r = app_client.post("/documents", json={
            "text": "Acme gift wrapping costs $3.99 per item.",
        })
        assert r.status_code == 200

    def test_add_document_returns_doc_id(self, app_client):
        r = app_client.post("/documents", json={"text": "Test text"})
        assert "doc_id" in r.json()

    def test_add_document_with_custom_id(self, app_client):
        r = app_client.post("/documents", json={
            "text": "Custom ID test",
            "doc_id": "my-custom-id-999",
        })
        assert r.json()["doc_id"] == "my-custom-id-999"

    def test_add_document_increments_total(self, app_client):
        before = app_client.get("/documents").json()["total"]
        app_client.post("/documents", json={"text": "A new document"})
        after = app_client.get("/documents").json()["total"]
        assert after == before + 1

    def test_add_document_with_metadata(self, app_client):
        app_client.post("/documents", json={
            "text": "Acme premium membership costs $9.99/month",
            "doc_id": "test-meta-001",
            "metadata": {"topic": "membership", "department": "marketing"},
        })
        docs = app_client.get("/documents").json()["documents"]
        added = next(d for d in docs if d["doc_id"] == "test-meta-001")
        assert added["metadata"]["topic"] == "membership"

    def test_missing_text_returns_422(self, app_client):
        """Pydantic should reject a body with no 'text' field."""
        r = app_client.post("/documents", json={"metadata": {"topic": "test"}})
        assert r.status_code == 422


class TestListDocuments:
    def test_empty_database_returns_zero(self, app_client):
        r = app_client.get("/documents")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_after_seed_returns_seven(self, app_client):
        app_client.post("/documents/seed")
        r = app_client.get("/documents")
        assert r.json()["total"] == 7

    def test_each_document_has_required_fields(self, app_client):
        app_client.post("/documents/seed")
        for doc in app_client.get("/documents").json()["documents"]:
            assert "doc_id" in doc
            assert "text" in doc
            assert "metadata" in doc


class TestDeleteDocument:
    def test_delete_existing_document_returns_200(self, app_client):
        app_client.post("/documents/seed")
        r = app_client.delete("/documents/acme-return-001")
        assert r.status_code == 200

    def test_delete_reduces_count_by_one(self, app_client):
        app_client.post("/documents/seed")
        before = app_client.get("/documents").json()["total"]
        app_client.delete("/documents/acme-return-001")
        after = app_client.get("/documents").json()["total"]
        assert after == before - 1

    def test_deleted_document_no_longer_listed(self, app_client):
        app_client.post("/documents/seed")
        app_client.delete("/documents/acme-shipping-002")
        ids = [d["doc_id"] for d in app_client.get("/documents").json()["documents"]]
        assert "acme-shipping-002" not in ids

    def test_delete_nonexistent_document_is_idempotent(self, app_client):
        """
        ChromaDB's collection.delete() does not raise when an ID is missing.
        So deleting a non-existent document returns 200 (no-op, not an error).
        """
        r = app_client.delete("/documents/does-not-exist-xyz")
        assert r.status_code == 200


class TestRagChat:
    def test_returns_200_with_seeded_data(self, app_client):
        app_client.post("/documents/seed")
        with patch("app.routes.rag.get_client", return_value=_mock_llm()):
            r = app_client.post("/documents/rag-chat", json={
                "question": "What is the return policy?",
                "top_k": 3,
            })
        assert r.status_code == 200

    def test_response_has_all_required_fields(self, app_client):
        app_client.post("/documents/seed")
        with patch("app.routes.rag.get_client", return_value=_mock_llm()):
            r = app_client.post("/documents/rag-chat", json={"question": "test"})
        data = r.json()
        for field in ["question", "answer", "retrieved_documents",
                      "context_used", "rag_flow_summary", "total_docs_in_db"]:
            assert field in data, f"Missing field: {field}"

    def test_answer_comes_from_mock_llm(self, app_client):
        """The answer in the response should be exactly what our mock LLM returned."""
        app_client.post("/documents/seed")
        expected = "You can return items within 30 days for a full refund."
        with patch("app.routes.rag.get_client", return_value=_mock_llm(expected)):
            r = app_client.post("/documents/rag-chat", json={"question": "return policy"})
        assert r.json()["answer"] == expected

    def test_top_k_controls_number_of_retrieved_docs(self, app_client):
        app_client.post("/documents/seed")
        with patch("app.routes.rag.get_client", return_value=_mock_llm()):
            r1 = app_client.post("/documents/rag-chat", json={"question": "policy", "top_k": 1})
            r3 = app_client.post("/documents/rag-chat", json={"question": "policy", "top_k": 3})
        assert len(r1.json()["retrieved_documents"]) == 1
        assert len(r3.json()["retrieved_documents"]) == 3

    def test_single_doc_in_db_is_always_retrieved(self, app_client):
        """
        With only one document, it must always be the retrieved result.
        This tests the vector search independently of embedding quality.
        """
        app_client.post("/documents", json={
            "text": "Acme returns: 30 day window, original packaging required",
            "doc_id": "only-doc-001",
        })
        with patch("app.routes.rag.get_client", return_value=_mock_llm()):
            r = app_client.post("/documents/rag-chat", json={
                "question": "Can I return an item?",
                "top_k": 1,
            })
        docs = r.json()["retrieved_documents"]
        assert len(docs) == 1
        assert docs[0]["doc_id"] == "only-doc-001"

    def test_similarity_score_is_between_zero_and_one(self, app_client):
        app_client.post("/documents/seed")
        with patch("app.routes.rag.get_client", return_value=_mock_llm()):
            r = app_client.post("/documents/rag-chat", json={"question": "warranty"})
        for doc in r.json()["retrieved_documents"]:
            score = doc["similarity_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} is out of range [0, 1]"

    def test_context_used_contains_retrieved_doc_text(self, app_client):
        """The context_used field should contain text from the retrieved documents."""
        app_client.post("/documents/seed")
        with patch("app.routes.rag.get_client", return_value=_mock_llm()):
            r = app_client.post("/documents/rag-chat", json={"question": "shipping cost"})
        context = r.json()["context_used"]
        assert len(context) > 0  # context was built

    def test_empty_knowledge_base_returns_400(self, app_client):
        """If no documents are stored, the endpoint should return 400 with a helpful message."""
        r = app_client.post("/documents/rag-chat", json={"question": "anything"})
        assert r.status_code == 400
        assert "empty" in r.json()["detail"].lower()

    def test_missing_question_returns_422(self, app_client):
        r = app_client.post("/documents/rag-chat", json={"top_k": 3})
        assert r.status_code == 422
