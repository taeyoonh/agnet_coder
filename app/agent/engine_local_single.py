"""Local llama.cpp-backed single-shot agent."""

from __future__ import annotations

from typing import Dict, List

from .llama_client import LlamaServerClient
from .single_agent import SingleShotAgent

_CLIENT = LlamaServerClient()
_AGENT = SingleShotAgent(_CLIENT)


def agent_reply(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, str]:
    return _AGENT.run(message, history)


def agent_stream(message: str, history: List[Dict[str, str]] | None = None):
    yield from _AGENT.stream(message, history)


__all__ = ["agent_reply", "agent_stream", "SingleShotAgent"]

