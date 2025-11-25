from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    (([], []), []),
    (([1, 3, 5], []), [1, 3, 5]),
    (([], [2, 4]), [2, 4]),
    (([1, 2, 4], [1, 3, 4]), [1, 1, 2, 3, 4, 4]),
    (([1, 5, 9], [2, 2, 2]), [1, 2, 2, 2, 5, 9]),
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
        raise SystemExit("usage: python merge_sorted_lists.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for (a, b), expected in CASES:
        a_copy = a[:]
        b_copy = b[:]
        result = func(a_copy, b_copy)
        if result != expected:
            raise AssertionError(
                f"a={a!r}, b={b!r}, expected {expected!r}, got {result!r}"
            )
        if a_copy != a or b_copy != b:
            raise AssertionError("input lists must not be mutated")

    print("PASS")


if __name__ == "__main__":
    main()
