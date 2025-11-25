"""Minimal message classes to avoid pulling in langchain_core at runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BaseMessage:
    content: Any


@dataclass(slots=True)
class HumanMessage(BaseMessage):
    pass


@dataclass(slots=True)
class AIMessage(BaseMessage):
    pass


@dataclass(slots=True)
class SystemMessage(BaseMessage):
    pass


__all__ = ["BaseMessage", "HumanMessage", "AIMessage", "SystemMessage"]
