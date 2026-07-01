# tests/test_info.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests for informational endpoints: GET /  /models  /flow-explained
#
# These endpoints return static data — no Gemini API, no ChromaDB.
# So we use a plain TestClient with no mocking needed at all.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRootEndpoint:
    """GET / — health check and endpoint directory."""

    def test_returns_200(self):
        assert client.get("/").status_code == 200

    def test_status_is_ok(self):
        assert client.get("/").json()["status"] == "ok"

    def test_shows_all_four_flows(self):
        """All 4 flows (Agent, RAG, MCP, Multi-Agent) should be listed."""
        endpoints = client.get("/").json()["endpoints"]
        keys = list(endpoints.keys())
        assert any("Flow 1" in k for k in keys), "Flow 1 (Agent) missing"
        assert any("Flow 2" in k for k in keys), "Flow 2 (RAG) missing"
        assert any("Flow 3" in k for k in keys), "Flow 3 (MCP) missing"
        assert any("Flow 4" in k for k in keys), "Flow 4 (Multi-Agent) missing"

    def test_has_quick_start_tip(self):
        assert "quick_start" in client.get("/").json()

    def test_multi_agent_endpoint_listed(self):
        body = str(client.get("/").json())
        assert "/multi-agent-chat" in body


class TestModelsEndpoint:
    """GET /models — list of supported Gemini model IDs."""

    def test_returns_200(self):
        assert client.get("/models").status_code == 200

    def test_returns_list_of_models(self):
        models = client.get("/models").json()["models"]
        assert isinstance(models, list)
        assert len(models) >= 2

    def test_default_model_is_present(self):
        ids = [m["id"] for m in client.get("/models").json()["models"]]
        assert "gemini-2.5-flash" in ids

    def test_each_model_has_id_and_description(self):
        for m in client.get("/models").json()["models"]:
            assert "id" in m, "Model missing 'id' field"
            assert "description" in m, "Model missing 'description' field"


class TestFlowExplainedEndpoint:
    """GET /flow-explained — plain-English architecture guide."""

    def test_returns_200(self):
        assert client.get("/flow-explained").status_code == 200

    def test_has_step_types_section(self):
        assert "step_types" in client.get("/flow-explained").json()

    def test_has_architecture_section(self):
        assert "architecture" in client.get("/flow-explained").json()

    def test_includes_all_key_step_types(self):
        steps = client.get("/flow-explained").json()["step_types"]
        for expected in ["user_input", "thought", "google_search_call",
                         "google_search_result", "model_output"]:
            assert expected in steps, f"Step type '{expected}' missing from /flow-explained"
