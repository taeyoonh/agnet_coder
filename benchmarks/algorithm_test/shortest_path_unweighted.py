from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

GRAPHS = [
    (
        {
            'a': ['b', 'c'],
            'b': ['d'],
            'c': ['d'],
            'd': [],
        },
        'a',
        {'a': 0, 'b': 1, 'c': 1, 'd': 2},
    ),
    (
        {
            's': ['a', 'b'],
            'a': ['c'],
            'b': [],
            'c': [],
        },
        's',
        {'s': 0, 'a': 1, 'b': 1, 'c': 2},
    ),
]

ERROR_CASES = [
    (
        {
            'a': [],
        },
        'z',
    )
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
        raise SystemExit('usage: python shortest_path_unweighted.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for graph, start, expected in GRAPHS:
        result = func(dict(graph), start)
        if result != expected:
            raise AssertionError(
                f"graph={graph!r}, start={start!r}, expected {expected!r}, got {result!r}"
            )

    for graph, start in ERROR_CASES:
        try:
            func(dict(graph), start)
        except ValueError:
            pass
        else:
            raise AssertionError('expected ValueError for missing start node')

    print('PASS')


if __name__ == '__main__':
    main()
