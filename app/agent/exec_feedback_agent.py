from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pipeline_utils import (
    EXECUTION_REPAIR_SYSTEM_PROMPT,
    build_conversation,
    extract_headline,
)
from .simple_messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

CODE_BLOCK_RE = re.compile(r"```(?P<lang>[^\n]*)\n(?P<code>.*?)```", re.DOTALL)
MAX_ERROR_CHARS = 2000


@dataclass(slots=True)
class AttemptResult:
    attempt: int
    raw_reply: str
    code: Optional[str]
    success: bool
    checker_output: str


def _extract_code_block(markdown: str, preferred_language: Optional[str]) -> Optional[str]:
    matches = list(CODE_BLOCK_RE.finditer(markdown))
    if not matches:
        return None

    preferred_language = (preferred_language or "").strip().lower()
    if preferred_language:
        for match in reversed(matches):
            lang = match.group("lang").strip().lower()
            code = match.group("code").strip()
            if lang == preferred_language:
                return code

    return matches[-1].group("code").strip()


def _truncate(text: str, limit: int = MAX_ERROR_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


class ExecutionFeedbackAgent:
    """Generate code, run the checker, and retry with execution feedback."""

    def __init__(
        self,
        client,
        system_prompt: str = EXECUTION_REPAIR_SYSTEM_PROMPT,
        max_attempts: int = 3,
    ) -> None:
        self.client = client
        self.system_prompt = system_prompt
        self.max_attempts = max_attempts

    def _run_checker(self, checker: Path, code: str) -> Tuple[bool, str]:
        with tempfile.TemporaryDirectory(prefix="exec-feedback-") as tmpdir:
            submission = Path(tmpdir) / "submission.py"
            submission.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(checker), str(submission)],
                capture_output=True,
                text=True,
                check=False,
            )
            output = (proc.stdout + proc.stderr).strip()
            success = proc.returncode == 0
            if not output:
                output = "PASS" if success else "checker failed without output"
            return success, output

    def _failure_prompt(
        self,
        original_prompt: str,
        previous_code: Optional[str],
        error_output: str,
        attempt: int,
    ) -> str:
        remaining = max(self.max_attempts - attempt, 0)
        code_section = previous_code or "(previous attempt did not include a code block)"
        return (
            f"Attempt {attempt} failed against the automated checker.\n\n"
            f"[Task]\n{original_prompt.strip()}\n\n"
            f"[Previous Code]\n```python\n{code_section}\n```\n\n"
            f"[Checker Output]\n{_truncate(error_output)}\n\n"
            "Rewrite the FULL Python solution from scratch with the above failure in mind.\n"
            "- Keep one concise explanation followed by a single Python code block.\n"
            "- Ensure the final line of your message is <END-OF-CODE>.\n"
            f"- You have {remaining} retries after this."
        )

    def run(
        self,
        message: str,
        history: List[Dict[str, str]] | None = None,
        task: Any | None = None,
    ) -> Dict[str, str]:
        preferred_language = getattr(task, "language", None)
        checker_path = getattr(task, "checker", None)
        checker = Path(checker_path) if checker_path else None

        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]
        messages.extend(build_conversation(history, message))

        attempts: List[AttemptResult] = []
        final_reply = ""

        for attempt in range(1, self.max_attempts + 1):
            reply = self.client.chat(messages).strip()
            final_reply = reply
            code = _extract_code_block(reply, preferred_language)

            if checker and checker.exists() and code:
                success, checker_output = self._run_checker(checker, code)
            elif not checker:
                success, checker_output = True, "no checker provided"
            elif not code:
                success, checker_output = False, "no code block found to execute"
            else:
                success, checker_output = False, "checker file missing on disk"

            attempts.append(
                AttemptResult(
                    attempt=attempt,
                    raw_reply=reply,
                    code=code,
                    success=success,
                    checker_output=checker_output,
                )
            )

            if success:
                break

            messages.append(AIMessage(content=reply))
            messages.append(
                HumanMessage(
                    content=self._failure_prompt(
                        message,
                        code,
                        checker_output,
                        attempt,
                    )
                )
            )

        headline, _ = extract_headline(final_reply)
        return {"headline": headline, "body": final_reply}

    def stream(
        self,
        message: str,
        history: List[Dict[str, str]] | None = None,
        task: Any | None = None,
    ):
        result = self.run(message, history=history, task=task)
        yield {"stage": "complete", "headline": result["headline"], "content": result["body"]}


__all__ = ["ExecutionFeedbackAgent"]
