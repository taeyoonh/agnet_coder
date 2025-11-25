from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

CASES = [
    ([['1']], 1),
    ([['0']], 0),
    (
        [
            ['1', '1', '0', '0'],
            ['1', '0', '0', '1'],
            ['0', '0', '1', '1'],
        ],
        2,
    ),
    (
        [
            ['1', '1', '1'],
            ['0', '1', '0'],
            ['1', '1', '1'],
        ],
        1,
    ),
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
        raise SystemExit('usage: python num_islands.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for grid, expected in CASES:
        original = deepcopy(grid)
        result = func(deepcopy(grid))
        if result != expected:
            raise AssertionError(f"grid={grid!r}, expected {expected}, got {result!r}")
        if grid != original:
            raise AssertionError('input grid must not be mutated')

    print('PASS')


if __name__ == '__main__':
    main()
