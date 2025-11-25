from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    (([], 0), []),
    (([], 5), []),
    (([1], 0), [1]),
    (([1], 3), [1]),
    (([1, 2, 3, 4, 5], 1), [5, 1, 2, 3, 4]),
    (([1, 2, 3, 4, 5], 2), [4, 5, 1, 2, 3]),
    (([1, 2, 3, 4, 5], 7), [4, 5, 1, 2, 3]),
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


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python rotate_list_right.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for (nums, k), expected in CASES:
        nums_copy = nums[:]
        result = func(nums_copy, k)
        if result != expected:
            raise AssertionError(
                f"nums={nums!r}, k={k}, expected {expected!r}, got {result!r}"
            )

    print("PASS")


if __name__ == "__main__":
    main()
