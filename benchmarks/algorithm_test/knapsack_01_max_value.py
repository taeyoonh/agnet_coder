from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CASES = [
    (([1, 2, 3], [6, 10, 12], 5), 22),
    (([2, 3, 4], [4, 5, 6], 5), 9),
    (([3, 4, 5], [30, 50, 60], 8), 90),
    (([1, 2], [10, 20], 0), 0),
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
        raise SystemExit('usage: python knapsack_01_max_value.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for (weights, values, capacity), expected in CASES:
        result = func(list(weights), list(values), capacity)
        if result != expected:
            raise AssertionError(
                f"weights={weights!r}, values={values!r}, capacity={capacity}, "
                f"expected {expected}, got {result!r}"
            )

    print('PASS')


if __name__ == '__main__':
    main()
