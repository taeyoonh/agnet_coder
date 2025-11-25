from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ("", 0),
    ("a", 1),
    ("aa", 1),
    ("ab", 2),
    ("abcabcbb", 3),  # "abc"
    ("bbbbb", 1),     # "b"
    ("pwwkew", 3),    # "wke"
    ("dvdf", 3),      # "vdf"
    ("abba", 2),      # "ab" or "ba"
    ("tmmzuxt", 5),   # "mzuxt"
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
        raise SystemExit("usage: python longest_unique_substring.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for s, expected in CASES:
        result = func(s)
        if not isinstance(result, int):
            raise AssertionError(
                f"s={s!r}, result must be int, got {type(result).__name__}"
            )
        if result != expected:
            raise AssertionError(
                f"s={s!r}, expected {expected!r}, got {result!r}"
            )

    print("PASS")


if __name__ == "__main__":
    main()
