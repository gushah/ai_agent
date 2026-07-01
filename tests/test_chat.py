# tests/test_chat.py
# ─────────────────────────────────────────────────────────────────────────────
# Tests for POST /chat (Agent flow with Google Search).
#
# We mock run_agent() so tests don't call the real Gemini API.
# This lets us test:
#   - The endpoint accepts valid input and returns the right shape
#   - It rejects invalid input with 422
#   - The custom model parameter is forwarded correctly
# ─────────────────────────────────────────────────────────────────────────────

from unittest.mock import patch

from app.models.schemas import AgentStep, ChatResponse


def make_fake_chat_response(question: str = "test question") -> ChatResponse:
    """
    Build a realistic ChatResponse without calling Gemini.
    Used as the return value when we mock run_agent().
    """
    return ChatResponse(
        question=question,
        model_used="gemini-2.5-flash",
        total_steps=3,
        agent_flow_summary=[
            "[0] USER  → User Question",
            "[1] AGENT → Tool Call → Google Search",
            "[2] AGENT → Final Answer from LLM",
        ],
        steps=[
            AgentStep(
                step_index=0, step_type="user_input", role="user",
                label="User Question", detail="Your question", data={},
            ),
            AgentStep(
                step_index=1, step_type="google_search_call", role="agent",
                label="Google Search", detail="Searching...",
                data={"queries": ["test question"]},
            ),
            AgentStep(
                step_index=2, step_type="model_output", role="agent",
                label="Final Answer", detail="LLM answered",
                data={"text": "This is the answer."},
            ),
        ],
        final_answer="This is the answer.",
    )


class TestChatEndpoint:
    def test_valid_request_returns_200(self, app_client):
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "What is 2 + 2?"})
        assert r.status_code == 200

    def test_response_has_all_required_fields(self, app_client):
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "test"})
        data = r.json()
        for field in ["question", "model_used", "total_steps",
                      "agent_flow_summary", "steps", "final_answer"]:
            assert field in data, f"Missing field: {field}"

    def test_question_is_echoed_in_response(self, app_client):
        question = "What is the capital of France?"
        fake = make_fake_chat_response(question)
        with patch("app.routes.chat.run_agent", return_value=fake):
            r = app_client.post("/chat", json={"message": question})
        assert r.json()["question"] == question

    def test_steps_is_a_list(self, app_client):
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "test"})
        assert isinstance(r.json()["steps"], list)

    def test_agent_flow_summary_is_a_list(self, app_client):
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "test"})
        assert isinstance(r.json()["agent_flow_summary"], list)
        assert len(r.json()["agent_flow_summary"]) > 0

    def test_missing_message_returns_422(self, app_client):
        """Pydantic validation must reject a body with no 'message' field."""
        r = app_client.post("/chat", json={})
        assert r.status_code == 422

    def test_custom_model_is_forwarded_to_run_agent(self, app_client):
        """
        When the user sends model='gemini-2.5-pro', run_agent() should
        receive that model name, not the default.
        """
        captured = {}

        def fake_run_agent(message, model, **kwargs):
            captured["model"] = model
            return make_fake_chat_response()

        with patch("app.routes.chat.run_agent", side_effect=fake_run_agent):
            app_client.post("/chat", json={"message": "test", "model": "gemini-2.5-pro"})

        assert captured.get("model") == "gemini-2.5-pro"

    def test_step_types_are_strings(self, app_client):
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "test"})
        for step in r.json()["steps"]:
            assert isinstance(step["step_type"], str)
            assert isinstance(step["role"], str)


class TestConversationMemory:
    """Tests for the session_id / conversation memory feature."""

    def test_response_includes_session_id(self, app_client):
        """Every response must echo back a session_id."""
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "Hello"})
        assert "session_id" in r.json()
        assert r.json()["session_id"] is not None

    def test_omitting_session_id_creates_new_session(self, app_client):
        """Two requests without session_id should get different session_ids."""
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r1 = app_client.post("/chat", json={"message": "First"})
            r2 = app_client.post("/chat", json={"message": "Second"})
        assert r1.json()["session_id"] != r2.json()["session_id"]

    def test_session_id_is_echoed_when_provided(self, app_client):
        """When the caller passes a session_id, the same id must come back."""
        sid = "my-test-session-42"
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r = app_client.post("/chat", json={"message": "Hello", "session_id": sid})
        assert r.json()["session_id"] == sid

    def test_follow_up_injects_history_into_message(self, app_client):
        """
        The second request in a session should receive the previous turn
        injected into the message passed to run_agent().
        """
        captured = []

        def fake_run_agent(message, model, **kwargs):
            captured.append(message)
            return make_fake_chat_response(message)

        with patch("app.routes.chat.run_agent", side_effect=fake_run_agent):
            r1 = app_client.post("/chat", json={"message": "What is RAG?"})
            sid = r1.json()["session_id"]
            app_client.post("/chat", json={"message": "Give an example", "session_id": sid})

        # First call: no history yet — message is sent as-is
        assert captured[0] == "What is RAG?"
        # Second call: history prepended
        assert "Previous conversation:" in captured[1]
        assert "What is RAG?" in captured[1]
        assert "Give an example" in captured[1]

    def test_question_in_response_is_original_not_augmented(self, app_client):
        """
        Even though we inject history context into the message sent to the LLM,
        the `question` field in the response must show the user's original text.
        """
        with patch("app.routes.chat.run_agent", return_value=make_fake_chat_response()):
            r1 = app_client.post("/chat", json={"message": "First question"})
            sid = r1.json()["session_id"]
            r2 = app_client.post(
                "/chat", json={"message": "Follow-up question", "session_id": sid}
            )
        assert r2.json()["question"] == "Follow-up question"
