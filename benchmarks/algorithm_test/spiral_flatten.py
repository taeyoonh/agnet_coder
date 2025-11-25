"""Checker for spiral_flatten benchmark task."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([[1]], [1]),
    ([[1, 2], [3, 4]], [1, 2, 4, 3]),
    (
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
        [1, 2, 3, 6, 9, 8, 7, 4, 5],
    ),
    (
        [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
        ],
        [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7],
    ),
    (
        [
            [3, 4, 5],
            [6, 7, 8],
        ],
        [3, 4, 5, 8, 7, 6],
    ),
]


def load_solution(path: Path):
    spec = importlib.util.spec_from_file_location("submission", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, "solution"):
        raise AssertionError("submission must define solution()")
    return module.solution  # type: ignore[attr-defined]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python spiral_flatten.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for matrix, expected in CASES:
        result = func([row[:] for row in matrix])
        if result != expected:
            raise AssertionError(
                f"Input={matrix!r}, expected {expected!r}, got {result!r}"
            )

    print("PASS")


if __name__ == "__main__":
    main()
