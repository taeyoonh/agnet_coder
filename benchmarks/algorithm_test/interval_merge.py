from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([], []),
    ([(1, 3)], [(1, 3)]),
    ([(1, 3), (2, 4)], [(1, 4)]),
    ([(1, 2), (3, 4)], [(1, 2), (3, 4)]),
    ([(1, 4), (2, 3)], [(1, 4)]),
    ([(1, 2), (2, 3)], [(1, 3)]),
    ([(5, 7), (1, 3), (2, 6)], [(1, 7)]),
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


def normalize(intervals):
    return [(int(a), int(b)) for a, b in intervals]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python interval_merge.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for intervals, expected in CASES:
        input_copy = list(intervals)
        result = func(list(intervals))
        if normalize(result) != expected:
            raise AssertionError(
                f"intervals={intervals!r}, expected {expected!r}, got {result!r}"
            )
        if input_copy != intervals:
            raise AssertionError("input must not be mutated in-place")

    print("PASS")


if __name__ == "__main__":
    main()
