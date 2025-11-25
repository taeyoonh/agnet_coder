from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([], 0),
    ([2], 2),
    ([2, 1, 5, 6, 2, 3], 10),
    ([2, 4], 4),
    ([6, 2, 5, 4, 5, 1, 6], 12),
]


def load_solution(path: Path):
    spec = importlib.util.spec_from_file_location('submission', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, 'solution'):
        raise AssertionError('submission must define solution()')
    func = module.solution  # type: ignore[attr-defined]
    if not callable(func):
        raise AssertionError('solution must be callable')
    return func


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: python max_rectangle_in_histogram.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for heights, expected in CASES:
        result = func(list(heights))
        if result != expected:
            raise AssertionError(
                f"heights={heights!r}, expected {expected}, got {result!r}"
            )

    print('PASS')


if __name__ == '__main__':
    main()
