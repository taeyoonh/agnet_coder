from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

CHANGELOG_SAMPLE = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Job queue instrumentation for the scheduler (off by default)
- Skip nightly rebuilds when the workspace hash is unchanged (#231)

### Fixed
- docs: patch upgrade instructions for air-gapped installs
- Handle Windows path that includes a colon in the workspace root

## [2.1.0] - 2024-09-24
### Added
- CLI `deploy --dry-run` switch to preview release impact
- Verify SAML metadata export for EU tenants

### Changed
- Reorganized config loader fallback order
- Local cache now hashes environment keys to prevent collisions

### Fixed
- Guard nil pointer when env var is missing (#202)

## [2.0.1] - 2024-08-01
### Fixed
- Patch release for OAuth double encoding (#210)
"""

EXPECTED_ENTRIES_SAMPLE = [
    {
        "label": "Unreleased",
        "date": None,
        "sections": {
            "Added": [
                "Job queue instrumentation for the scheduler (off by default)",
                "Skip nightly rebuilds when the workspace hash is unchanged (#231)",
            ],
            "Fixed": [
                "docs: patch upgrade instructions for air-gapped installs",
                "Handle Windows path that includes a colon in the workspace root",
            ],
        },
    },
    {
        "label": "2.1.0",
        "date": "2024-09-24",
        "sections": {
            "Added": [
                "CLI `deploy --dry-run` switch to preview release impact",
                "Verify SAML metadata export for EU tenants",
            ],
            "Changed": [
                "Reorganized config loader fallback order",
                "Local cache now hashes environment keys to prevent collisions",
            ],
            "Fixed": [
                "Guard nil pointer when env var is missing (#202)",
            ],
        },
    },
    {
        "label": "2.0.1",
        "date": "2024-08-01",
        "sections": {
            "Fixed": [
                "Patch release for OAuth double encoding (#210)",
            ],
        },
    },
]

EXPECTED_SAMPLE = {
    "latest_release": EXPECTED_ENTRIES_SAMPLE[1],
    "entries": EXPECTED_ENTRIES_SAMPLE,
}

REGRESSION_SAMPLE = """# Mini changelog

## [1.0.1] - 2023-02-11
### Security
- Rotate service tokens weekly

### Fixed
- Avoid leaking temporary files on Windows

## [1.0.0] - 2023-01-01
### Added
- First public release
- Include observability exporter
"""

EXPECTED_ENTRIES_REGRESSION = [
    {
        "label": "1.0.1",
        "date": "2023-02-11",
        "sections": {
            "Security": [
                "Rotate service tokens weekly",
            ],
            "Fixed": [
                "Avoid leaking temporary files on Windows",
            ],
        },
    },
    {
        "label": "1.0.0",
        "date": "2023-01-01",
        "sections": {
            "Added": [
                "First public release",
                "Include observability exporter",
            ],
        },
    },
]

EXPECTED_REGRESSION = {
    "latest_release": EXPECTED_ENTRIES_REGRESSION[0],
    "entries": EXPECTED_ENTRIES_REGRESSION,
}


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


def assert_entries(actual: Any, expected: list[dict[str, Any]], label: str) -> None:
    if not isinstance(actual, list):
        raise AssertionError(f"{label} must be a list, got {type(actual)!r}")
    if len(actual) != len(expected):
        raise AssertionError(
            f"{label} length mismatch: expected {len(expected)}, got {len(actual)}"
        )
    for idx, (got, want) in enumerate(zip(actual, expected)):
        if not isinstance(got, dict):
            raise AssertionError(f"{label}[{idx}] must be dict, got {type(got)!r}")
        for key in ("label", "date", "sections"):
            if key not in got:
                raise AssertionError(f"{label}[{idx}] missing field: {key}")
        if got["label"] != want["label"]:
            raise AssertionError(
                f"{label}[{idx}] label mismatch: expected {want['label']}, got {got['label']}"
            )
        if got["date"] != want["date"]:
            raise AssertionError(
                f"{label}[{idx}] date mismatch: expected {want['date']}, got {got['date']}"
            )
        sections = got["sections"]
        if not isinstance(sections, dict):
            raise AssertionError(f"{label}[{idx}].sections must be dict, got {type(sections)!r}")
        expected_sections = want["sections"]
        if set(sections) != set(expected_sections):
            raise AssertionError(
                f"{label}[{idx}] sections mismatch: expected {set(expected_sections)}, got {set(sections)}"
            )
        for sec_name, expected_items in expected_sections.items():
            items = sections.get(sec_name)
            if items != expected_items:
                raise AssertionError(
                    f"{label}[{idx}] section {sec_name!r} mismatch:\nexpected {expected_items}\n got {items}"
                )


def assert_latest_release(result: dict[str, Any], expected: dict[str, Any]) -> None:
    latest = result.get("latest_release")
    if not isinstance(latest, dict):
        raise AssertionError("latest_release must be a dict")
    for key in ("label", "date", "sections"):
        if latest.get(key) != expected.get(key):
            raise AssertionError(
                f"latest_release[{key}] mismatch: expected {expected.get(key)}, got {latest.get(key)}"
            )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python changelog_parser.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)

    result = func(CHANGELOG_SAMPLE)
    if not isinstance(result, dict):
        raise AssertionError("solution must return a dict")
    assert_entries(result.get("entries"), EXPECTED_ENTRIES_SAMPLE, "primary entries")
    assert_latest_release(result, EXPECTED_SAMPLE["latest_release"])

    regression = func(REGRESSION_SAMPLE)
    if not isinstance(regression, dict):
        raise AssertionError("solution must return a dict")
    assert_entries(regression.get("entries"), EXPECTED_ENTRIES_REGRESSION, "reg entries")
    assert_latest_release(regression, EXPECTED_REGRESSION["latest_release"])

    print("PASS")


if __name__ == "__main__":
    main()
