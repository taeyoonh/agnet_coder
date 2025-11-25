"""Checker for two_sum_indices benchmark task."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([2, 7, 11, 15], 9, (0, 1)),
    ([3, 2, 4], 6, (1, 2)),
    ([3, 3], 6, (0, 1)),
    ([-1, -2, -3, -4, -5], -8, (2, 4)),
    ([0, 4, 3, 0], 0, (0, 3)),
    ([1, 5, 1, 5], 6, (0, 1)),
]


def load_solution(path: Path):
    spec = importlib.util.spec_from_file_location("submission", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, "solution"):
        raise AssertionError("submission must define solution()")
    return module.solution  # type: ignore[attr-defined]


def check_pair(nums, target, pair):
    if not isinstance(pair, tuple):
        raise AssertionError("solution must return tuple")
    if len(pair) != 2:
        raise AssertionError("tuple must contain exactly two indices")
    i, j = pair
    if not all(isinstance(x, int) for x in pair):
        raise AssertionError("indices must be integers")
    if not (0 <= i < j < len(nums)):
        raise AssertionError("indices must satisfy 0 <= i < j < len(nums)")
    if nums[i] + nums[j] != target:
        raise AssertionError("selected indices do not sum to target")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python two_sum_indices.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for nums, target, expected in CASES:
        result = func(nums[:], target)
        check_pair(nums, target, result)
        if result != expected:
            raise AssertionError(
                f"Expected lexicographically smallest pair {expected}, got {result}"
            )

    print("PASS")


if __name__ == "__main__":
    main()
