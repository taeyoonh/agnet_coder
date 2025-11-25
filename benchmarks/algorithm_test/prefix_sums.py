from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([], []),
    ([1], [1]),
    ([1, 2, 3], [1, 3, 6]),
    ([5, -2, 4], [5, 3, 7]),
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
        raise SystemExit("usage: python prefix_sums.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for nums, expected in CASES:
        result = func(nums[:])
        if result != expected:
            raise AssertionError(f"nums={nums!r}, expected {expected}, got {result!r}")
        # input 불변성은 심하게 따지지 않음 (이미 복사본 전달)

    print("PASS")


if __name__ == "__main__":
    main()
