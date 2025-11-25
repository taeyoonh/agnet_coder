"""Hosted GPT API single-shot agent."""

from __future__ import annotations

from typing import Dict, List

from .openai_client import OpenAIChatClient
from .single_agent import SingleShotAgent

_CLIENT = OpenAIChatClient()
_AGENT = SingleShotAgent(_CLIENT)


def agent_reply(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, str]:
    return _AGENT.run(message, history)


def agent_stream(message: str, history: List[Dict[str, str]] | None = None):
    yield from _AGENT.stream(message, history)


__all__ = ["agent_reply", "agent_stream", "SingleShotAgent"]

