"""Checker for SWE-bench inspired Django slugify bug."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

CASES = [
    ("Hello, World!", False, "hello-world"),
    ("Spam_and   Eggs", False, "spam-and-eggs"),
    ("already-slug--value", False, "already-slug-value"),
    ("멀티 agent 테스트", True, "멀티-agent-테스트"),
    ("  trim---ME  ", False, "trim-me"),
    ("", False, ""),
]

SEPARATOR_RE = re.compile(r"^[a-z0-9\-]+$")
UNICODE_SEPARATOR_RE = re.compile(r"^[\w\-]+$", re.UNICODE)


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


def check_slug(slug: str, allow_unicode: bool):
    if allow_unicode:
        pattern = UNICODE_SEPARATOR_RE
    else:
        pattern = SEPARATOR_RE
    if slug and not pattern.match(slug):
        raise AssertionError(
            f"Slug contains invalid characters for allow_unicode={allow_unicode}: {slug!r}"
        )
    if "--" in slug:
        raise AssertionError("Slug must collapse consecutive hyphens")
    if slug.startswith("-") or slug.endswith("-"):
        raise AssertionError("Slug must not start or end with hyphen")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python bugfix_swebench_django_slugify.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for value, allow_unicode, expected in CASES:
        result = func(value, allow_unicode)
        if result != expected:
            raise AssertionError(
                f"slugify({value!r}, allow_unicode={allow_unicode}) => {result!r}, expected {expected!r}"
            )
        check_slug(result, allow_unicode)

    print("PASS")


if __name__ == "__main__":
    main()
