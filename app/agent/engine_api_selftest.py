from __future__ import annotations

import os
from typing import Any, Dict, List

from .openai_client import OpenAIChatClient
from .self_test_agent import SelfTestAgent

_CLIENT = OpenAIChatClient()
_AGENT = SelfTestAgent(
    _CLIENT,
    max_attempts=int(os.getenv("SELFTEST_AGENT_MAX_ATTEMPTS", "3")),
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


__all__ = ["agent_reply", "agent_stream", "SelfTestAgent"]
