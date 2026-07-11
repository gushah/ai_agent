# AI Agent + RAG + MCP + Multi-Agent — Learning Project

A hands-on FastAPI app that makes **every internal step of an AI agent visible**.
Built for beginners who want to deeply understand how AI agents, LLMs, vector databases, RAG, MCP, and multi-agent systems actually work — not just use them as black boxes.

> **Flowchart diagrams** are in [docs/how-it-works.md](docs/how-it-works.md) — GitHub renders them automatically.
> Individual SVG diagrams for each flow are in [docs/diagrams/](docs/diagrams/).

---

## What Problem Does This Solve? (Real-World Value)

**The core problem:** An LLM like Gemini knows everything up to its training date, but knows *nothing* about your business — your products, internal policies, customer data, or private documents.

This app demonstrates the 4 patterns companies use to solve that:

| Pattern | Business problem solved | Real product using it |
|---|---|---|
| **Agent** `/chat` | Questions needing live internet data | Perplexity AI, Google AI Overview |
| **RAG** `/rag-chat` | Questions answered from YOUR private documents | Notion AI, Confluence AI, SharePoint Copilot |
| **MCP** `/mcp-chat` | Questions needing both internet AND your private data | GitHub Copilot (code + docs), Intercom Fin |
| **Multi-Agent** `/multi-agent-chat` | Complex research combining multiple specialist sources | Enterprise research tools, financial analysis bots |

**The single change needed to make this YOUR product:** Run `POST /documents` (or update `POST /documents/seed`) with your real documents instead of the sample Acme Corp policies. The architecture, code, and endpoints stay exactly the same.

---

## The Scenario — Acme Corp AI Assistant

To make every concept concrete, this app uses a single running example throughout:

> **You are the AI team at Acme Corp, an online retailer.**
> Your manager asks: *"Can we build a chatbot that instantly answers customer questions about our return policy, shipping costs, warranties, and membership — without them having to search the website?"*

The 7 documents loaded by `POST /documents/seed` are Acme Corp's real business policies:

| Document ID | What it contains |
|---|---|
| `acme-return-001` | 30-day return policy, electronics exception, how to start a return |
| `acme-shipping-002` | Shipping costs, delivery times, free shipping threshold ($50) |
| `acme-warranty-003` | 1-year warranty, what's covered, how to make a claim |
| `acme-refund-004` | Refund timelines, store credit, partial refunds |
| `acme-support-005` | Support hours, phone / email / chat contacts |
| `acme-membership-006` | Premium plan ($9.99/month), benefits, cancellation policy |
| `acme-orders-007` | Order tracking, cancellation window, what to do if delayed |

**Why not just use keyword search?** A customer might write "get my money back", "send it back", "wrong size", or "I changed my mind" — none contain "return policy", but all should find `acme-return-001`. Vector search finds them all. Keyword search misses them all.

---

## The Big Picture — All 4 Flows

```
YOUR QUESTION
     │
     ├─── Flow 1: AGENT  →  POST /chat
     │         Question → FastAPI → Gemini LLM thinks → calls Google Search
     │         → reads live results → writes final answer
     │         Knowledge source: the live internet
     │
     ├─── Flow 2: RAG    →  POST /documents/rag-chat
     │         Question → FastAPI → your code embeds it → searches ChromaDB
     │         → retrieves your documents → injects them → LLM reads ONLY those → answers
     │         Knowledge source: your private ChromaDB documents only
     │
     ├─── Flow 3: MCP    →  POST /mcp-chat
     │         Question → FastAPI → Gemini LLM thinks → autonomously calls
     │         Google Search AND/OR your ChromaDB (via MCP protocol) → answers
     │         Knowledge source: internet + your documents — LLM picks
     │
     └─── Flow 4: MULTI-AGENT  →  POST /multi-agent-chat
               Question → 3 specialist agents run in sequence:
               Agent 1 (internet) + Agent 2 (ChromaDB) + Agent 3 (synthesizer)
               Knowledge source: both, always, with [Internet]/[KB] labels
```

**One-sentence difference:** Flow 1 = LLM + internet. Flow 2 = your code + your docs. Flow 3 = LLM + both. Flow 4 = 3 LLMs + both + transparent sourcing.

---

## Documentation

