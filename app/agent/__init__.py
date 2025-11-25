from __future__ import annotations

import importlib
import os
from types import ModuleType
from typing import Dict

ENGINE_ALIAS_MAP = {
    "local_multi": ".engine_local_multi",
    "local_single": ".engine_local_single",
    "api_multi": ".engine_api_multi",
    "api_single": ".engine_api_single",
    "local_exec": ".engine_local_exec",
    "local-exec": ".engine_local_exec",
    "api_exec": ".engine_api_exec",
    "api-exec": ".engine_api_exec",
    "local_selftest": ".engine_local_selftest",
    "local-selftest": ".engine_local_selftest",
    "api_selftest": ".engine_api_selftest",
    "api-selftest": ".engine_api_selftest",
}

_ENGINE_CACHE: Dict[str, ModuleType] = {}


def _engine_key(name: str | None = None) -> str:
    if name:
        key = name.lower()
    else:
        key = os.getenv("AGENT_ENGINE", "local_multi").lower()
    if key not in ENGINE_ALIAS_MAP:
        return "local_multi"
    return key


def normalize_engine_name(name: str | None = None) -> str:
    return _engine_key(name)


def _get_engine(name: str | None = None) -> ModuleType:
    key = _engine_key(name)
    if key not in _ENGINE_CACHE:
        module_path = ENGINE_ALIAS_MAP[key]
        _ENGINE_CACHE[key] = importlib.import_module(module_path, __name__)
    return _ENGINE_CACHE[key]


def agent_reply(message: str, history, engine: str | None = None):
    impl = _get_engine(engine)
    return impl.agent_reply(message, history)


def agent_stream(message: str, history, engine: str | None = None):
    impl = _get_engine(engine)
    yield from impl.agent_stream(message, history)


__all__ = ["agent_reply", "agent_stream", "ENGINE_ALIAS_MAP", "normalize_engine_name"]
