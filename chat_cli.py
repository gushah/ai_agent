#!/usr/bin/env python3
# chat_cli.py
# ─────────────────────────────────────────────────────────────────────────────
# Terminal chat client for all 4 AI Agent flows.
#
# Start the server first:
#   .venv/bin/python -m uvicorn main:app --reload --port 8000
#
# Then run:
#   .venv/bin/python chat_cli.py
#
# Mode commands (switch flow):
#   /chat   — Agent + Google Search  (default, with conversation memory)
#   /rag    — RAG: answers from your ChromaDB knowledge base
#   /mcp    — MCP: LLM picks Google Search OR ChromaDB autonomously
#   /multi  — Multi-Agent: 3 specialist agents collaborate
#
# Other commands:
#   /steps  — show agent's internal reasoning from the last response
#   /seed   — load sample Acme Corp docs into ChromaDB (needed for /rag, /mcp)
#   /new    — start a fresh conversation (resets session memory, /chat only)
#   /quit   — exit
# ─────────────────────────────────────────────────────────────────────────────

import sys
import textwrap

import httpx

BASE = "http://localhost:8000"
WIDTH = 80

MODES = {
    "chat":  {"url": f"{BASE}/chat",               "label": "Agent + Google Search"},
    "rag":   {"url": f"{BASE}/documents/rag-chat",  "label": "RAG (knowledge base)"},
    "mcp":   {"url": f"{BASE}/mcp-chat",            "label": "MCP (LLM picks tools)"},
    "multi": {"url": f"{BASE}/multi-agent-chat",    "label": "Multi-Agent (3 agents)"},
}

HELP = (
    "  Mode commands : /chat  /rag  /mcp  /multi\n"
    "  Other commands: /steps  /seed  /new  /quit"
)


# ── helpers ───────────────────────────────────────────────────────────────────

def wrap(text: str, indent: str = "") -> str:
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
        else:
            lines.extend(
                textwrap.wrap(para, width=WIDTH - len(indent),
                              subsequent_indent=indent)
            )
    return "\n".join(indent + l if l else "" for l in lines)


def divider():
    print("─" * WIDTH)


def call(url: str, payload: dict) -> dict:
    r = httpx.post(url, json=payload, timeout=90)
    r.raise_for_status()
    return r.json()


# ── /steps display — different per mode ──────────────────────────────────────

def show_steps(mode: str, data: dict) -> None:
    print()
    divider()

    if mode == "rag":
        docs = data.get("retrieved_documents", [])
        print(f"  RAG: retrieved {len(docs)} document(s) from ChromaDB")
        divider()
        for doc in docs:
            score = doc.get("similarity_score", 0)
            did   = doc.get("doc_id", "?")
            text  = doc.get("text", "")[:100]
            print(f"  [{score:.2f}] {did}")
            print(wrap(text + "...", indent="        "))
            print()
        flow = data.get("rag_flow_summary", [])
        if flow:
            print("  Flow summary:")
            for line in flow:
                print(f"    {line}")

    elif mode == "multi":
        agents = data.get("agents", [])
        print(f"  Multi-Agent: {len(agents)} agents ran")
        divider()
        for agent in agents:
            print(f"  [{agent.get('name', '?')}]  {agent.get('role', '')}")
            answer = agent.get("final_answer") or agent.get("answer", "")
            if answer:
                print(wrap(answer[:300], indent="    "))
            print()

    else:  # chat / mcp
        steps = data.get("steps", [])
        print(f"  Agent reasoning chain ({len(steps)} steps):")
        divider()
        ICONS = {
            "user_input":             "  You   ",
            "thought":                " Think  ",
            "google_search_call":     "Search  ",
            "google_search_result":   "Result  ",
            "model_output":           "Answer  ",
            "function_call":          " Tool → ",
            "function_result":        " Tool ← ",
            "mcp_server_tool_call":   " MCP  → ",
            "mcp_server_tool_result": " MCP  ← ",
        }
        for step in steps:
            icon = ICONS.get(step["step_type"], step["step_type"][:8].center(8))
            print(f"  [{step['step_index']}] {icon}  {step['label']}")
            if step.get("detail"):
                print(wrap(step["detail"], indent="              "))

    divider()
    print()


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    mode       = "chat"
    session_id : str | None = None
    last_data  : dict = {}

    print()
    divider()
    print("  AI Agent CLI  —  all 4 flows in one terminal")
    print(HELP)
    divider()
    print(f"\n  Current mode: /chat — {MODES['chat']['label']}")
    print("  Tip: type /seed first to load sample docs (needed for /rag and /mcp)\n")

    while True:
        prompt = f"[{mode}] You: "
        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue

        low = user_input.lower()

        # ── built-in commands ─────────────────────────────────────────────────

        if low in ("/quit", "/exit", "quit", "exit"):
            print("Goodbye!")
            break

        if low in ("/chat", "/rag", "/mcp", "/multi"):
            mode = low.lstrip("/")
            last_data = {}
            label = MODES[mode]["label"]
            print(f"\n  Switched to [{mode}] — {label}")
            if mode == "chat":
                if session_id:
                    print(f"  Continuing session {session_id[:8]}... (type /new to reset)")
                else:
                    print("  New session — conversation memory is on.")
            elif mode in ("rag", "mcp"):
                print("  Tip: run /seed if you haven't loaded sample docs yet.")
            print()
            continue

        if low == "/new":
            session_id = None
            last_data  = {}
            print("\n  Conversation reset — started a new session.\n")
            continue

        if low == "/steps":
            if last_data:
                show_steps(mode, last_data)
            else:
                print("\n  (no response yet — ask a question first)\n")
            continue

        if low == "/seed":
            try:
                r = httpx.post(f"{BASE}/documents/seed", timeout=30)
                r.raise_for_status()
                d = r.json()
                print(f"\n  {d.get('message', 'Done.')}")
                print(f"  Total docs in KB: {d.get('total_in_db', '?')}\n")
            except httpx.ConnectError:
                print("\n  [Error] Server not running.\n")
            except Exception as exc:
                print(f"\n  [Error] {exc}\n")
            continue

        if low in ("/help", "/?"):
            print(f"\n{HELP}\n")
            continue

        # ── build payload for current mode ────────────────────────────────────

        url = MODES[mode]["url"]

        if mode == "rag":
            payload = {"question": user_input}
        else:
            payload = {"message": user_input}
            if mode == "chat":
                payload["session_id"] = session_id

        # ── call the API ──────────────────────────────────────────────────────

        try:
            data = call(url, payload)
        except httpx.ConnectError:
            print(
                "\n  [Error] Cannot connect — is the server running?\n"
                "    .venv/bin/python -m uvicorn main:app --reload --port 8000\n"
            )
            continue
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", exc.response.text)
            print(f"\n  [Error {exc.response.status_code}] {detail}\n")
            continue
        except Exception as exc:
            print(f"\n  [Error] {exc}\n")
            continue

        last_data = data

        # ── update session for chat mode ──────────────────────────────────────

        if mode == "chat":
            session_id = data.get("session_id")

        # ── display answer ────────────────────────────────────────────────────

        if mode == "rag":
            answer = data.get("answer", "(no answer)")
            n_docs = len(data.get("retrieved_documents", []))
            hint   = f"  (searched {n_docs} doc(s) from KB — type /steps to see which)"
        elif mode == "multi":
            answer = data.get("final_answer", "(no answer)")
            n_agents = len(data.get("agents", []))
            hint   = f"  (ran {n_agents} agents — type /steps to see each one's contribution)"
        else:
            answer = data.get("final_answer", "(no answer)")
            n_steps = data.get("total_steps", 0)
            hint   = f"  ({n_steps} steps — type /steps to see the reasoning chain)"

        print()
        print(wrap(f"Agent: {answer}"))
        print()
        print(hint)
        print()


