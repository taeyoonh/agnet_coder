from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    (([1, 2, 3, 3], [3, 4, 5, 6], [50, 10, 40, 70]), 120),
    (([1, 2, 3, 4], [3, 5, 10, 6], [20, 20, 100, 70]), 150),
    (([1, 1, 1], [2, 3, 4], [5, 6, 4]), 10),
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
        raise SystemExit('usage: python job_scheduling_max_profit.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for (starts, ends, profits), expected in CASES:
        result = func(list(starts), list(ends), list(profits))
        if result != expected:
            raise AssertionError(
                f"starts={starts!r}, ends={ends!r}, profits={profits!r}, "
                f"expected {expected}, got {result!r}"
            )

    print('PASS')


if __name__ == '__main__':
    main()
