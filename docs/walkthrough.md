# Walkthrough — Testing All APIs Step by Step

Work through these in order. Each step builds on the last.

---

### 🔵 STEP A — Check the server is running

**Endpoint:** `GET /`

In browser: http://127.0.0.1:8000/

**What you see:**
```json
{
  "status": "ok",
  "message": "AI Agent Flow API is running.",
  "endpoints": { ... }
}
```
**What it means:** Server is healthy. All routes are registered.

---

### 🔵 STEP B — Learn the architecture (no LLM call, instant)

**Endpoint:** `GET /flow-explained`

In browser: http://127.0.0.1:8000/flow-explained

**What you see:** A full JSON breakdown of how an AI agent works — every step type explained in plain English. Read this before running `/chat`.

---

### 🟢 STEP C — Ask the AI Agent a question (Agent flow)

**Endpoint:** `POST /chat`

In docs: click **POST /chat → Try it out** → paste this body → Execute:
```json
{
  "message": "What are the latest breakthroughs in AI agents in 2026?"
}
```

Or with curl:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the latest breakthroughs in AI agents in 2026?"}'
```

**What you see:** (read `agent_flow_summary` first — it's the quickest overview)
```json
{
  "agent_flow_summary": [
    "[0] USER  → User Question",
    "[1] AGENT → Agent Thinking (internal)",
    "[2] AGENT → Tool Call → Google Search",
    "[3] TOOL  → Tool Result ← Google Search",
    "[4] AGENT → Agent Thinking (internal)",
    "[5] AGENT → Final Answer from LLM"
  ],
  "steps": [ ... full detail of each step ... ],
  "final_answer": "Here are the latest AI agent breakthroughs..."
}
```

**What is happening inside:**

| step | what the LLM is doing |
|---|---|
| `user_input` | Your question entered the system |
| `thought` | LLM silently reasons: "I need to search for this" — you never normally see this |
| `google_search_call` | LLM decides to call Google Search, sends queries |
| `google_search_result` | Search results (title, URL, snippet) come back to the LLM |
| `thought` | LLM reasons again: "Now I have enough to answer" |
| `model_output` | LLM writes the final answer using the search results |

**Experiment:** Try a question that doesn't need searching, like `"What is 2 + 2?"`. You'll see fewer steps — no `google_search_call` — because the LLM already knows the answer.

---

### 🟡 STEP D — Add sample documents to your knowledge base

**Endpoint:** `POST /documents/seed`

In docs: click **POST /documents/seed → Try it out → Execute** (no body needed)

Or with curl:
```bash
curl -X POST http://127.0.0.1:8000/documents/seed
```

**What it does:** Loads 7 Acme Corp business policy documents into ChromaDB (return policy, shipping, warranty, refunds, support hours, membership, order tracking). Each document is converted to a 768-number vector by Gemini's embedding model and saved to disk (`chroma_db/` folder).

**What you see:**
```json
{
  "message": "Added 7 Acme Corp business policy documents.",
  "added_ids": ["acme-return-001", "acme-shipping-002", "acme-warranty-003", "acme-refund-004", "acme-support-005", "acme-membership-006", "acme-orders-007"],
  "total_in_db": 7,
  "tip": "Now try POST /rag-chat with: 'What is the return policy?'"
}
```

---

### 🟡 STEP E — See what's in your knowledge base

**Endpoint:** `GET /documents`

In browser: http://127.0.0.1:8000/documents

**What you see:** All 7 documents with their IDs, text, and metadata. These are what ChromaDB has stored.

---

### 🟡 STEP F — Add your own document

**Endpoint:** `POST /documents`

In docs: click **POST /documents → Try it out** → paste this body → Execute:
```json
{
  "text": "Acme Corp Gift Wrapping: Gift wrapping is available for $3.99 per item. Add a personalised message card at no extra charge. Gift-wrapped items arrive in a branded Acme gift box with a ribbon. Select 'gift wrap' at checkout. Not available for oversized items.",
  "metadata": {
    "source": "Acme Corp Checkout Guide",
    "topic": "gift wrapping"
  }
}
```

**What happens:** Your text is sent to Gemini's `text-embedding-004` model, which returns a 768-number vector representing the meaning. That vector + your text is saved to ChromaDB. Now if a customer asks *"Do you do gift packaging?"* — this document will be retrieved, even though it says "gift wrapping" not "gift packaging".

---

### 🟠 STEP G — Ask a question using your knowledge base (RAG flow)

**Endpoint:** `POST /documents/rag-chat`

In docs: click **POST /documents/rag-chat → Try it out** → paste this → Execute:
```json
{
  "question": "What is the return policy?",
  "top_k": 3
}
```

Or with curl:
```bash
curl -X POST http://127.0.0.1:8000/documents/rag-chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the return policy?", "top_k": 3}'
```

**What you see:** (read `rag_flow_summary` first)
```json
{
  "rag_flow_summary": [
    "[1] Embedded question using Gemini text-embedding-004",
    "[2] Searched 7 documents in ChromaDB → retrieved top 3",
    "    • Doc 'acme-return-001' (similarity: 0.91) — Acme Corp Return Policy: Customers may...",
    "    • Doc 'acme-refund-004' (similarity: 0.78) — Acme Corp Refund Process: Refunds are...",
    "    • Doc 'acme-orders-007' (similarity: 0.61) — Acme Corp Order Tracking...",
    "[3] Built context block from 3 retrieved documents",
    "[4] Sent prompt to gemini-2.5-flash with context injected",
    "[5] LLM answered using ONLY the retrieved context (no internet)"
  ],
  "retrieved_documents": [
    {
      "doc_id": "acme-return-001",
      "text": "Acme Corp Return Policy: Customers may return...",
      "similarity_score": 0.91,
      "metadata": {"topic": "returns", "department": "customer_service"}
    }
  ],
  "context_used": "[Document 1 | similarity: 0.91]\nAcme Corp Return Policy...",
  "answer": "Acme Corp accepts returns within 30 days of purchase..."
}
```

**What is happening inside:**

| step | what is actually happening |
|---|---|
| Embed question | `"What is the return policy?"` → 768-number vector via Gemini embedding |
| Search ChromaDB | Vector compared to all 7 stored document vectors using cosine similarity |
| Retrieve top 3 | `acme-return-001` scores highest (return policy = most relevant meaning) |
| Build context | Documents formatted into a text block |
| LLM prompt | `"Answer using ONLY this context: [Acme docs] QUESTION: What is the return policy?"` |
| LLM answers | Reads only the Acme policy document — cannot make things up |

**Experiment 1:** Ask `"How long does delivery take?"` — ChromaDB should find `acme-shipping-002`. Notice the question uses "delivery" but the doc says "shipping" — vector search finds it anyway.

**Experiment 2:** Ask `"What is the weather today?"` — the LLM will say it doesn't have that information. Weather is not in Acme's documents. This proves the LLM is genuinely constrained to your knowledge base.

**Experiment 3:** Ask `"Can I get my money back?"` — no word matches "refund" but it should still find `acme-refund-004`. This is the clearest demonstration of why vector search beats keyword search.

**Experiment 4:** Change `top_k` from 3 to 1 — the answer becomes less complete because the LLM only sees one document. Change to 5 — it sees more context and can give a richer answer.

---

### 🔵 STEP H — Compare Agent vs RAG on the same question

Ask both endpoints the same question and compare the answers:

```bash
# Agent (uses Google Search — live internet)
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is an embedding?"}'

