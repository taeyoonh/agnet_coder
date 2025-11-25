from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([[1]], [[1]]),
    ([[1, 2]], [[1], [2]]),
    ([[1], [2]], [[1, 2]]),
    ([[1, 2, 3], [4, 5, 6]], [[1, 4], [2, 5], [3, 6]]),
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
        raise SystemExit("usage: python matrix_transpose.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for matrix, expected in CASES:
        original = [row[:] for row in matrix]
        result = func([row[:] for row in matrix])
        if result != expected:
            raise AssertionError(
                f"matrix={matrix!r}, expected {expected!r}, got {result!r}"
            )
        if matrix != original:
            raise AssertionError("input matrix must not be mutated")

    print("PASS")


if __name__ == "__main__":
    main()
