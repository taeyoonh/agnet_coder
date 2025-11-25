from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

BASE_CONFIG = {
    "logging": {"level": "INFO", "sinks": ["stdout"]},
    "services": {
        "billing": {
            "timeout": 30,
            "domains": ["core"],
            "retries": {"max": 3, "backoff": "exponential"},
        },
        "search": {
            "timeout": 80,
            "domains": ["read-only"],
            "cache": {"ttl": 60},
        },
    },
    "routers": [
        {"name": "edge", "hosts": ["app.example.com"], "headers": {"x-trace": "1"}},
        {"name": "admin", "hosts": ["admin.example.com"], "headers": {}},
    ],
    "feature_flags": {"checkout": {"enabled": False, "percent": 0}},
}

OPERATIONS = [
    {"op": "set", "path": "logging.level", "value": "DEBUG"},
    {"op": "merge", "path": "services.billing.retries", "value": {"max": 5, "jitter": True}},
    {"op": "set", "path": "feature_flags.checkout.percent", "value": 25},
    {"op": "set", "path": "feature_flags.checkout.enabled", "value": True},
    {"op": "merge", "path": "services.search.cache", "value": {"ttl": 120, "strategy": "request-window"}},
    {"op": "set", "path": "routers[0].headers.Cache-Control", "value": "no-store"},
    {"op": "remove", "path": "routers[1]"},
    {"op": "set", "path": "services.new_service", "value": {"timeout": 45, "regions": ["us-east", "ap-south"]}},
    {"op": "set", "path": "services.billing.domains", "value": ["core", "payments"]},
    {"op": "set", "path": "logging.sinks[1]", "value": "file"},
    {"op": "set", "path": "logging.files.main.path", "value": "/var/log/app.log"},
]

EXPECTED_CONFIG = {
    "logging": {
        "level": "DEBUG",
        "sinks": ["stdout", "file"],
        "files": {"main": {"path": "/var/log/app.log"}},
    },
    "services": {
        "billing": {
            "timeout": 30,
            "domains": ["core", "payments"],
            "retries": {"max": 5, "backoff": "exponential", "jitter": True},
        },
        "search": {
            "timeout": 80,
            "domains": ["read-only"],
            "cache": {"ttl": 120, "strategy": "request-window"},
        },
        "new_service": {"timeout": 45, "regions": ["us-east", "ap-south"]},
    },
    "routers": [
        {
            "name": "edge",
            "hosts": ["app.example.com"],
            "headers": {"x-trace": "1", "Cache-Control": "no-store"},
        }
    ],
    "feature_flags": {"checkout": {"enabled": True, "percent": 25}},
}


def load_solution(path: Path):
    spec = importlib.util.spec_from_file_location("submission", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, "solution"):
        raise AssertionError("submission must define solution()")
    func = module.solution  # type: ignore[attr-defined]
    if not callable(func):
        raise AssertionError("solution must be callable")
    return func


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python config_patch_engine.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)
    source = deepcopy(BASE_CONFIG)
    result = func(source, OPERATIONS)
    if result != EXPECTED_CONFIG:
        raise AssertionError(f"config mismatch:\nexpected {EXPECTED_CONFIG}\n got {result}")
    if source != BASE_CONFIG:
        raise AssertionError("solution must not mutate the base config in-place")
    print("PASS")


if __name__ == "__main__":
    main()
