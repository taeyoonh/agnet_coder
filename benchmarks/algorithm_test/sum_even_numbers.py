from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([], 0),
    ([1, 3, 5], 0),
    ([2, 4, 6], 12),
    ([1, 2, 3, 4, 5, 6], 12),
    ([-2, -3, -4, -5], -6),
    ([0, 1, 2], 2),
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
        raise SystemExit("usage: python sum_even_numbers.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for nums, expected in CASES:
        result = func(nums[:])
        if result != expected:
            raise AssertionError(f"nums={nums!r}, expected {expected}, got {result!r}")

    print("PASS")


if __name__ == "__main__":
    main()
