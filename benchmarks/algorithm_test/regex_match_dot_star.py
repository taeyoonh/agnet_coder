from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    (("aa", "a"), False),
    (("aa", "a*"), True),
    (("ab", ".*"), True),
    (("aab", "c*a*b"), True),
    (("mississippi", "mis*is*p*."), False),
    (("mississippi", "mis*is*ip*."), True),
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
        raise SystemExit(
            "usage: python regex_match_dot_star.py <submission.py>"
        )
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for (s, p), expected in CASES:
        result = func(s, p)
        if result is not expected:
            raise AssertionError(
                f"s={s!r}, p={p!r}, expected {expected}, got {result!r}"
            )

    print("PASS")


if __name__ == "__main__":
    main()
