"""Checker for QuixBugs-inspired depth-first search task."""

from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

GRAPHS = [
    (
        {
            "a": ["b", "c"],
            "b": ["d"],
            "c": ["e"],
            "d": ["c"],
            "e": [],
        },
        "a",
        ["a", "b", "d", "c", "e"],
    ),
    (
        {
            "s": ["a", "b"],
            "a": ["c", "d"],
            "b": ["e"],
            "c": [],
            "d": ["e"],
            "e": [],
        },
        "s",
        ["s", "a", "c", "d", "e", "b"],
    ),
    (
        {
            "x": ["y"],
            "y": ["z"],
            "z": ["x"],
        },
        "x",
        ["x", "y", "z"],
    ),
    (
        {
            "1": ["2", "3"],
            "2": ["4", "5"],
            "3": ["5"],
            "4": [],
            "5": ["6"],
            "6": [],
        },
        "2",
        ["2", "4", "5", "6"],
    ),
]

ERROR_CASES = [
    ({"a": ["b"]}, "z"),
]


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


def assert_dfs(func, graph, start, expected):
    original = deepcopy(graph)
    result = func(graph, start)
    if graph != original:
        raise AssertionError("solution must not mutate input graph")
    if not isinstance(result, list):
        raise AssertionError("result must be a list")
    if result != expected:
        raise AssertionError(
            f"DFS order mismatch for start={start!r}. Expected {expected}, got {result}"
        )


def assert_errors(func, graph, start):
    try:
        func(graph, start)
    except ValueError:
        return
    raise AssertionError("solution must raise ValueError when start node is missing")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python bugfix_quixbugs_depth_first_search.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for graph, start, expected in GRAPHS:
        assert_dfs(func, graph, start, expected)

    for graph, start in ERROR_CASES:
        assert_errors(func, graph, start)

    print("PASS")


if __name__ == "__main__":
    main()
