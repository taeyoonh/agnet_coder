from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    (([1, 2, 5], 11), 3),
    (([2], 3), -1),
    (([1], 0), 0),
    (([2, 5, 10, 1], 27), 4),
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
        raise SystemExit('usage: python coin_change_min_coins.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for (coins, amount), expected in CASES:
        result = func(list(coins), amount)
        if result != expected:
            raise AssertionError(
                f"coins={coins!r}, amount={amount}, expected {expected}, got {result!r}"
            )

    print('PASS')


if __name__ == '__main__':
    main()
