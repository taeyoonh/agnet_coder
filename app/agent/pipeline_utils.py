from __future__ import annotations

import os
from typing import Dict, List, Tuple

from .simple_messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

# --- System prompts: 3-stage coder pipeline ---------------------------------

CODER1_SYSTEM_PROMPT = """
You are a pragmatic senior Python engineer. Read the user's request and draft a clear solution with just enough context.
- Keep explanations short (what / why) before the code block.
- Provide exactly one Python code block containing the full solution.
- Close the response with `<END-OF-CODE>`.
""".strip()


CODER2_SYSTEM_PROMPT = """
You are a meticulous reviewer. Assume coder1's attempt may be wrong.
- Briefly state any issues or invariants you're checking.
- If problems exist, rewrite the full Python solution; otherwise keep a minimal confirmation.
- Provide exactly one improved Python code block and end with `<END-OF-CODE>`.
""".strip()


CODER3_SYSTEM_PROMPT = """
You are the final reviewer. Give a concise summary of the final plan, list the critical invariants you checked, and present the cleanest Python solution.
- Keep the structure simple: short summary, brief bullet list, single code block, tiny test guide.
- Always ensure the code block is complete and end the message with `<END-OF-CODE>`.
""".strip()

EXECUTION_REPAIR_SYSTEM_PROMPT = """
You are a Python engineer who iterates with real execution feedback.
- Always respond with one concise explanation paragraph followed by a single Python code block.
- Rewrite the full solution each round; do not rely on previous code being present.
- The final line of your message must be `<END-OF-CODE>`.
- Expect to receive failing test logs or tracebacks; use them to fix bugs aggressively.
""".strip()

SELF_TEST_SYSTEM_PROMPT = """
You are a Python engineer who must write both the solution and your own executable tests.
- Output exactly two Python code blocks:
  1) Full solution implementation (define the required function).
  2) Self-tests with a `def run_tests(): ...` that calls asserts; include `if __name__ == "__main__": run_tests()`.
- Keep explanations short (one paragraph) before the code blocks.
- End your entire message with `<END-OF-CODE>`.
- Tests must be specific and minimally sufficient; avoid flaky or randomized cases.
""".strip()


SINGLE_AGENT_SYSTEM_PROMPT = """
You are a helpful Python coding assistant. Read the latest user message (plus any brief history), describe your plan at a high level, then output one complete Python solution and end with `<END-OF-CODE>`.
""".strip()


MAX_RECENT_TURNS = int(os.getenv("AGENT_RECENT_TURNS", "6"))
SUMMARY_CHAR_LIMIT = int(os.getenv("AGENT_HISTORY_SUMMARY_CHARS", "1200"))
PROMPT_DEBUG = os.getenv("AGENT_PROMPT_DEBUG", "1").lower() not in ("0", "false", "no")


def coerce_content(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks = []
        for block in value:
            if isinstance(block, dict) and block.get("type") == "text":
                chunks.append(block.get("text", ""))
        return "\n".join(chunks)
    return str(value)


def serialize_message(message: BaseMessage) -> Dict[str, str]:
    if isinstance(message, SystemMessage):
        role = "system"
    elif isinstance(message, HumanMessage):
        role = "user"
    else:
        role = "assistant"
    return {"role": role, "content": coerce_content(message.content)}


def summarize_history(history: List[Dict[str, str]], limit: int = SUMMARY_CHAR_LIMIT) -> str:
    """Collapse older dialogue turns into terse bullet points."""

    if not history:
        return ""

    lines: List[str] = []
    consumed = 0
    for entry in history:
        role = entry.get("role", "user")
        speaker = "Agent" if role == "assistant" else "User"
        content = (entry.get("content") or "").strip()
        if not content:
            continue
        collapsed = " ".join(content.split())
        line = f"{speaker}: {collapsed}"

        if limit and consumed + len(line) > limit:
            available = max(limit - consumed, 0)
            if available < 10:
                break
            line = line[:available].rstrip()

        lines.append(f"- {line}")
        consumed += len(line)

        if limit and consumed >= limit:
            break

    if not lines:
        return ""

    return "Previous conversation summary:\n" + "\n".join(lines)


def debug_log_messages(messages: List[BaseMessage], header: str = "") -> None:
    """Print prompts to stdout when AGENT_PROMPT_DEBUG is enabled."""
    if not PROMPT_DEBUG:
        return
    title = f"[prompt] {header}".strip() or "[prompt]"
    print(title)
    for idx, message in enumerate(messages, start=1):
        role = (
            "system"
            if isinstance(message, SystemMessage)
            else "user"
            if isinstance(message, HumanMessage)
            else "assistant"
        )
        content = coerce_content(message.content).strip()
        print(f"  {idx:02d}. ({role}) {content}")
    print("-" * 40, flush=True)


def build_conversation(history: List[Dict[str, str]] | None, message: str) -> List[BaseMessage]:
    history = history or []
    recent_turns = history[-MAX_RECENT_TURNS:] if MAX_RECENT_TURNS > 0 else history
    older_turns = history[:-MAX_RECENT_TURNS] if MAX_RECENT_TURNS > 0 else []

    conversation: List[BaseMessage] = []
    summary = summarize_history(older_turns)
    if summary:
        conversation.append(SystemMessage(content=summary))

    for entry in recent_turns:
        content = entry.get("content", "").strip()
        if not content:
            continue
        role = entry.get("role", "user")
        if role == "assistant":
            conversation.append(AIMessage(content=content))
        else:
            conversation.append(HumanMessage(content=content))

    conversation.append(HumanMessage(content=message.strip()))
    return conversation


def dialogue_transcript(messages: List[BaseMessage]) -> str:
    parts: List[str] = []
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Agent"
        parts.append(f"{role}: {coerce_content(msg.content).strip()}")
    return "\n".join(parts)


def extract_headline(markdown: str) -> Tuple[str, str]:
    lines = markdown.splitlines()
    for line in lines:
        if line.startswith("### "):
            headline = line.removeprefix("### ").strip()
            return headline or "AI Code Plan", markdown
    return "AI Code Plan", markdown


def render_response(headline: str, draft1: str, draft2: str, final: str) -> str:
    sections = [
        f"### {headline or 'AI Code Plan'}",
    ]
    if draft1:
        sections.append("**Coder1 Output**\n" + draft1.strip())
    if draft2:
        sections.append("**Coder2 Output**\n" + draft2.strip())
    if final:
        sections.append("**Coder3 Summary**\n" + final.strip())
    return "\n\n".join(sections).strip()


__all__ = [
    "CODER1_SYSTEM_PROMPT",
    "CODER2_SYSTEM_PROMPT",
    "CODER3_SYSTEM_PROMPT",
    "EXECUTION_REPAIR_SYSTEM_PROMPT",
    "SELF_TEST_SYSTEM_PROMPT",
    "SINGLE_AGENT_SYSTEM_PROMPT",
    "MAX_RECENT_TURNS",
    "SUMMARY_CHAR_LIMIT",
    "coerce_content",
    "serialize_message",
    "summarize_history",
    "build_conversation",
    "dialogue_transcript",
    "extract_headline",
    "render_response",
]
