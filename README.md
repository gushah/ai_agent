# AI Agent + RAG + MCP — Learning Project

A hands-on FastAPI app that makes **every internal step of an AI agent visible**.
Built for beginners who want to deeply understand how AI agents, LLMs, vector databases, RAG, and MCP actually work — not just use them as black boxes.

Open `agent_flow_diagram.svg` in your browser to see the full visual diagram.

---

## The Big Picture — All 3 Flows at a Glance

This project shows you **3 different ways an AI can answer a question**. Each builds on the previous one.

```
YOUR QUESTION
     │
     ├─── Flow 1: AGENT  →  POST /chat
     │         Your question → FastAPI → Gemini LLM thinks → calls Google Search
     │         → reads live results → writes final answer
     │         Who searches: the LLM decides on its own
     │         Knowledge source: the live internet
     │
     ├─── Flow 2: RAG    →  POST /documents/rag-chat
     │         Your question → FastAPI → your code embeds it → searches ChromaDB
     │         → retrieves your documents → injects them → LLM reads ONLY those → answers
     │         Who searches: your code always searches (the LLM has no choice)
     │         Knowledge source: your private ChromaDB documents only
     │
     └─── Flow 3: MCP    →  POST /mcp-chat
               Your question → FastAPI → Gemini LLM thinks → autonomously calls
               Google Search AND/OR your ChromaDB (via MCP protocol) → answers
               Who searches: the LLM decides which tool(s) to use
               Knowledge source: internet + your documents — LLM picks
```

**One-sentence difference:** Flow 1 = LLM + internet. Flow 2 = your code + your documents. Flow 3 = LLM + both.

---

## Table of Contents

