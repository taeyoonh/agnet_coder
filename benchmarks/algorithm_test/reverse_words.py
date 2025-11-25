from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ("", ""),
    ("hello", "hello"),
    ("hello world", "world hello"),
    ("  hello   world  ", "world hello"),
    ("a b  c", "c b a"),
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


def split_words(s: str) -> list[str]:
    return s.split(" ") if s == "" else s.split()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python reverse_words.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for text, expected in CASES:
        result = func(text)
        if result != expected:
            raise AssertionError(f"text={text!r}, expected {expected!r}, got {result!r}")

    print("PASS")


if __name__ == "__main__":
    main()
