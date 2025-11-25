"""Single-shot agent that handles plan/code/review in one completion."""

from __future__ import annotations

from typing import Dict, List

from .simple_messages import SystemMessage

from .pipeline_utils import (
    SINGLE_AGENT_SYSTEM_PROMPT,
    build_conversation,
    extract_headline,
)


SINGLE_AGENT_PROMPT = """
You are a Senior Engineer acting as a planner, coder, and reviewer all in one.
Summarize the user conversation and existing history to define the problem, create an execution plan,
present stable, complete code, and also write your own verification/improvement ideas.
Always implement in Python 3.

Output Format (English Markdown):
1. `### <One-line Summary>` - Introduce the solution
strategy in one sentence
2. `**Problem Analysis**` - 2-4 bullets for requirements/constraints
3. `**Execution Plan**` - At least 4 specific steps
4. `**Core Code**` - A single
code block (full Python implementation)
5. `**Test Guide**` - 2-4 bullets of representative
cases
6. `**Further Improvements**` - 2 or more ideas for quality/scalability/testing

Rules:
- Avoid repeating information already provided; focus on changes/core logic.
- The very last line of your response must be <END-OF-CODE>.
""".strip()


class SingleShotAgent:
    def __init__(self, client, system_prompt: str = SINGLE_AGENT_SYSTEM_PROMPT) -> None:
        self.client = client
        self.system_prompt = system_prompt

    def run(self, message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, str]:
        conversation = build_conversation(history, f"""{SINGLE_AGENT_PROMPT}\n\n{message}""")
        prompts = [SystemMessage(content=self.system_prompt), *conversation]
        final = self.client.chat(prompts).strip()
        headline, _ = extract_headline(final)
        return {"headline": headline, "body": final}

    def stream(self, message: str, history: List[Dict[str, str]] | None = None):
        response = self.run(message, history)
        yield {"stage": "complete", "headline": response["headline"], "content": response["body"]}


__all__ = ["SingleShotAgent"]