# RAG (uses your ChromaDB documents — your knowledge base)
curl -X POST http://127.0.0.1:8000/documents/rag-chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is an embedding?", "top_k": 2}'
```

You'll see the RAG answer is grounded in your seeded documents, while the Agent answer comes from a Google Search.

---

### 🔴 STEP I — Delete a document

**Endpoint:** `DELETE /documents/{doc_id}`

In docs: click **DELETE /documents/{doc_id} → Try it out** → enter `acme-return-001` → Execute

Then ask `"What is the return policy?"` again via RAG — it will now find different (less relevant) documents.

---

### 🟣 STEP J — MCP Chat (LLM picks its own tools autonomously)

**Requires:** MCP server running (Step 6b in [setup.md](setup.md)).

**Endpoint:** `POST /mcp-chat`

```bash
curl -X POST http://127.0.0.1:8000/mcp-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is RAG? Also find the latest AI agent news."}'  
```

**What makes this different from /chat and /rag-chat:**

| | `/chat` | `/rag-chat` | `/mcp-chat` |
|---|---|---|---|
| Knowledge source | Internet only | Your ChromaDB only | Both — LLM chooses |
| Who decides to search | LLM | Your code | LLM |
| Search triggered by | LLM thinking | You always search | LLM thinking |
| Tool protocol | Built-in | None (manual) | MCP standard |

**What you see in `agent_flow_summary`:**
```
[0] USER  → User Question
[1] AGENT → Agent Thinking (internal)
[2] AGENT → MCP Tool Call → search_knowledge_base   ← LLM called YOUR ChromaDB
[3] TOOL  → MCP Tool Result ← Knowledge Base        ← results returned via MCP
[4] AGENT → Tool Call → Google Search               ← LLM also searched internet
[5] TOOL  → Tool Result ← Google Search
[6] AGENT → Agent Thinking (internal)
[7] AGENT → Final Answer from LLM
```

**New step types you will see:**

| step_type | role | meaning |
|---|---|---|
| `mcp_server_tool_call` | agent | LLM called a function on your MCP server |
| `mcp_server_tool_result` | tool | MCP server ran the function and returned results |

**Experiment:** Ask `"What is the weather today?"` — the LLM will use Google Search because that's not in your knowledge base. Ask `"What is the Acme return policy?"` — the LLM will call `search_knowledge_base` because it finds it relevant. Ask `"Tell me about Acme's policies and today's AI news"` — it will use both tools.

---

### ⚪ STEP K — Multi-Agent Chat (3 specialists cooperate)

**Endpoint:** `POST /multi-agent-chat`

```bash
curl -X POST http://127.0.0.1:8000/multi-agent-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is RAG and how is it used in production AI systems?"}'
```

**What makes this different from everything else:**

You don't get one answer. You get **three agents' answers** plus a synthesized final:

| | What it does | Knowledge source |
|---|---|---|
| **research_agent** | Searches Google for current info | Internet |
| **knowledge_agent** | Searches ChromaDB for relevant docs | Your private KB |
| **synthesizer_agent** | Combines both into one answer | Both, labelled |

**What you see:**
```json
{
  "multi_agent_summary": [
    "[Agent 1] research_agent     → searched internet for: 'What is RAG...'",
    "[Agent 2] knowledge_agent    → searched ChromaDB knowledge base",
    "[Agent 3] synthesizer_agent  → combined both sources → final answer below"
  ],
  "agents": [
    {
      "agent_name": "research_agent",
      "role": "Internet Researcher — uses Google Search to find current information",
      "answer": "RAG (Retrieval Augmented Generation) is a technique that...",
      "flow_summary": ["[0] USER → User Question", "[1] AGENT → google_search_call", ...]
    },
    {
      "agent_name": "knowledge_agent",
      "role": "Knowledge Base Expert — searches your private ChromaDB documents",
      "answer": "Based on your documents: RAG stands for...",
      "flow_summary": ["Searched ChromaDB — retrieved 3 doc(s): ..."]
    },
    {
      "agent_name": "synthesizer_agent",
      "role": "Synthesizer — combines both agents' findings into one final answer",
      "answer": "[Internet] RAG is widely used in production... [Knowledge Base] Your docs explain...",
      "flow_summary": ["Combined research_agent + knowledge_agent outputs"]
    }
  ],
  "final_answer": "[Internet] RAG (Retrieval Augmented Generation)... [Knowledge Base] ..."
}
```

**Experiment 1:** Ask something NOT in your knowledge base, like `"What is the latest iPhone?"`. Knowledge agent will say "No relevant documents found." Synthesizer will use only the internet source.

**Experiment 2:** Compare `/chat` vs `/multi-agent-chat` on the same question. The multi-agent answer will have `[Internet]` and `[Knowledge Base]` labels, making sources completely transparent.

---

## Understanding the Responses

### Agent flow response fields (`POST /chat`)

| field | what it is |
|---|---|
| `agent_flow_summary` | Quick one-liner per step — read this first |
| `steps[].step_type` | The internal SDK type: `user_input`, `thought`, `google_search_call`, `google_search_result`, `model_output` |
| `steps[].role` | Who did this: `user`, `agent`, or `tool` |
| `steps[].detail` | Plain-English explanation |
| `steps[].data` | Structured data (search queries, search results, answer text) |
| `final_answer` | Just the final text — what you'd show to an end user |

### RAG flow response fields (`POST /documents/rag-chat`)

| field | what it is |
|---|---|
| `rag_flow_summary` | Quick step-by-step of what happened — read this first |
| `retrieved_documents` | Docs ChromaDB found, with similarity scores (0.0–1.0) |
| `context_used` | The exact text block injected into the LLM prompt |
| `answer` | The LLM's answer — constrained to the context |

### MCP flow response fields (`POST /mcp-chat`)
Same shape as `/chat` (ChatResponse). The difference is in the step types inside `steps[]`:

| step_type | role | meaning |
|---|---|---|
| `mcp_server_tool_call` | agent | LLM autonomously called a function on your MCP server |
| `mcp_server_tool_result` | tool | MCP server returned the function result back to the LLM |

The `data` field of `mcp_server_tool_call` tells you:
- `tool` — which function was called (`search_knowledge_base`, `add_document_to_kb`, `get_kb_stats`)
- `arguments` — what arguments the LLM passed to the function

### Multi-Agent flow response fields (`POST /multi-agent-chat`)

| field | what it is |
|---|---|
| `multi_agent_summary` | Quick 3-line overview — read this first |
| `agents[].agent_name` | `research_agent`, `knowledge_agent`, or `synthesizer_agent` |
| `agents[].role` | Human-readable description of what this agent does |
| `agents[].answer` | This agent's individual output |
| `agents[].flow_summary` | Steps this agent took (shows Google Search calls, ChromaDB results) |
| `final_answer` | The synthesizer agent's combined output |

### Similarity score guide

| score | meaning |
|---|---|
| 0.90–1.00 | Near-identical meaning |
| 0.75–0.89 | Very relevant |
| 0.50–0.74 | Somewhat related |
| below 0.50 | Probably not relevant |
