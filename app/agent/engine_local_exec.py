from __future__ import annotations

import os
from typing import Any, Dict, List

from .exec_feedback_agent import ExecutionFeedbackAgent
from .llama_client import LlamaServerClient

_CLIENT = LlamaServerClient()
_AGENT = ExecutionFeedbackAgent(
    _CLIENT,
    max_attempts=int(os.getenv("EXEC_AGENT_MAX_ATTEMPTS", "3")),
)


def agent_reply(
    message: str,
    history: List[Dict[str, str]] | None = None,
    **kwargs: Any,
) -> Dict[str, str]:
    return _AGENT.run(message, history, task=kwargs.get("task"))


def agent_stream(
    message: str,
    history: List[Dict[str, str]] | None = None,
    **kwargs: Any,
):
    yield from _AGENT.stream(message, history, task=kwargs.get("task"))


__all__ = ["agent_reply", "agent_stream", "ExecutionFeedbackAgent"]
