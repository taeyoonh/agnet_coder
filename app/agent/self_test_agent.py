from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .pipeline_utils import SELF_TEST_SYSTEM_PROMPT, build_conversation, extract_headline
from .simple_messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

CODE_BLOCK_RE = re.compile(r"```(?P<lang>[^\n]*)\n(?P<code>.*?)```", re.DOTALL)
MAX_ERROR_CHARS = 2000


@dataclass(slots=True)
class ParsedBlocks:
    solution: str
    tests: str


def _extract_blocks(markdown: str) -> Optional[ParsedBlocks]:
    matches = list(CODE_BLOCK_RE.finditer(markdown))

    # 1) Normal case: at least two code blocks found
    if len(matches) >= 2:
        solution = matches[0].group("code").strip()
        tests = matches[1].group("code").strip()
        return ParsedBlocks(solution=solution, tests=tests)

    # 2) Single code block: try to split around def run_tests
    if len(matches) == 1:
        code = matches[0].group("code")
        # Locate where run_tests is defined
        m = re.search(r"^def\s+run_tests\s*\(", code, re.MULTILINE)
        if m:
            solution = code[: m.start()].strip()
            tests = code[m.start() :].strip()
            if solution and tests:
                return ParsedBlocks(solution=solution, tests=tests)

    # Otherwise, parsing failed
    return None


def _run_self_tests(solution: str, tests: str) -> Tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="selftest-") as tmpdir:
        script = Path(tmpdir) / "submission_with_tests.py"
        script.write_text(
            "\n\n".join([solution, tests, "\nif __name__ == '__main__':\n    run_tests()\n"]),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (proc.stdout + proc.stderr).strip()
        success = proc.returncode == 0
        if not output:
            output = "PASS" if success else "self-tests failed without output"
        return success, output


def _truncate(text: str, limit: int = MAX_ERROR_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


class SelfTestAgent:
    """Generate solution + tests, run them, retry with feedback (max_attempts)."""

    def __init__(self, client, max_attempts: int = 3) -> None:
        self.client = client
        self.max_attempts = max_attempts

    def _failure_prompt(self, user_prompt: str, blocks: ParsedBlocks | None, error: str, attempt: int, last_reply: str = "") -> str:
        remaining = max(self.max_attempts - attempt, 0)

        if blocks is not None:
            sol = blocks.solution
            tests = blocks.tests
        else:

            sol = "(no solution block parsed)"
            tests = "(no test block parsed)"

        base = (
            f"Attempt {attempt} failed when running your self-tests.\n\n"
            f"[Task]\n{user_prompt.strip()}\n\n"
            f"[Solution Block]\n```python\n{sol}\n```\n\n"
            f"[Self-Test Block]\n```python\n{tests}\n```\n\n"
            f"[Test Run Output]\n{_truncate(error)}\n\n"
            "Revise BOTH the code and the tests so they are correct and non-flaky.\n"
            "- Output format: short explanation, then two Python code blocks (solution first, tests second with run_tests()).\n"
            "- End with <END-OF-CODE>.\n"
            f"- Remaining retries after this: {remaining}.\n"
        )

        if blocks is None and last_reply:
            base += (
                "\nFor reference, your previous full reply was:\n"
                "```markdown\n"
                f"{_truncate(last_reply)}\n"
                "```"
            )
        return base

    def run(
        self,
        message: str,
        history: List[Dict[str, str]] | None = None,
        task=None,
    ) -> Dict[str, str]:

        prompts: List[BaseMessage] = [SystemMessage(content=SELF_TEST_SYSTEM_PROMPT)]
        prompts.extend(build_conversation(history, message))

        final_reply = ""

        for attempt in range(1, self.max_attempts + 1):
            reply = self.client.chat(prompts).strip()
            final_reply = reply
            blocks = _extract_blocks(reply)

            if blocks:
                success, output = _run_self_tests(blocks.solution, blocks.tests)
            else:
                success, output = False, "Expected two Python code blocks (solution + self-tests) but could not parse them."

            if success:
                break

            prompts.append(AIMessage(content=reply))
            prompts.append(
                HumanMessage(
                    content=self._failure_prompt(
                        message,
                        blocks,
                        output,
                        attempt,
                        last_reply=reply,
                    )
                )
            )

        headline, _ = extract_headline(final_reply)
        return {"headline": headline, "body": final_reply}

    def stream(self, message: str, history: List[Dict[str, str]] | None = None, task=None):
        result = self.run(message, history=history, task=task)
        yield {"stage": "complete", "headline": result["headline"], "content": result["body"]}


__all__ = ["SelfTestAgent"]