if __name__ == "__main__":
    main()

# ── helpers ───────────────────────────────────────────────────────────────────

def wrap(text: str, indent: str = "") -> str:
    """Word-wrap text to WIDTH columns with an optional indent."""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
        else:
            lines.extend(
                textwrap.wrap(paragraph, width=WIDTH - len(indent),
                              subsequent_indent=indent)
            )
    return "\n".join(indent + l if l else "" for l in lines)


def print_divider():
    print("─" * WIDTH)


def print_steps(steps: list[dict]) -> None:
    """Print the agent's internal reasoning chain."""
    print()
    print_divider()
    print("  Agent reasoning chain:")
    print_divider()
    for step in steps:
        icon = {
            "user_input":           "  You  ",
            "thought":              " Think ",
            "google_search_call":   "Search ",
            "google_search_result": "Result ",
            "model_output":         "Answer ",
            "function_call":        "  Tool ",
            "function_result":      "  Tool←",
            "mcp_server_tool_call":   " MCP→  ",
            "mcp_server_tool_result": " MCP←  ",
        }.get(step["step_type"], step["step_type"][:7].center(7))

        print(f"  [{step['step_index']}] {icon}  {step['label']}")
        if step.get("detail"):
            print(wrap(step["detail"], indent="            "))
    print_divider()
    print()


# ── main loop ─────────────────────────────────────────────────────────────────

def main():
    session_id: str | None = None
    last_steps: list[dict] = []

    print()
    print_divider()
    print("  AI Agent Chat")
    print("  Commands: /steps  /new  /quit")
    print_divider()
    print()

    while True:
        # Prompt
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue

        # Built-in commands
        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "/steps":
            if last_steps:
                print_steps(last_steps)
            else:
                print("  (no steps yet — ask a question first)\n")
            continue

        if user_input.lower() == "/new":
            session_id = None
            last_steps = []
            print("  Started a new conversation.\n")
            continue

        # Call the API
        try:
            response = httpx.post(
                API_URL,
                json={"message": user_input, "session_id": session_id},
                timeout=60,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            print(
                "\n  [Error] Cannot connect to the server.\n"
                "  Start it with:\n"
                "    .venv/bin/python -m uvicorn main:app --reload --port 8000\n"
            )
            continue
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", exc.response.text)
            print(f"\n  [Error {exc.response.status_code}] {detail}\n")
            continue
        except Exception as exc:
            print(f"\n  [Error] {exc}\n")
            continue

        data = response.json()
        session_id = data.get("session_id")
        last_steps = data.get("steps", [])
        answer = data.get("final_answer", "(no answer)")

        print()
        print(wrap(f"Agent: {answer}"))
        print()
        print(f"  (type /steps to see how the agent reasoned through this)")
        print()


if __name__ == "__main__":
    main()
