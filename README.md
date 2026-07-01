# AI Agent + RAG — Learning Project

A hands-on FastAPI app that makes **every internal step of an AI agent visible**.
Built for beginners who want to deeply understand how AI agents, LLMs, vector databases, and RAG actually work — not just use them as black boxes.

Open `agent_flow_diagram.svg` in your browser to see the full visual diagram.

---

## Table of Contents

1. [Key Concepts — Read First](#key-concepts--read-first)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
4. [Testing All APIs — Step by Step](#testing-all-apis--step-by-step)
5. [Understanding the Responses](#understanding-the-responses)
6. [How the Code Flows](#how-the-code-flows)

---

## Key Concepts — Read First

Before touching any code, read these. Each concept is one paragraph.

### What is an LLM?
A Large Language Model (like Gemini) is a neural network trained on billions of text documents. It predicts the next word, over and over, to produce responses. It has a "knowledge cutoff" — it knows nothing about events after its training ended. It also knows nothing about *your* private documents.

### What is an AI Agent?
A regular LLM just takes a prompt and gives an answer. An **AI Agent** is smarter — it can decide to use *tools* (like Google Search) to get extra information before answering. It loops: think → act → observe the result → think again → act again → answer. You can see every loop in this project.

### What is RAG?
**Retrieval Augmented Generation**. Instead of relying on the LLM's training data, you store *your own documents* in a vector database. When a question comes in, the most relevant documents are retrieved and given to the LLM as context. The LLM then answers using *your documents* as its source of truth — not the internet, not its training data.

### What is a Vector Database?
A normal database finds exact matches (`WHERE name = 'AI'`). A vector database finds *meaning matches*. It converts text into a list of numbers (a "vector" or "embedding") that represents the text's meaning. Texts with similar meanings produce similar numbers. So "machine learning" and "neural network" will be found as related, even though they share no words.

### What are Embeddings?
An embedding model (we use Gemini's `text-embedding-004`) converts any text into a list of 768 numbers. These numbers encode the *meaning*. Similar meaning → numbers are close together in space. This is what makes semantic search possible.

### What is FastAPI?
A Python web framework that turns Python functions into HTTP endpoints. It automatically validates your request data (using Pydantic), generates interactive docs at `/docs`, and is one of the fastest Python frameworks available.

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
│   │   └── parser.py             ← Converts each raw SDK step → readable AgentStep
│   │
│   ├── vectordb/                  ← Vector Database logic
│   │   ├── store.py               ← ChromaDB setup + Gemini embedding function
│   │   └── retriever.py          ← add_document(), search(), list_all_documents()
│   │
│   └── routes/
│       ├── chat.py                ← POST /chat  (Agent flow)
│       ├── rag.py                 ← POST /documents/rag-chat  (RAG flow)
│       └── info.py                ← GET /,  GET /models,  GET /flow-explained
│
├── chroma_db/                     ← ChromaDB data (created automatically on first use)
├── requirements.txt               ← Python dependencies
├── README.md                      ← This file
└── agent_flow_diagram.svg         ← Visual diagram — open in browser
```

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

### Step 6 — Start the server
```bash
.venv/bin/uvicorn main:app --reload --port 8000
```

You should see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

### Step 7 — Open the interactive docs
Go to http://127.0.0.1:8000/docs in your browser.
Every endpoint is listed there. You can run them directly from the browser — no curl needed.

---

## Testing All APIs — Step by Step

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

**What it does:** Loads 7 sample documents about RAG, embeddings, ChromaDB, AI agents, LLMs, and FastAPI into ChromaDB. Each document is converted to a 768-number vector by Gemini's embedding model and saved to disk (`chroma_db/` folder).

**What you see:**
```json
{
  "message": "Added 7 sample documents.",
  "added_ids": ["rag-001", "vec-001", "emb-001", ...],
  "total_in_db": 7,
  "tip": "Now try POST /rag-chat with a question like 'What is RAG?'"
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
  "text": "FastAPI automatically generates interactive API documentation at the /docs endpoint using OpenAPI and Swagger UI. This makes it very easy to test endpoints without writing any code.",
  "metadata": {
    "source": "my notes",
    "topic": "FastAPI"
  }
}
```

**What happens:** Your text is sent to Gemini's `text-embedding-004` model, which returns a 768-number vector representing the meaning. That vector + your text is saved to ChromaDB. It will now be searchable by meaning.

---

### 🟠 STEP G — Ask a question using your knowledge base (RAG flow)

**Endpoint:** `POST /documents/rag-chat`

In docs: click **POST /documents/rag-chat → Try it out** → paste this → Execute:
```json
{
  "question": "What is RAG and how does it work?",
  "top_k": 3
}
```

Or with curl:
```bash
curl -X POST http://127.0.0.1:8000/documents/rag-chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG and how does it work?", "top_k": 3}'
```

**What you see:** (read `rag_flow_summary` first)
```json
{
  "rag_flow_summary": [
    "[1] Embedded question using Gemini text-embedding-004",
    "[2] Searched 7 documents in ChromaDB → retrieved top 3",
    "    • Doc 'rag-001' (similarity: 0.94) — RAG stands for Retrieval...",
    "    • Doc 'vec-001' (similarity: 0.81) — A vector database stores...",
    "    • Doc 'emb-001' (similarity: 0.76) — An embedding is a list...",
    "[3] Built context block from 3 retrieved documents",
    "[4] Sent prompt to gemini-2.5-flash with context injected",
    "[5] LLM answered using ONLY the retrieved context (no internet)"
  ],
  "retrieved_documents": [
    {
      "doc_id": "rag-001",
      "text": "RAG stands for Retrieval Augmented Generation...",
      "similarity_score": 0.94,
      "metadata": {"topic": "RAG", "source": "AI glossary"}
    }
  ],
  "context_used": "[Document 1 | similarity: 0.94]\nRAG stands for...",
  "answer": "RAG (Retrieval Augmented Generation) works by..."
}
```

**What is happening inside:**
| step | what is actually happening |
|---|---|
| Embed question | `"What is RAG?"` → 768-number vector via Gemini embedding |
| Search ChromaDB | Vector compared to all stored vectors using cosine similarity |
| Retrieve top 3 | 3 most semantically similar documents returned with scores |
| Build context | Documents formatted into a text block |
| LLM prompt | `"Answer using ONLY this context: [docs] QUESTION: What is RAG?"` |
| LLM answers | Gemini reads only the provided context — cannot make up info |

**Experiment 1:** Ask `"What is ChromaDB?"` — it should find the ChromaDB document.

**Experiment 2:** Ask `"What is the weather today?"` — it will say it doesn't have that information, because weather is not in your documents. This shows the LLM is actually constrained to your knowledge base.

**Experiment 3:** Change `top_k` to 1 vs 5 — see how fewer/more documents affect the answer.

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

You'll see the RAG answer is grounded in `emb-001` (your embedding document), while the Agent answer comes from a Google Search.

---

### 🔴 STEP I — Delete a document

**Endpoint:** `DELETE /documents/{doc_id}`

In docs: click **DELETE /documents/{doc_id} → Try it out** → enter `emb-001` → Execute

Then ask `"What is an embedding?"` again via RAG — it will now find different (less relevant) documents.

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

### Similarity score guide

| score | meaning |
|---|---|
| 0.90–1.00 | Near-identical meaning |
| 0.75–0.89 | Very relevant |
| 0.50–0.74 | Somewhat related |
| below 0.50 | Probably not relevant |

---

## How the Code Flows

### Agent flow (POST /chat)
```
HTTP request
    → app/routes/chat.py          validates input
    → app/agent/runner.py         calls Gemini interactions API
    → app/agent/parser.py         converts each SDK step → AgentStep
    → app/models/schemas.py       shapes the ChatResponse
    → HTTP response (JSON)
```

### RAG flow (POST /documents/rag-chat)
```
HTTP request
    → app/routes/rag.py           validates input
    → app/vectordb/retriever.py   search(question, top_k)
        → app/vectordb/store.py   GeminiEmbeddingFunction → ChromaDB
    → app/routes/rag.py           builds context + LLM prompt
    → app/client.py               calls Gemini generate_content()
    → HTTP response (JSON)
```

### When you add a document (POST /documents)
```
HTTP request
    → app/routes/rag.py           validates DocumentIn
    → app/vectordb/retriever.py   add_document(text, metadata)
        → app/vectordb/store.py   GeminiEmbeddingFunction converts text → vector
        → ChromaDB                saves vector + text + metadata to chroma_db/ folder
    → HTTP response (doc_id)
```

---

## Files to Read in Order (if studying the code)

1. **`app/config.py`** — 15 lines. What tools and settings the agent has.
2. **`app/models/schemas.py`** — The data shapes. Read this to understand what every endpoint returns.
3. **`app/vectordb/store.py`** — How ChromaDB and Gemini embeddings are connected.
4. **`app/vectordb/retriever.py`** — How documents are added and searched.
5. **`app/agent/runner.py`** — How the Gemini agent API is called.
6. **`app/agent/parser.py`** — How each step type is decoded into a readable format.
7. **`app/routes/chat.py`** — The agent HTTP endpoint.
8. **`app/routes/rag.py`** — The RAG HTTP endpoints (most interesting file for RAG).
9. **`main.py`** — Last. Just app setup and router registration.