| Doc | What's inside |
|---|---|
| [docs/concepts.md](docs/concepts.md) | Key concepts with real-world analogies (LLM, Agent, RAG, Vector DB, MCP, etc.) + project structure |
| [docs/setup.md](docs/setup.md) | Setup (5 min) + running the test suite |
| [docs/walkthrough.md](docs/walkthrough.md) | Steps A–K: run every endpoint, see what happens + understanding the responses |
| [docs/how-it-works.md](docs/how-it-works.md) | How the code flows — all 4 flows in plain English + Mermaid diagrams |
| [docs/reference.md](docs/reference.md) | Which flow to use + files to read in order + all endpoints at a glance |
| [docs/interview-ready-summary.md](docs/interview-ready-summary.md) | A short, simple interview-friendly summary of the repo and why it matters |
| [docs/learn-first.md](docs/learn-first.md) | A focused beginner-friendly guide to start with the `/chat` flow only |

**Suggested reading order:**
1. This README — understand why each pattern exists
2. [concepts.md](docs/concepts.md) — one paragraph per term, with analogies
3. [setup.md](docs/setup.md) — get it running
4. [walkthrough.md](docs/walkthrough.md) — run each endpoint yourself, see the output
5. [how-it-works.md](docs/how-it-works.md) — now that you've seen it work, the diagrams will make sense

---

## Trying It — Terminal Chat Client

Instead of using `/docs` (Swagger UI) or raw `curl`, you can chat with all 4 flows directly in a terminal.

**Terminal 1 — server:**
```bash
export GEMINI_API_KEY="your-key"
.venv/bin/python -m uvicorn main:app --reload --port 8000
```
Podman:
```bash
cd /Users/ankita/dev/ai_agent
export GEMINI_API_KEY="your-key"
podman build -t ai-agent-app .

# Run in the foreground (showing logs in the terminal)
podman run --rm -p 8000:8000 -e GEMINI_API_KEY="$GEMINI_API_KEY" ai-agent-app

# Run in the background (detached mode)
podman run -d --name ai-agent-app -p 8000:8000 -e GEMINI_API_KEY="$GEMINI_API_KEY" ai-agent-app

# Check running containers
podman ps

# View logs
podman logs -f ai-agent-app

# Stop the container
podman stop ai-agent-app

# Remove a stopped container
podman rm ai-agent-app

# Remove an image
podman rmi ai-agent-app

# Remove all stopped containers and unused images (careful)
podman system prune -a
```
**Terminal 2 — chat:**
```bash
.venv/bin/python chat_cli.py
```

You get a prompt where you can switch between all 4 flows:

```
────────────────────────────────────────────────────────────────────────────────
  AI Agent CLI  —  all 4 flows in one terminal
  Mode commands : /chat  /rag  /mcp  /multi
  Other commands: /steps  /seed  /new  /quit
────────────────────────────────────────────────────────────────────────────────

[chat] You: What is RAG?
Agent: RAG (Retrieval-Augmented Generation) is...
  (4 steps — type /steps to see the reasoning chain)

[chat] You: Give me a real-world example     ← follow-up works (session memory)
[chat] You: /seed                             ← load sample Acme Corp docs
[chat] You: /rag                              ← switch to RAG mode
[rag]  You: What is the return policy?
Agent: Customers may return any unused item within 30 days...
  (searched 3 doc(s) from KB — type /steps to see which)

[rag]  You: /steps                            ← see which docs were retrieved
[rag]  You: /mcp                              ← switch to MCP mode
[mcp]  You: What are the shipping costs?      ← LLM picks Google or ChromaDB
[mcp]  You: /multi                            ← switch to Multi-Agent
[multi] You: Summarise Acme's policies        ← 3 agents collaborate
[multi] You: /steps                           ← see each agent's individual answer
```

**What you see in Terminal 1** while chatting:
```
INFO     [chat] ▶  message='What is RAG?'  session=new  history=0 turns
INFO     [runner] Calling Gemini (gemini-2.5-flash) ...
INFO     [runner] Got 4 steps from Gemini
INFO     [runner]   [0] user   → User Question
INFO     [runner]   [1] agent  → Thought  (280 chars)
INFO     [runner]   [2] agent  → Google Search  queries=['what is RAG AI']
INFO     [runner]   [3] agent  → Final Answer  (512 chars)
INFO     [chat] ✓  4 steps  |  answer: RAG (Retrieval-Augmented Generation)...
```

Terminal 1 shows the agent's internal reasoning in real time — what it searched for, how many results it got, and how long its answer was.

---

## Key Features

| Feature | Detail |
|---|---|
| **Conversation memory** | `POST /chat` keeps the last 5 turns per session. Pass `session_id` from the response back to continue a conversation. |
| **Async routes** | All endpoints are `async def` with `asyncio.to_thread()` for blocking Gemini/ChromaDB calls — the event loop never blocks. |
| **Server-side logging** | Every request logs agent steps to Terminal 1 in real time. |
| **78 tests** | All flows tested without a real API key using mocks and in-memory ChromaDB. |
