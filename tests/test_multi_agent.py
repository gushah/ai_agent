# tests/test_multi_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests for POST /multi-agent-chat (Multi-Agent Orchestration).
#
# The multi-agent flow runs 3 specialist agents in sequence:
#   1. research_agent  — searches the internet (Google Search)
#   2. knowledge_agent — searches ChromaDB (internal KB)
#   3. synthesizer_agent — combines both answers with [Internet] and [KB] labels
#
# We mock run_multi_agent() so the test doesn't call the real Gemini API.
# ─────────────────────────────────────────────────────────────────────────────

from unittest.mock import patch

from app.models.schemas import AgentResult, MultiAgentResponse


def make_fake_multi_response(question: str = "What is the return policy?") -> MultiAgentResponse:
    """
    Build a realistic MultiAgentResponse without calling Gemini.
    Used as the return value when we mock run_multi_agent().
    """
    return MultiAgentResponse(
        question=question,
        model_used="gemini-2.5-flash",
        multi_agent_summary=[
            "[Agent 1] research_agent searched the internet for recent info",
            "[Agent 2] knowledge_agent searched ChromaDB knowledge base",
            "[Agent 3] synthesizer_agent combined both answers",
        ],
        agents=[
            AgentResult(
                agent_name="research_agent",
                role="Internet Researcher — searches live web",
                answer="Internet sources say returns vary by retailer.",
                flow_summary=["Searched Google for 'return policy best practices'"],
            ),
            AgentResult(
                agent_name="knowledge_agent",
                role="Knowledge Base Expert — searches ChromaDB",
                answer="Acme Corp accepts returns within 30 days with original packaging.",
                flow_summary=["Retrieved acme-return-001 (score=0.91)"],
            ),
            AgentResult(
                agent_name="synthesizer_agent",
                role="Synthesizer — combines internet + KB into one answer",
                answer=(
                    "[Internet] Returns vary by retailer, typically 30-90 days. "
                    "[Knowledge Base] Acme Corp: 30 days, original packaging required."
                ),
                flow_summary=["Combined both sources with clear labels"],
            ),
        ],
        final_answer=(
            "[Internet] Returns vary by retailer, typically 30-90 days. "
            "[Knowledge Base] Acme Corp: 30 days, original packaging required."
        ),
    )


class TestMultiAgentEndpoint:
    def test_valid_request_returns_200(self, app_client):
        with patch("app.routes.multi_agent.run_multi_agent", return_value=make_fake_multi_response()):
            r = app_client.post("/multi-agent-chat", json={"message": "What is the return policy?"})
        assert r.status_code == 200

    def test_response_has_all_required_fields(self, app_client):
        with patch("app.routes.multi_agent.run_multi_agent", return_value=make_fake_multi_response()):
            r = app_client.post("/multi-agent-chat", json={"message": "test"})
        data = r.json()
        for field in ["question", "model_used", "multi_agent_summary",
                      "agents", "final_answer"]:
            assert field in data, f"Missing field: {field}"

    def test_response_has_exactly_three_agents(self, app_client):
        with patch("app.routes.multi_agent.run_multi_agent", return_value=make_fake_multi_response()):
            r = app_client.post("/multi-agent-chat", json={"message": "test"})
        assert len(r.json()["agents"]) == 3

    def test_all_three_agent_names_are_present(self, app_client):
        with patch("app.routes.multi_agent.run_multi_agent", return_value=make_fake_multi_response()):
            r = app_client.post("/multi-agent-chat", json={"message": "test"})
        names = [a["agent_name"] for a in r.json()["agents"]]
        assert "research_agent" in names
        assert "knowledge_agent" in names
        assert "synthesizer_agent" in names

    def test_missing_message_returns_422(self, app_client):
        r = app_client.post("/multi-agent-chat", json={})
        assert r.status_code == 422

    def test_each_agent_has_a_non_empty_answer(self, app_client):
        with patch("app.routes.multi_agent.run_multi_agent", return_value=make_fake_multi_response()):
            r = app_client.post("/multi-agent-chat", json={"message": "test"})
        for agent in r.json()["agents"]:
            assert "answer" in agent
            assert len(agent["answer"]) > 0, f"{agent['agent_name']} has empty answer"

    def test_final_answer_is_non_empty(self, app_client):
        with patch("app.routes.multi_agent.run_multi_agent", return_value=make_fake_multi_response()):
            r = app_client.post("/multi-agent-chat", json={"message": "test"})
        assert len(r.json()["final_answer"]) > 0

    def test_question_is_echoed_in_response(self, app_client):
        fake = make_fake_multi_response("How long is the warranty?")
        with patch("app.routes.multi_agent.run_multi_agent", return_value=fake):
            r = app_client.post("/multi-agent-chat", json={"message": "How long is the warranty?"})
        assert r.json()["question"] == "How long is the warranty?"
