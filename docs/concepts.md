# Key Concepts — Read This First

Before touching any code, read these. Each concept is one paragraph with a real-world analogy.

---

### What is an LLM?
A Large Language Model (like Gemini) is a neural network trained on billions of text documents. It predicts the next word, over and over, to produce responses. It has a "knowledge cutoff" — it knows nothing about events after its training ended. It also knows nothing about *your* private documents.

> **Real-world analogy:** Imagine a person who has read every book, article, and website ever written — but was locked in a room before today's newspaper arrived. They know an enormous amount, but nothing after their training date, and nothing about your personal notes.

---

### What is an AI Agent?
A regular LLM just takes a prompt and gives an answer. An **AI Agent** is smarter — it can decide to use *tools* (like Google Search) to get extra information before answering. It loops: think → act → observe the result → think again → act again → answer. You can see every loop in this project.

> **Real-world analogy:** The difference between asking a friend a question (they just answer from memory) vs. hiring a research assistant (they say "let me look that up first", go check sources, then come back with a well-researched answer). The research assistant is the agent.

---

### What is RAG?
**Retrieval Augmented Generation**. Instead of relying on the LLM's training data, you store *your own documents* in a vector database. When a question comes in, the most relevant documents are retrieved and given to the LLM as context. The LLM then answers using *your documents* as its source of truth — not the internet, not its training data.

> **Real-world analogy:** Before asking an expert a question, you hand them a folder of your company's internal documents and say: "Answer using ONLY what's in this folder." They can't use their outside knowledge. This ensures answers are grounded in YOUR data — perfect for private or company-specific information.

---

### What is a Vector Database?
A normal database finds exact matches (`WHERE name = 'AI'`). A vector database finds *meaning matches*. It converts text into a list of numbers (a "vector" or "embedding") that represents the text's meaning. Texts with similar meanings produce similar numbers. So "machine learning" and "neural network" will be found as related, even though they share no words.

> **Real-world analogy:** A regular library organises books alphabetically. A vector database is like a library where books are shelved by *topic similarity* — so "How to train a dog" ends up next to "Animal behaviour training", even though the words are completely different. You find things by meaning, not by spelling.

---

