# Reference

---

## Which Flow Should I Use?

Ask yourself: *Where does the answer live?*

```
Is it on the internet / current events?
    YES → use /chat  (Agent flow)
    NO  → is it in my private documents?
              YES → use /rag-chat  (RAG flow) — fast, predictable, controlled
              MAYBE BOTH → use /mcp-chat  (MCP flow) — LLM decides which source(s) to use
```

| Situation | Use this |
|---|---|
| "What happened in AI last week?" | `/chat` — needs live internet |
| "Summarise our internal onboarding doc" | `/rag-chat` — your private document |
| "Explain RAG and also find any new RAG papers" | `/mcp-chat` — needs KB + internet, LLM decides |
| "Give me the best possible answer from all sources" | `/multi-agent-chat` — 3 specialists, full transparency |
| Testing the system, just understanding how it works | Start with `/chat` — simplest flow |

---

## Files to Read in Order (if studying the code)

1. **`app/config.py`** — What tools and settings the agent has.
2. **`app/models/schemas.py`** — All data shapes. Read this to know what every endpoint returns.
3. **`app/vectordb/store.py`** — How ChromaDB and Gemini embeddings are connected.
4. **`app/vectordb/retriever.py`** — How documents are added and searched.
5. **`app/agent/runner.py`** — The core: how Gemini is called with tools.
6. **`app/agent/parser.py`** — How every step type (including MCP) is decoded into readable format.
7. **`app/routes/chat.py`** — Agent endpoint (Google Search tool).
8. **`app/routes/rag.py`** — RAG endpoints (manual ChromaDB flow).
9. **`mcp_server/server.py`** — The MCP server: exposes ChromaDB as LLM-callable tools.
10. **`app/routes/mcp_chat.py`** — MCP endpoint (LLM + Google Search + ChromaDB).
11. **`app/agent/multi_runner.py`** — The orchestrator: 3 agents in sequence.
12. **`app/routes/multi_agent.py`** — Multi-agent endpoint.
13. **`main.py`** — Last. App setup and router registration.

---

## All Endpoints at a Glance

| Method | Endpoint | What it does | Needs MCP server? |
|--------|----------|--------------|-------------------|
| `GET`  | `/` | Health check | No |
| `GET`  | `/docs` | Interactive Swagger UI | No |
| `GET`  | `/flow-explained` | Plain-English architecture guide | No |
| `GET`  | `/models` | List Gemini models | No |
| `POST` | `/chat` | AI agent with Google Search — see every step | No |
| `POST` | `/documents/seed` | Load 7 Acme Corp policy documents into ChromaDB | No |
| `POST` | `/documents` | Add your own document to ChromaDB | No |
| `GET`  | `/documents` | List all stored documents | No |
| `DELETE` | `/documents/{id}` | Remove a document | No |
| `POST` | `/documents/rag-chat` | Ask question using your knowledge base (RAG) | No |
| `POST` | `/mcp-chat` | AI agent with Google Search **+** ChromaDB via MCP | **Yes** (port 8001) |
| `POST` | `/multi-agent-chat` | 3 specialist agents: research + knowledge + synthesizer | No |
