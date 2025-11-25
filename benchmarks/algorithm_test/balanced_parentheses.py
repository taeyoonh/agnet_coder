from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ("", True),
    ("abc", True),
    ("()", True),
    ("([])", True),
    ("({[]})", True),
    ("(]", False),
    ("([)]", False),
    ("(a[)]", False),
    (")(", False),
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
        raise SystemExit("usage: python balanced_parentheses.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for s, expected in CASES:
        result = func(s)
        if result is not expected:
            raise AssertionError(f"s={s!r}, expected {expected}, got {result!r}")

    print("PASS")


if __name__ == "__main__":
    main()