### What are Embeddings?
An embedding model (we use Gemini's `text-embedding-004`) converts any text into a list of 768 numbers. These numbers encode the *meaning*. Similar meaning → numbers are close together in space. This is what makes semantic search possible.

> **Real-world analogy:** Think of a GPS coordinate for meaning. The word "happy" might be at coordinates (0.2, 0.8, ...) and "joyful" at (0.21, 0.79, ...) — they're very close. "Sad" is far away. "Car" is in a completely different direction. Distance between coordinates = distance between meanings.

---

### What is FastAPI?
A Python web framework that turns Python functions into HTTP endpoints. It automatically validates your request data (using Pydantic), generates interactive docs at `/docs`, and is one of the fastest Python frameworks available.

> **Real-world analogy:** FastAPI is like a restaurant. The menu at `/docs` shows all available dishes (endpoints). You place an order (HTTP request with JSON body). The kitchen (your Python function) prepares it. The waiter returns your order (JSON response). Pydantic is the waiter who checks your order is valid before sending it to the kitchen.

---

### What is Multi-Agent?
A single AI agent can only do so many things well. **Multi-Agent** means you create several specialist agents — each focused on one job — and an **orchestrator** coordinates them. Agent 1 might search the internet. Agent 2 might search your private documents. Agent 3 might combine their outputs into a final answer. Each agent is just a focused LLM call with a specific prompt and specific tools.

> **Real-world analogy:** Instead of asking one person to research a topic, write a report, AND fact-check it — you hire a research team. The researcher finds facts, the archivist checks the internal records, and the editor combines everything into the final document. Better results because everyone stays in their lane.

> **Multi-Agent vs MCP:** In MCP, the LLM autonomously picks which tools to use. In Multi-Agent, *your code* decides which agents to run and in what order. You have more control and visibility.

---

### What is MCP (Model Context Protocol)?
MCP is an open standard created by Anthropic — think of it as a **USB-C port for AI tools**. Before MCP, every AI tool integration was custom-built differently. MCP standardises the way an LLM discovers and calls external tools. You build an MCP server that *exposes functions*, and any LLM that speaks MCP can call those functions. In this project the MCP server exposes your ChromaDB knowledge base as callable tools (`search_knowledge_base`, `add_document_to_kb`, `get_kb_stats`). The LLM then autonomously decides when to call them.

> **Real-world analogy:** Before USB-C, every device had a different charger. USB-C standardised the plug so any device works with any charger. MCP does the same for AI tools — your ChromaDB "plugin" works with any AI model that speaks MCP, not just Gemini. You write the server once; any LLM can use it.

---

### What is the difference between RAG and MCP?
- **RAG (`/rag-chat`)** — *You* control the flow: your code searches ChromaDB, injects context, then asks the LLM. Simple and predictable.
- **MCP (`/mcp-chat`)** — *The LLM* controls the flow: you give it the tool, and it decides when to call `search_knowledge_base` on its own. More autonomous and flexible.

---

### What is Pydantic?
A Python library that validates data shapes using type hints. In FastAPI, every request body and response is a Pydantic model. If you send the wrong data type, FastAPI rejects it with a clear error before it ever reaches your code. All models are in `app/models/schemas.py`.

> **Real-world analogy:** A form at a government office. The form defines exactly what fields are required, what type each field must be (text, number, date), and which are optional. If you submit it wrong, the clerk rejects it at the window before it goes to the back office. Pydantic is that form — it catches bad data early.

---

### What is the google-genai SDK?
The official Python client library for Google's Gemini API. In this project it does two things: (1) `client.interactions.create()` — runs the full AI agent loop and returns every step, (2) `client.models.embed_content()` — converts text into embedding vectors for ChromaDB.

> **Real-world analogy:** A phone app for ordering food from a restaurant. Without the app you'd have to call the restaurant, know the exact menu codes, speak their language, etc. The SDK handles all that complexity — you just say `client.interactions.create(message)` and it handles authentication, formatting, API calls, and parsing the response.

---

## Project Structure

```
ai_learning/
│
├── main.py                        ← Start here. Creates the app, wires all routes.
│
├── app/
│   ├── config.py                  ← Settings: which tools, temperature, model name
│   ├── client.py                  ← Gemini SDK client (created once, reused everywhere)
│   │
│   ├── models/
│   │   └── schemas.py             ← All data shapes (what goes in, what comes out)
│   │                                 ChatRequest, AgentStep, ChatResponse
│   │                                 DocumentIn, RagRequest, RagResponse
│   │
│   ├── agent/                     ← AI Agent logic
│   │   ├── runner.py              ← THE CORE: calls Gemini, collects all steps
│   │   ├── parser.py              ← Converts each raw SDK step → readable AgentStep
│   │   └── multi_runner.py        ← Orchestrates 3 specialist agents (multi-agent)
│   │
│   ├── vectordb/                  ← Vector Database logic
│   │   ├── store.py               ← ChromaDB setup + Gemini embedding function
│   │   └── retriever.py           ← add_document(), search(), list_all_documents()
│   │
│   └── routes/
│       ├── chat.py                ← POST /chat       (Agent + Google Search)
│       ├── rag.py                 ← POST /documents/rag-chat  (Manual RAG)
│       ├── mcp_chat.py            ← POST /mcp-chat   (Agent + Google Search + ChromaDB via MCP)
│       ├── multi_agent.py         ← POST /multi-agent-chat  (3 specialist agents)
│       └── info.py                ← GET /,  GET /models,  GET /flow-explained
│
├── mcp_server/
│   └── server.py                  ← MCP Server — exposes ChromaDB as tools the LLM can call
│                                    Tools: search_knowledge_base, add_document_to_kb, get_kb_stats
│                                    Runs separately on port 8001
│
├── tests/                         ← 73 tests — run with: .venv/bin/python -m pytest tests/ -v
│   ├── conftest.py                ← FakeEmbeddingFn + in-memory ChromaDB fixtures
│   ├── test_info.py               ← Info endpoint tests (no mocking)
│   ├── test_schemas.py            ← Pydantic validation tests
│   ├── test_rag.py                ← Full RAG flow tests
│   ├── test_chat.py               ← /chat tests (mocked run_agent)
│   └── test_multi_agent.py        ← /multi-agent-chat tests
│
├── chroma_db/                     ← ChromaDB data (created automatically on first use)
├── requirements.txt               ← Python dependencies
└── agent_flow_diagram.svg         ← Visual diagram — open in browser
```
