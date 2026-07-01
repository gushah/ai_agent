# app/agent/parser.py
# ─────────────────────────────────────────────────────────────────────────────
# Converts raw SDK step objects into clean AgentStep dicts.
#
# The google-genai SDK returns a typed union for each step. Every step has a
# `type` field (discriminator). We match on the Python class to extract
# the right fields for each step type.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Any

from google.genai._gaos.types.interactions.step import (
    FunctionCallStep,
    FunctionResultStep,
    GoogleSearchCallStep,
    GoogleSearchResultStep,
    MCPServerToolCallStep,
    MCPServerToolResultStep,
    ModelOutputStep,
    ThoughtStep,
    UserInputStep,
)
from google.genai._gaos.types.interactions.textcontent import TextContent

from app.models.schemas import AgentStep


# ── helpers ──────────────────────────────────────────────────────────────────

def _text_from_content_list(content_list: Any) -> str:
    """
    Extract plain text from a List[Content].
    Used for UserInputStep.content and ModelOutputStep.content.
    Each item in the list is a TextContent (or similar) with a .text field.
    """
    if not content_list:
        return ""
    parts = []
    for item in content_list:
        if isinstance(item, TextContent) and item.text:
            parts.append(item.text)
        elif hasattr(item, "text") and item.text:
            parts.append(item.text)
    return "".join(parts)


# ── per-type parsers ──────────────────────────────────────────────────────────

def _parse_user_input(index: int, step: UserInputStep) -> AgentStep:
    text = _text_from_content_list(step.content or [])
    return AgentStep(
        step_index=index,
        step_type="user_input",
        role="user",
        label="User Question",
        detail=f'Your message entered the agent: "{text}"',
        data={"text": text},
    )


def _parse_thought(index: int, step: ThoughtStep) -> AgentStep:
    thought_text = ""
    if step.summary:
        for item in step.summary:
            if hasattr(item, "text") and item.text:
                thought_text += item.text
    preview = thought_text[:300] + ("..." if len(thought_text) > 300 else "")
    return AgentStep(
        step_index=index,
        step_type="thought",
        role="agent",
        label="Agent Thinking (internal)",
        detail=(
            "The LLM is silently reasoning (chain-of-thought). "
            "This is never shown to end-users. "
            f"Thought preview: {preview or '(hidden by model)'}"
        ),
        data={"thought_preview": preview},
    )


def _parse_google_search_call(index: int, step: GoogleSearchCallStep) -> AgentStep:
    queries = (step.arguments.queries or []) if step.arguments else []
    return AgentStep(
        step_index=index,
        step_type="google_search_call",
        role="agent",
        label="Tool Call → Google Search",
        detail=(
            "The agent decided it needs live information and called Google Search. "
            f"Queries sent: {queries}"
        ),
        data={
            "tool": "google_search",
            "call_id": step.id,
            "queries": queries,
            "search_type": str(step.search_type or "web_search"),
        },
    )


def _parse_google_search_result(index: int, step: GoogleSearchResultStep) -> AgentStep:
    results = step.result or []
    # Show first 3 results as a preview
    preview = [
        {
            "title": str(getattr(r, "title", "") or "")[:80],
            "url": str(getattr(r, "url", "") or ""),
            "snippet": str(getattr(r, "snippet", "") or "")[:150],
        }
        for r in results[:3]
    ]
    return AgentStep(
        step_index=index,
        step_type="google_search_result",
        role="tool",
        label="Tool Result ← Google Search",
        detail=(
            f"Google Search returned {len(results)} result(s). "
            "The LLM reads these to compose its answer."
        ),
        data={
            "call_id": step.call_id,
            "total_results": len(results),
            "top_results_preview": preview,
        },
    )


def _parse_function_call(index: int, step: FunctionCallStep) -> AgentStep:
    name = getattr(step, "name", "unknown")
    args = getattr(step, "arguments", {})
    return AgentStep(
        step_index=index,
        step_type="function_call",
        role="agent",
        label=f"Tool Call → {name}",
        detail=f"Agent called custom function '{name}' with args: {args}",
        data={"tool": name, "arguments": str(args)[:300]},
    )


