"""Reusable LangGraph-powered multi-stage agent."""

from __future__ import annotations

from typing import Dict, List, TypedDict

from .simple_messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from .pipeline_utils import (
    CODER1_SYSTEM_PROMPT,
    CODER2_SYSTEM_PROMPT,
    CODER3_SYSTEM_PROMPT,
    build_conversation,
    dialogue_transcript,
    extract_headline,
    render_response,
)


class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    draft1: str
    draft2: str
    final: str


class LangGraphAgent:
    """Three-stage coder pipeline (coder1 → coder2 → coder3)."""

    def __init__(
        self,
        client,
        coder1_prompt: str = CODER1_SYSTEM_PROMPT,
        coder2_prompt: str = CODER2_SYSTEM_PROMPT,
        coder3_prompt: str = CODER3_SYSTEM_PROMPT,
    ) -> None:
        self.client = client
        self.coder1_prompt = coder1_prompt
        self.coder2_prompt = coder2_prompt
        self.coder3_prompt = coder3_prompt
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("coder1", self._coder1)
        workflow.add_node("coder2", self._coder2)
        workflow.add_node("coder3", self._coder3)
        workflow.set_entry_point("coder1")
        workflow.add_edge("coder1", "coder2")
        workflow.add_edge("coder2", "coder3")
        workflow.add_edge("coder3", END)
        return workflow.compile()

    def _coder1(self, state: AgentState):
        dialogue = dialogue_transcript(state["messages"])
        prompts = [
            SystemMessage(content=self.coder1_prompt),
            HumanMessage(content=f"""
You are a Senior Algorithm/Software
Engineer. Based on the user's problem description,
(if any) existing code, and test
cases, write the first solution code.
All implementations must be in Python 3.

Role:
- Accurately understand the problem requirements and constraints, and select
  an efficient algorithm considering time/space complexity.
- Independently check boundary cases (min/max
input, all elements are the same, unusual patterns, etc.) and
  reflect them in the logic.

Output Format (English Markdown):
1. A brief description paragraph (summarizing the
approach)
2. A single code block (must be Python, full working code)
3. 2-4 bullets for test strategy (which cases to verify with)

Rules:
- Do not repeat code blocks with the same content.
- Avoid unnecessarily lengthy explanations; focus on the core logic and test ideas.
- The very last line of your response must be <END-OF-CODE>.
                    사용자 요구사항 및 대화:\n{dialogue}\n\n첫 번째 해결책을 제시하세요."""),
        ]
        draft1 = self.client.chat(prompts)
        return {"draft1": draft1}

    def _coder2(self, state: AgentState):
        dialogue = dialogue_transcript(state["messages"])
        draft1 = state.get("draft1", "")
        prompts = [
            SystemMessage(content=self.coder2_prompt),
            HumanMessage(
                content=(
                    f"""
You are a Senior Code Reviewer and Bug Hunter.
All implementations must be in Python 3.

Critical Premise:
- Assume the code written by coder1 is "mostly
wrong, or has at least one error."
- Your goal is not to trust the code, but to
  "prove it wrong" with counterexamples and logical verification.

Role:
- Reread the problem requirements and find where coder1's code violates them.
- Using the provided examples + additional test cases you create, mentally simulate the code
  and actively try to find cases where the actual output differs from the expected output.
- If even one problem is suspected, you may discard coder1's code and
  rewrite the entire code "from a new perspective."

Verification Procedure:
1. Write 2-3 of the problem's core constraints
as one-line bullets.
   (e.g., an
invariant like "String length must always be maintained after the operation")
2. Try to find where coder1's code violates these constraints.
3. If a counterexample is suspected, simulate how
coder1's code
   behaves for that input, index by index, for 2-3 steps.
4. If an error is confirmed or strongly suspected,
   rewrite the "second version of the code" from scratch to fix it.

Output Format (English Markdown):
1. "Verification Summary" paragraph (whether a counterexample was found, which constraint is violated)
2. A single code block (the corrected,
full Python code. Must be different from coder1's code)
3. A bullet list of "Additional Test
Cases" 2-4 items (Input / Expected Output explanation)

Rules:
- Do not resubmit code that is identical to coder1's.
- It is acceptable to completely overhaul the code structure.
- The very last line of your response must be <END-OF-CODE>.
                    """
                    "사용자 요구사항과 대화:\n"
                    f"{dialogue}\n\n"
                    "coder1 응답:\n"
                    f"{draft1}\n\n"
                    "위 코드를 검증하고 필요한 경우 더 나은 전체 코드를 다시 작성하세요."
                )
            ),
        ]
        draft2 = self.client.chat(prompts)
        return {"draft2": draft2}

    def _coder3(self, state: AgentState):
        dialogue = dialogue_transcript(state["messages"])
        draft1 = state.get("draft1", "")
        draft2 = state.get("draft2", "")
        prompts = [
            SystemMessage(content=self.coder3_prompt),
            HumanMessage(
                content=(
                    f"""
You are a Senior Engineer in charge of final verification and refactoring.
All implementations must be in Python 3.

Critical Premise:
- Assume the code written by coder2 also "still
has a high probability of containing bugs."
- Your goal is not to trust coder2's code. Instead, you must re-verify it logically
  from the perspective of the problem definition and invariants, and if necessary,
  aggressively modify it or
  rewrite it entirely.

Role:
1. Reread the problem requirements and constraints, and independently define 2-4 key
invariants.
   - Examples: "String length must always remain constant, even after multiple operations",
   
"Indices must
always be accessed within valid bounds",
   
"Time
complexity must be acceptable for n <= 1e5", etc.
2. Logically check if coder2's code "always" satisfies these invariants.
   - Pay close attention to: changes in array/string length, index movements, loop
termination conditions,
     and time/space complexity (Big O).
3. If any part is suspicious, create small
examples/edge cases
   and mentally simulate how the code will behave.
4. If bugs or design flaws are found,
refer to coder2's code but rewrite the "final version"
   from a perspective of safety and clarity.
   - Do not just make trivial changes like variable renaming.
     If the logic/structure is flawed, focus on
fixing the structure.

Output Format (English Markdown):
1. `### <One-line Summary>`: Summarize the final
solution in one sentence
   (e.g., "A greedy + prefix sum solution in O(n)")
2. `**Core Verification Points**` section:
   - 2-4 bullets describing which invariants and edge
cases you focused on verifying.
3. A single code block:
   - The final, complete code (must be Python).
   - Do not copy coder2's code verbatim without explanation.
     If you judge that the exact same structure is the best, state why in the core verification points.
4. "Test Guide" section:
   - 2-4 bullets with representative
test cases (input/expected output) to run.
   - Include min/max inputs, and extreme patterns (all 0s, all 1s, alternating patterns, etc.).

Rules:
- The final code must aim for "Readability
+ Safety + Requirements Met" simultaneously.
- If any part is ambiguous, modify it to be "more conservative and clear" than coder2's code.
- You must use exactly one code block.
- The entire response must be within 150 lines.
- The very last line of your response must be <END-OF-CODE>."""
                    "사용자와의 대화 기록:\n"
                    f"{dialogue}\n\n"
                    "coder1 응답:\n"
                    f"{draft1}\n\n"
                    "coder2 응답:\n"
                    f"{draft2}\n\n"
                    "위 정보를 바탕으로 최종 검증/리팩터링 결과를 작성하세요."
                )
            ),
        ]
        final = self.client.chat(prompts)
        return {"final": final}

    def _initial_state(
        self, message: str, history: List[Dict[str, str]] | None = None
    ) -> AgentState:
        conversation = build_conversation(history, message)
        return {
            "messages": conversation,
            "draft1": "",
            "draft2": "",
            "final": "",
        }

    def run(self, message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, str]:
        initial_state = self._initial_state(message, history)
        result = self.graph.invoke(initial_state)

        draft1 = (result.get("draft1") or "").strip()
        draft2 = (result.get("draft2") or "").strip()
        final = (result.get("final") or "").strip()

        content = final or draft2 or draft1
        headline, _ = extract_headline(content)

        return {"headline": headline, "body": content}

    def stream(self, message: str, history: List[Dict[str, str]] | None = None):
        initial_state = self._initial_state(message, history)
        draft1 = ""
        draft2 = ""
        final = ""
        last_payload: Dict[str, str] = {}
        for update in self.graph.stream(initial_state, stream_mode="updates"):
            for node, payload in update.items():
                if node == "coder1":
                    draft1 = (payload.get("draft1") or "").strip()
                    if draft1 and draft1 != last_payload.get("coder1"):
                        last_payload["coder1"] = draft1
                        yield {"stage": "coder1", "content": draft1}
                elif node == "coder2":
                    draft2 = (payload.get("draft2") or "").strip()
                    if draft2 and draft2 != last_payload.get("coder2"):
                        last_payload["coder2"] = draft2
                        yield {"stage": "coder2", "content": draft2}
                elif node == "coder3":
                    final = (payload.get("final") or "").strip()
                    if final and final != last_payload.get("coder3"):
                        last_payload["coder3"] = final
                        yield {"stage": "coder3", "content": final}
        headline, _ = extract_headline(final or draft2 or draft1)
        body = render_response(headline, draft1, draft2, final)
        yield {"stage": "complete", "headline": headline, "content": body}


__all__ = ["LangGraphAgent", "AgentState"]
