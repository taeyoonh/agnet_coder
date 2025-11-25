from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    ([], 0),
    ([(0, 30), (5, 10), (15, 20)], 2),
    ([(7, 10), (2, 4)], 1),
    ([(1, 2), (2, 3), (3, 4)], 1),
    ([(1, 4), (2, 5), (7, 9)], 2),
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
        raise SystemExit('usage: python meeting_rooms_min.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for intervals, expected in CASES:
        result = func(list(intervals))
        if result != expected:
            raise AssertionError(
                f"intervals={intervals!r}, expected {expected}, got {result!r}"
            )

    print('PASS')


if __name__ == '__main__':
    main()