def _parse_function_result(index: int, step: FunctionResultStep) -> AgentStep:
    output = getattr(step, "output", None)
    return AgentStep(
        step_index=index,
        step_type="function_result",
        role="tool",
        label="Tool Result ← Function",
        detail="Custom tool returned a result back to the LLM.",
        data={"output": str(output)[:300]},
    )


def _parse_mcp_tool_call(index: int, step: MCPServerToolCallStep) -> AgentStep:
    name = getattr(step, "name", "unknown")          # tool function name
    args = getattr(step, "arguments", {}) or {}
    server = getattr(step, "server_name", "knowledge_base")
    return AgentStep(
        step_index=index,
        step_type="mcp_server_tool_call",
        role="agent",
        label=f"MCP Tool Call → {name}",
        detail=(
            f"The LLM decided to call '{name}' on the MCP server '{server}'. "
            f"MCP is a standard protocol — the LLM sends the call, "
            f"the MCP server runs the function against ChromaDB and returns results. "
            f"Args: {args}"
        ),
        data={"tool": name, "server": server, "arguments": str(args)[:500]},
    )


def _parse_mcp_tool_result(index: int, step: MCPServerToolResultStep) -> AgentStep:
    content = getattr(step, "content", None)
    output_text = ""
    if content:
        if isinstance(content, list):
            for item in content:
                if hasattr(item, "text") and item.text:
                    output_text += item.text
        else:
            output_text = str(content)
    preview = output_text[:400] + ("..." if len(output_text) > 400 else "")
    return AgentStep(
        step_index=index,
        step_type="mcp_server_tool_result",
        role="tool",
        label="MCP Tool Result ← Knowledge Base",
        detail=(
            "The MCP server executed the tool function (e.g. searched ChromaDB) "
            "and returned the result to the LLM. The LLM will now use this to compose its answer."
        ),
        data={"output_preview": preview},
    )


def _parse_model_output(index: int, step: ModelOutputStep) -> AgentStep:
    text = _text_from_content_list(step.content or [])
    preview = text[:300] + ("..." if len(text) > 300 else "")
    return AgentStep(
        step_index=index,
        step_type="model_output",
        role="agent",
        label="Final Answer from LLM",
        detail=(
            "The LLM synthesised all tool results and reasoning into a final answer. "
            f"Preview: {preview}"
        ),
        data={"full_text": text},
    )


def _parse_unknown(index: int, step: Any) -> AgentStep:
    step_type_name = getattr(step, "type", type(step).__name__)
    raw_data: dict[str, Any] = {}
    if hasattr(step, "__dict__"):
        raw_data = {
            k: str(v)[:200]
            for k, v in vars(step).items()
            if not k.startswith("_")
        }
    return AgentStep(
        step_index=index,
        step_type=str(step_type_name),
        role="agent",
        label=f"Step: {step_type_name}",
        detail=f"Unrecognised SDK step type '{step_type_name}' — inspect 'data'.",
        data=raw_data,
    )


# ── public entry point ────────────────────────────────────────────────────────

def parse_step(index: int, step: Any) -> AgentStep:
    """
    Convert one raw SDK step object into a clean AgentStep.
    Dispatches to the correct per-type parser based on the Python class.
    """
    if isinstance(step, UserInputStep):
        return _parse_user_input(index, step)
    if isinstance(step, ThoughtStep):
        return _parse_thought(index, step)
    if isinstance(step, GoogleSearchCallStep):
        return _parse_google_search_call(index, step)
    if isinstance(step, GoogleSearchResultStep):
        return _parse_google_search_result(index, step)
    if isinstance(step, FunctionCallStep):
        return _parse_function_call(index, step)
    if isinstance(step, FunctionResultStep):
        return _parse_function_result(index, step)
    if isinstance(step, MCPServerToolCallStep):
        return _parse_mcp_tool_call(index, step)
    if isinstance(step, MCPServerToolResultStep):
        return _parse_mcp_tool_result(index, step)
    if isinstance(step, ModelOutputStep):
        return _parse_model_output(index, step)
    return _parse_unknown(index, step)


def extract_final_answer(steps: list[Any]) -> str:
    """
    Walk steps in reverse and return text from the last ModelOutputStep.
    That is always the LLM's final answer to the user.
    """
    for step in reversed(steps):
        if isinstance(step, ModelOutputStep):
            text = _text_from_content_list(step.content or [])
            if text:
                return text
    return "No model_output step found in the interaction."
