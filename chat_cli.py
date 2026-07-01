#!/usr/bin/env python3
# chat_cli.py
# ─────────────────────────────────────────────────────────────────────────────
# Terminal chat interface for the AI Agent API.
#
# Usage:
#   1. Start the server in one terminal:
#        .venv/bin/python -m uvicorn main:app --reload --port 8000
#
#   2. Run this script in another terminal:
#        .venv/bin/python chat_cli.py
#
# Commands inside the chat:
#   /steps    — show every internal reasoning step from the last response
#   /new      — start a fresh conversation (clears session)
#   /quit     — exit
# ─────────────────────────────────────────────────────────────────────────────

import sys
import textwrap

import httpx

API_URL = "http://localhost:8000/chat"
WIDTH = 80  # wrap long lines for readability

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
