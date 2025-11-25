from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ("", 0),
    ("bcdfg", 0),
    ("aeiou", 5),
    ("AEIOU", 5),
    ("Hello, World!", 3),
    ("UnIverSity", 4),
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
        raise SystemExit("usage: python count_vowels.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for text, expected in CASES:
        result = func(text)
        if result != expected:
            raise AssertionError(f"text={text!r}, expected {expected}, got {result!r}")

    print("PASS")


if __name__ == "__main__":
    main()
