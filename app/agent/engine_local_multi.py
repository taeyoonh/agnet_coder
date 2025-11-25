"""Local llama.cpp-backed multi-stage agent."""

from __future__ import annotations

from typing import Dict, List

from .llama_client import LlamaServerClient
from .multi_agent import LangGraphAgent

_CLIENT = LlamaServerClient()
_AGENT = LangGraphAgent(_CLIENT)


def agent_reply(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, str]:
    return _AGENT.run(message, history)


def agent_stream(message: str, history: List[Dict[str, str]] | None = None):
    yield from _AGENT.stream(message, history)


__all__ = ["agent_reply", "agent_stream", "LangGraphAgent"]