1. [Key Concepts — Read First](#key-concepts--read-first)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
4. [Testing All APIs — Step by Step](#testing-all-apis--step-by-step)
5. [Understanding the Responses](#understanding-the-responses)
6. [How the Code Flows](#how-the-code-flows)
7. [All Endpoints at a Glance](#all-endpoints-at-a-glance)

---

## Key Concepts — Read First

Before touching any code, read these. Each concept is one paragraph.

### What is an LLM?
A Large Language Model (like Gemini) is a neural network trained on billions of text documents. It predicts the next word, over and over, to produce responses. It has a "knowledge cutoff" — it knows nothing about events after its training ended. It also knows nothing about *your* private documents.

> **Real-world analogy:** Imagine a person who has read every book, article, and website ever written — but was locked in a room before today's newspaper arrived. They know an enormous amount, but nothing after their training date, and nothing about your personal notes.

### What is an AI Agent?
A regular LLM just takes a prompt and gives an answer. An **AI Agent** is smarter — it can decide to use *tools* (like Google Search) to get extra information before answering. It loops: think → act → observe the result → think again → act again → answer. You can see every loop in this project.

> **Real-world analogy:** The difference between asking a friend a question (they just answer from memory) vs. hiring a research assistant (they say "let me look that up first", go check sources, then come back with a well-researched answer). The research assistant is the agent.

### What is RAG?
**Retrieval Augmented Generation**. Instead of relying on the LLM's training data, you store *your own documents* in a vector database. When a question comes in, the most relevant documents are retrieved and given to the LLM as context. The LLM then answers using *your documents* as its source of truth — not the internet, not its training data.

> **Real-world analogy:** Before asking an expert a question, you hand them a folder of your company's internal documents and say: "Answer using ONLY what's in this folder." They can't use their outside knowledge. This ensures answers are grounded in YOUR data — perfect for private or company-specific information.

### What is a Vector Database?
A normal database finds exact matches (`WHERE name = 'AI'`). A vector database finds *meaning matches*. It converts text into a list of numbers (a "vector" or "embedding") that represents the text's meaning. Texts with similar meanings produce similar numbers. So "machine learning" and "neural network" will be found as related, even though they share no words.

> **Real-world analogy:** A regular library organises books alphabetically. A vector database is like a library where books are shelved by *topic similarity* — so "How to train a dog" ends up next to "Animal behaviour training", even though the words are completely different. You find things by meaning, not by spelling.

### What are Embeddings?
An embedding model (we use Gemini's `text-embedding-004`) converts any text into a list of 768 numbers. These numbers encode the *meaning*. Similar meaning → numbers are close together in space. This is what makes semantic search possible.

> **Real-world analogy:** Think of a GPS coordinate for meaning. The word "happy" might be at coordinates (0.2, 0.8, ...) and "joyful" at (0.21, 0.79, ...) — they're very close. "Sad" is far away. "Car" is in a completely different direction. Distance between coordinates = distance between meanings.

### What is FastAPI?
A Python web framework that turns Python functions into HTTP endpoints. It automatically validates your request data (using Pydantic), generates interactive docs at `/docs`, and is one of the fastest Python frameworks available.

> **Real-world analogy:** FastAPI is like a restaurant. The menu at `/docs` shows all available dishes (endpoints). You place an order (HTTP request with JSON body). The kitchen (your Python function) prepares it. The waiter returns your order (JSON response). Pydantic is the waiter who checks your order is valid before sending it to the kitchen.

### What is Multi-Agent?
A single AI agent can only do so many things well. **Multi-Agent** means you create several specialist agents — each focused on one job — and an **orchestrator** coordinates them. Agent 1 might search the internet. Agent 2 might search your private documents. Agent 3 might combine their outputs into a final answer. Each agent is just a focused LLM call with a specific prompt and specific tools.

> **Real-world analogy:** Instead of asking one person to research a topic, write a report, AND fact-check it — you hire a research team. The researcher finds facts, the archivist checks the internal records, and the editor combines everything into the final document. Better results because everyone stays in their lane.

> **Multi-Agent vs MCP:** In MCP, the LLM autonomously picks which tools to use. In Multi-Agent, *your code* decides which agents to run and in what order. You have more control and visibility.

### What is MCP (Model Context Protocol)?
MCP is an open standard created by Anthropic — think of it as a **USB-C port for AI tools**. Before MCP, every AI tool integration was custom-built differently. MCP standardises the way an LLM discovers and calls external tools. You build an MCP server that *exposes functions*, and any LLM that speaks MCP can call those functions. In this project the MCP server exposes your ChromaDB knowledge base as callable tools (`search_knowledge_base`, `add_document_to_kb`, `get_kb_stats`). The LLM then autonomously decides when to call them.

> **Real-world analogy:** Before USB-C, every device had a different charger. USB-C standardised the plug so any device works with any charger. MCP does the same for AI tools — your ChromaDB "plugin" works with any AI model that speaks MCP, not just Gemini. You write the server once; any LLM can use it.

### What is the difference between RAG and MCP?
- **RAG (`/rag-chat`)** — *You* control the flow: your code searches ChromaDB, injects context, then asks the LLM. Simple and predictable.
- **MCP (`/mcp-chat`)** — *The LLM* controls the flow: you give it the tool, and it decides when to call `search_knowledge_base` on its own. More autonomous and flexible.

### What is Pydantic?
A Python library that validates data shapes using type hints. In FastAPI, every request body and response is a Pydantic model. If you send the wrong data type, FastAPI rejects it with a clear error before it ever reaches your code. All models are in `app/models/schemas.py`.

> **Real-world analogy:** A form at a government office. The form defines exactly what fields are required, what type each field must be (text, number, date), and which are optional. If you submit it wrong, the clerk rejects it at the window before it goes to the back office. Pydantic is that form — it catches bad data early.

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
│   │   ├── parser.py             ← Converts each raw SDK step → readable AgentStep
│   │   └── multi_runner.py        ← Orchestrates 3 specialist agents (multi-agent)
│   │
│   ├── vectordb/                  ← Vector Database logic
│   │   ├── store.py               ← ChromaDB setup + Gemini embedding function
│   │   └── retriever.py          ← add_document(), search(), list_all_documents()
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

### Step 6 — Start the FastAPI server
```bash
.venv/bin/uvicorn main:app --reload --port 8000
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

### 🟣 STEP J — MCP Chat (LLM picks its own tools autonomously)

**Requires:** MCP server running (Step 6b above).

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

**Experiment:** Ask `"What is the weather today?"` — the LLM will use Google Search because that's not in your knowledge base. Ask `"What is ChromaDB?"` — the LLM will call `search_knowledge_base` because it finds it relevant. Ask `"Tell me about RAG and today's AI news"` — it will use both tools.

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
      "flow_summary": ["Searched ChromaDB — retrieved 3 doc(s): rag-001 (score=0.94), ..."]
    },
    {
      "agent_name": "synthesizer_agent",
      "role": "Synthesizer — combines both agents' findings into one final answer",
      "answer": "[Internet] RAG is widely used in production... [Knowledge Base] Your docs explain...",
      "flow_summary": ["Combined research_agent + knowledge_agent outputs"]
    }
  ],
  "final_answer": "[Internet] RAG (Retrieval Augmented Generation)... [Knowledge Base] According to your docs..."
}
```

**Experiment 1:** Ask `"What is an LLM?"` — knowledge_agent will find your seeded `llm-001` doc AND research_agent will search Google. Compare the two answers before reading the synthesized one.

**Experiment 2:** Ask something NOT in your knowledge base, like `"What is the latest iPhone?"`. Knowledge agent will say "No relevant documents found." Synthesizer will use only the internet source.

**Experiment 3:** Compare `/chat` vs `/multi-agent-chat` on the same question. The multi-agent answer will have [Internet] and [Knowledge Base] labels, making sources completely transparent.

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

---

## How the Code Flows

### Flow 1 — Agent flow (POST /chat), step by step in plain English

```
Step 1  YOU send:  POST /chat  { "message": "What is the latest in AI?" }

Step 2  FastAPI receives the request.
        chat.py validates the JSON (Pydantic checks the shape).

Step 3  runner.py calls the Gemini SDK:
        client.interactions.create(model, message, tools=[google_search])

Step 4  Gemini LLM thinks (THOUGHT step — internal, silent):
        "This question needs current info. I should search Google."

Step 5  Gemini calls Google Search (GOOGLE_SEARCH_CALL step):
        Sends 1–3 search queries to the internet.

Step 6  Google returns results (GOOGLE_SEARCH_RESULT step):
        Title, URL, and snippet for each result come back to the LLM.

Step 7  Gemini thinks again (THOUGHT step):
        "I have enough. I can now write a good answer."

Step 8  Gemini writes the answer (MODEL_OUTPUT step):
        Uses the search snippets as context.

Step 9  parser.py converts each raw SDK step → a clean AgentStep object.

Step 10 YOU receive: JSON with every step visible + final_answer.
```

**Code file path:**
```
chat.py → runner.py → [Gemini + Google] → parser.py → ChatResponse JSON
```

---

### Flow 2 — RAG flow (POST /documents/rag-chat), step by step in plain English

```
Step 1  YOU send:  POST /documents/rag-chat  { "question": "What is RAG?", "top_k": 3 }

Step 2  FastAPI receives the request.
        rag.py validates the JSON.

Step 3  retriever.py embeds your question:
        "What is RAG?" → Gemini text-embedding-004 → [0.12, -0.34, ..., 0.88]  (768 numbers)

Step 4  ChromaDB receives that vector and compares it to ALL stored document vectors.
        It calculates cosine similarity (how close are the meanings?).

Step 5  ChromaDB returns the top 3 most similar documents with similarity scores.
        Example: rag-001 (0.94), vec-001 (0.81), emb-001 (0.76)

Step 6  rag.py builds a context block:
        "[Document 1 | similarity: 0.94]\nRAG stands for...\n\n[Document 2]..."

Step 7  rag.py builds the LLM prompt:
        "Answer using ONLY the context below. Do not use outside knowledge.
         Context: [the 3 documents]   Question: What is RAG?"

Step 8  Gemini reads only those 3 documents and writes an answer.
        It cannot search the internet. It cannot use its training data.
        It is constrained to YOUR documents.

Step 9  YOU receive: JSON with retrieved_documents, context_used, and answer.
```

**Code file path:**
```
rag.py → retriever.py → ChromaDB → (back to rag.py) → Gemini generate_content() → RagResponse JSON
```

---

### When you add a document (POST /documents), step by step in plain English

```
Step 1  YOU send:  POST /documents  { "text": "FastAPI generates docs at /docs...",
                                      "metadata": {"topic": "FastAPI"} }

Step 2  retriever.py receives the text.

Step 3  GeminiEmbeddingFunction calls Gemini text-embedding-004:
        "FastAPI generates docs at /docs..." → [0.45, 0.12, ..., -0.23]  (768 numbers)

Step 4  ChromaDB saves three things together:
        • The original text (so you can read it back)
        • The 768-number vector (so it can be searched by meaning)
        • Your metadata (topic, source, etc.)
        All saved to the chroma_db/ folder on disk.

Step 5  YOU receive: { "doc_id": "abc123", "message": "Document added" }
        Next time someone asks "How do I test FastAPI?", this document will be retrieved.
```

**Code file path:**
```
rag.py → retriever.add_document() → store.GeminiEmbeddingFunction → ChromaDB (chroma_db/ on disk)
```

---

### Flow 3 — MCP flow (POST /mcp-chat), step by step in plain English

```
Step 1  YOU send:  POST /mcp-chat  { "message": "What is RAG? Also any AI news today?" }
        Two terminals must be running: FastAPI on :8000 AND MCP server on :8001.

Step 2  FastAPI receives the request.
        mcp_chat.py sets tools = [google_search, mcp_server(url=localhost:8001/mcp)]

Step 3  runner.py calls the Gemini SDK with BOTH tools available.

Step 4  Gemini LLM thinks (THOUGHT step):
        "RAG is probably in the knowledge base. AI news needs internet. I'll use both."

Step 5  Gemini sends an MCP call to your server (MCP_SERVER_TOOL_CALL step):
        → HTTP request to http://localhost:8001/mcp
        → Function: search_knowledge_base(query="RAG", top_k=3)

Step 6  Your MCP server (mcp_server/server.py) receives the call.
        It runs retriever.search("RAG") → ChromaDB → returns top 3 documents.
        Results are sent back to Gemini via MCP protocol (MCP_SERVER_TOOL_RESULT step).

Step 7  Gemini also calls Google Search (GOOGLE_SEARCH_CALL step):
        Searches for "AI agent news 2026".
        Gets results back (GOOGLE_SEARCH_RESULT step).

Step 8  Gemini thinks again (THOUGHT step):
        "I now have KB results + internet results. Time to write the answer."

Step 9  Gemini writes the final answer (MODEL_OUTPUT step):
        Uses BOTH the ChromaDB documents AND the search results.

Step 10 parser.py converts all steps (including the new MCP step types).

Step 11 YOU receive: JSON with every step visible. You can see exactly when
        the LLM chose ChromaDB vs Google Search.
```

**Code file path:**
```
mcp_chat.py → runner.py → [Gemini decides] → mcp_server/server.py → retriever.py → ChromaDB
                                            → Google Search
                          → parser.py → ChatResponse JSON
```

**How MCP server exposes tools (mcp_server/server.py):**
```
FastMCP server starts on port 8001
    exposes 3 tools the LLM can discover and call:
    • search_knowledge_base(query, top_k)  → runs retriever.search()
    • add_document_to_kb(text, topic)      → runs retriever.add_document()
    • get_kb_stats()                        → counts documents in ChromaDB

Gemini connects to http://localhost:8001/mcp
    asks: "what tools do you have?"
    gets back: the 3 function signatures above
    calls them whenever it decides to — completely autonomously
```

### Flow 4 — Multi-Agent flow (POST /multi-agent-chat), step by step in plain English

```
Step 1  YOU send:  POST /multi-agent-chat  { "message": "What is RAG?" }

Step 2  FastAPI receives the request.
        multi_agent.py validates the JSON.

Step 3  multi_runner.py ORCHESTRATES the agents:

        ┌───────────────────────────────────────────────────────────────────┐
        │  AGENT 1: Research Agent                                          │
        │  Prompt: "Find current information about: What is RAG?"           │
        │  Tool: Google Search                                              │
        │  Internally: LLM thinks → calls Google → reads results → answers │
        │  Output: answer_from_internet                                     │
        └───────────────────────────────────────────────────────────────────┘
                                     ↓
        ┌───────────────────────────────────────────────────────────────────┐
        │  AGENT 2: Knowledge Agent                                         │
        │  Embeds question → searches ChromaDB → retrieves matching docs     │
        │  Tool: ChromaDB semantic search (no internet)                     │
        │  Prompt: "Answer using ONLY these documents: [docs]"              │
        │  Output: answer_from_knowledge_base                               │
        └───────────────────────────────────────────────────────────────────┘
                                     ↓
        ┌───────────────────────────────────────────────────────────────────┐
        │  AGENT 3: Synthesizer Agent                                       │
        │  Input: answer_from_internet + answer_from_knowledge_base         │
        │  Prompt: "Combine these, label each fact [Internet]/[KB]"         │
        │  Output: combined_final_answer                                    │
        └───────────────────────────────────────────────────────────────────┘

Step 4  YOU receive: JSON with all 3 agents' answers + final synthesized answer.
        Each agent's answer tells you where its knowledge came from.
```

**Code file path:**
```
multi_agent.py → multi_runner.run_multi_agent()
    ├─ run_research_agent()  → runner.run_agent() → Gemini + Google Search → parser.py
    ├─ run_knowledge_agent() → retriever.search() → ChromaDB → Gemini generate_content()
    └─ run_synthesizer_agent() → Gemini generate_content() with combined prompt
    → MultiAgentResponse JSON
```

**Key difference from MCP:**
```
MCP flow:         YOU give LLM two tools → LLM autonomously decides when to call each
Multi-Agent flow: YOUR CODE decides to run 3 agents in order → you have full control
```

---

### All 4 flows side by side — key differences

| | Flow 1: Agent `/chat` | Flow 2: RAG `/rag-chat` | Flow 3: MCP `/mcp-chat` | Flow 4: Multi-Agent `/multi-agent-chat` |
|---|---|---|---|---|
| **Who decides to search?** | LLM decides | Your code always searches | LLM decides | Your code (orchestrator) |
| **Knowledge source** | Live internet | Your ChromaDB only | Both — LLM picks | Both — always uses both |
| **LLM gets context from** | Google Search results | Your retrieved docs | Both sources | Each agent gets its own context |
| **You control the flow?** | No | Yes | No | Yes |
| **Agents visible** | 1 (the LLM) | 0 (no agent steps) | 1 (the LLM) | 3 (each one's output visible) |
| **Best for** | Current events, facts | Private/company data | Mixed questions | Highest quality — transparent sourcing |
| **Needs MCP server?** | No | No | Yes (port 8001) | No |

---

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
| `POST` | `/documents/seed` | Load 7 sample documents into ChromaDB | No |
| `POST` | `/documents` | Add your own document to ChromaDB | No |
| `GET`  | `/documents` | List all stored documents | No |
| `DELETE` | `/documents/{id}` | Remove a document | No |
| `POST` | `/documents/rag-chat` | Ask question using your knowledge base (RAG) | No |
| `POST` | `/mcp-chat` | AI agent with Google Search **+** ChromaDB via MCP | **Yes** (port 8001) |
| `POST` | `/multi-agent-chat` | 3 specialist agents: research + knowledge + synthesizer | No |
