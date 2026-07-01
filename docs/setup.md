# Setup & Running Tests

---

## Setup

Do this once. Takes about 2 minutes.

### Step 1 — Get a free Gemini API key
Go to https://aistudio.google.com/app/apikey → click "Create API key" → copy it.

### Step 2 — Create virtual environment
```bash
cd /Users/gushah/dev/ai_learning
python3 -m venv .venv
```

### Step 3 — Activate it
```bash
source .venv/bin/activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 — Set your API key
```bash
export GEMINI_API_KEY="paste-your-key-here"
```
> Tip: add this line to your `~/.zshrc` so you don't have to repeat it every session.

### Step 6 — Start the FastAPI server
```bash
.venv/bin/python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

### Step 6b — (Optional) Start the MCP server in a second terminal
Only needed for `POST /mcp-chat`. Open a new terminal tab:
```bash
cd /Users/gushah/dev/ai_learning/ai_agent
export GEMINI_API_KEY="paste-your-key-here"
.venv/bin/python mcp_server/server.py
```
You should see: `URL: http://localhost:8001/mcp`

### Step 7 — Open the interactive docs
Go to http://127.0.0.1:8000/docs in your browser.
Every endpoint is listed there. You can run them directly from the browser — no curl needed.

---

## Running the Test Suite

Tests verify all 4 flows **without** a Gemini API key and **without** writing to disk.
They use in-memory ChromaDB and mocked LLM calls, so they run in ~1 second.

```bash
# From the ai_agent/ folder with the venv active:
.venv/bin/python -m pytest tests/ -v
```

To also see test coverage:
```bash
.venv/bin/python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

### What the tests cover

| File | What it tests | Mocking strategy |
|---|---|---|
| `tests/test_info.py` | `GET /`, `/models`, `/flow-explained` | None needed — static data |
| `tests/test_schemas.py` | Pydantic validation (accepts / rejects data) | None — pure Python |
| `tests/test_rag.py` | All RAG endpoints (add, list, delete, rag-chat) | ChromaDB → in-memory; LLM → `MagicMock` |
| `tests/test_chat.py` | `POST /chat` request/response shape | `run_agent()` → fake `ChatResponse` |
| `tests/test_multi_agent.py` | `POST /multi-agent-chat` structure | `run_multi_agent()` → fake `MultiAgentResponse` |

> **Key technique:** `conftest.py` defines a `FakeEmbeddingFn` that returns deterministic vectors without calling Gemini. Every test gets a fresh isolated ChromaDB collection — no test ever touches the real `chroma_db/` folder.
