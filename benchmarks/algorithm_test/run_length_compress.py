"""Checker for run_length_compress benchmark task."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ("", ""),
    ("a", "a1"),
    ("aaabbc", "a3b2c1"),
    ("XYZ", "X1Y1Z1"),
    ("   ", " 3"),
    ("112233", "122232"),
    ("--==!!", "-2=2!2"),
    ("aaAAAAAabb", "a2A5a1b2"),
]


def load_solution(path: Path):
    spec = importlib.util.spec_from_file_location("submission", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, "solution"):
        raise AssertionError("submission must define solution()")
    return module.solution  # type: ignore[attr-defined]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python run_length_compress.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for text, expected in CASES:
        result = func(text)
        if result != expected:
            raise AssertionError(f"Input={text!r}, expected {expected!r}, got {result!r}")

    print("PASS")


if __name__ == "__main__":
    main()
