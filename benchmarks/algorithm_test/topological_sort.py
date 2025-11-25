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
        [['a', 'b', 'c', 'd'], ['a', 'c', 'b', 'd']],
    ),
    (
        {
            'k': ['a', 'b'],
            'a': [],
            'b': [],
        },
        [['k', 'a', 'b'], ['k', 'b', 'a']],
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


def is_valid_topo(graph: dict[str, list[str]], order: list[str]) -> bool:
    pos = {node: i for i, node in enumerate(order)}
    if set(pos.keys()) != set(graph.keys()):
        return False
    for u, nbrs in graph.items():
        for v in nbrs:
            if pos[u] >= pos[v]:
                return False
    return True


def lexicographically_smallest(valid_orders: list[list[str]]) -> list[str]:
    return min(valid_orders)


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: python topological_sort.py <submission.py>')
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    for graph, valid_orders in GRAPHS:
        result = func(dict(graph))
        if not is_valid_topo(graph, result):
            raise AssertionError(f"result {result!r} is not a valid topological order")
        expected = lexicographically_smallest(valid_orders)
        if result != expected:
            raise AssertionError(
                f"expected lexicographically smallest {expected!r}, got {result!r}"
            )

    print('PASS')


if __name__ == '__main__':
    main()
