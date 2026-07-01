# tests/test_schemas.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests for Pydantic models in app/models/schemas.py
#
# What Pydantic does: validates data SHAPES at the API boundary.
# If you send wrong types or missing required fields, Pydantic raises
# ValidationError before the code ever runs. These tests confirm that.
#
# No FastAPI, no mocking, no HTTP — pure Python unit tests.
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from pydantic import ValidationError

from app.config import DEFAULT_MODEL
from app.models.schemas import (
    AgentResult,
    AgentStep,
    ChatRequest,
    ChatResponse,
    DocumentIn,
    MultiAgentResponse,
    RagRequest,
    RetrievedDoc,
)


class TestChatRequest:
    def test_valid_message(self):
        r = ChatRequest(message="Hello world")
        assert r.message == "Hello world"

    def test_default_model_is_applied(self):
        r = ChatRequest(message="test")
        assert r.model == DEFAULT_MODEL

    def test_custom_model_is_accepted(self):
        r = ChatRequest(message="test", model="gemini-2.5-pro")
        assert r.model == "gemini-2.5-pro"

    def test_missing_message_raises_validation_error(self):
        """Pydantic must reject a request body with no 'message' field."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest()
        assert "message" in str(exc_info.value)

    def test_empty_string_is_accepted(self):
        """Empty string is a valid string type — Pydantic does not reject it."""
        r = ChatRequest(message="")
        assert r.message == ""


class TestRagRequest:
    def test_valid_question(self):
        r = RagRequest(question="What is the return policy?")
        assert r.question == "What is the return policy?"

    def test_default_top_k_is_three(self):
        r = RagRequest(question="test")
        assert r.top_k == 3

    def test_custom_top_k(self):
        r = RagRequest(question="test", top_k=5)
        assert r.top_k == 5

    def test_missing_question_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RagRequest()


class TestDocumentIn:
    def test_minimal_valid(self):
        d = DocumentIn(text="Some document text")
        assert d.text == "Some document text"
        assert d.doc_id is None       # optional, defaults to None
        assert d.metadata == {}       # optional, defaults to empty dict

    def test_with_all_fields(self):
        d = DocumentIn(
            text="Acme return policy: 30 days.",
            doc_id="acme-return-001",
            metadata={"topic": "returns", "department": "customer_service"},
        )
        assert d.doc_id == "acme-return-001"
        assert d.metadata["topic"] == "returns"

    def test_missing_text_raises_validation_error(self):
        with pytest.raises(ValidationError):
            DocumentIn()


class TestAgentStep:
    def test_valid_step(self):
        s = AgentStep(
            step_index=0,
            step_type="user_input",
            role="user",
            label="User Question",
            detail="Your question entered the system",
            data={"text": "hello"},
        )
        assert s.step_index == 0
        assert s.step_type == "user_input"
        assert s.role == "user"

    def test_data_field_accepts_any_dict(self):
        """data field is dict[str, Any] — accepts nested structures."""
        s = AgentStep(
            step_index=1,
            step_type="google_search_call",
            role="agent",
            label="Google Search",
            detail="Searching...",
            data={"queries": ["AI news", "latest AI 2026"], "count": 2},
        )
        assert s.data["count"] == 2


class TestRetrievedDoc:
    def test_valid(self):
        d = RetrievedDoc(
            doc_id="acme-return-001",
            text="Return within 30 days",
            metadata={"topic": "returns"},
            similarity_score=0.91,
        )
        assert d.similarity_score == 0.91
        assert 0.0 <= d.similarity_score <= 1.0


class TestAgentResult:
    def test_minimal(self):
        a = AgentResult(agent_name="research_agent", role="Researcher", answer="42")
        assert a.agent_name == "research_agent"
        assert a.flow_summary == []  # defaults to empty list

    def test_with_flow_summary(self):
        a = AgentResult(
            agent_name="knowledge_agent",
            role="KB Expert",
            answer="Found in KB",
            flow_summary=["Retrieved acme-return-001 (score=0.91)"],
        )
        assert len(a.flow_summary) == 1


class TestMultiAgentResponse:
    def test_full_response(self):
        resp = MultiAgentResponse(
            question="What is the return policy?",
            model_used="gemini-2.5-flash",
            multi_agent_summary=["Agent 1 searched", "Agent 2 searched", "Agent 3 combined"],
            agents=[
                AgentResult(agent_name="research_agent", role="r1", answer="internet answer"),
                AgentResult(agent_name="knowledge_agent", role="r2", answer="kb answer"),
                AgentResult(agent_name="synthesizer_agent", role="r3", answer="combined"),
            ],
            final_answer="Combined answer with [Internet] and [Knowledge Base] labels",
        )
        assert len(resp.agents) == 3
        assert resp.agents[0].agent_name == "research_agent"
        assert resp.agents[2].agent_name == "synthesizer_agent"
