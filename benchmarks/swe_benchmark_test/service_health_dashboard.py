from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

SNAPSHOTS = [
    {
        "service": "billing",
        "region": "us-east",
        "latency_ms_p95": 180,
        "error_rate": 1.7,
        "uptime": 0.982,
        "alerts": ["queue_backlog"],
        "deploy_offset_min": 170,
    },
    {
        "service": "billing",
        "region": "eu-west",
        "latency_ms_p95": 118,
        "error_rate": 0.4,
        "uptime": 0.999,
        "alerts": [],
        "deploy_offset_min": 70,
    },
    {
        "service": "auth",
        "region": "us-east",
        "latency_ms_p95": 90,
        "error_rate": 0.2,
        "uptime": 0.999,
        "alerts": [],
        "deploy_offset_min": 20,
    },
    {
        "service": "auth",
        "region": "ap-south",
        "latency_ms_p95": 240,
        "error_rate": 3.4,
        "uptime": 0.91,
        "alerts": ["outage", "pagerduty"],
        "deploy_offset_min": 10,
    },
    {
        "service": "search",
        "region": "us-west",
        "latency_ms_p95": 130,
        "error_rate": 0.1,
        "uptime": 0.997,
        "alerts": [],
        "deploy_offset_min": 200,
    },
]

EXPECTED_SERVICE_STATUS = {
    "billing": "DEGRADED",
    "auth": "DOWN",
    "search": "DEGRADED",
}

EXPECTED_REGION_STATUS = {
    ("billing", "us-east"): "DEGRADED",
    ("billing", "eu-west"): "HEALTHY",
    ("auth", "us-east"): "HEALTHY",
    ("auth", "ap-south"): "DOWN",
    ("search", "us-west"): "DEGRADED",
}

EXPECTED_ACTIONS = {
    "billing": {
        "billing/us-east: latency p95 180ms exceeds 140ms budget",
        "billing/us-east: error rate 1.70% exceeds 1.00% budget",
        "billing/us-east: outstanding alerts queue_backlog",
    },
    "auth": {
        "auth/ap-south: outage declared via alerts",
        "auth/ap-south: latency p95 240ms exceeds 140ms budget",
        "auth/ap-south: error rate 3.40% exceeds 1.00% budget",
    },
    "search": {
        "search/us-west: deploy overdue by 200 minutes",
    },
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


def assert_dashboard_structure(result: Any) -> None:
    if not isinstance(result, dict):
        raise AssertionError("solution must return a dict")
    for key in ("services", "global_status", "total_regions"):
        if key not in result:
            raise AssertionError(f"result missing required field: {key}")
    services = result["services"]
    if not isinstance(services, dict):
        raise AssertionError("services must be a dict")
    if set(services) != set(EXPECTED_SERVICE_STATUS):
        raise AssertionError(
            f"services set mismatch: expected {set(EXPECTED_SERVICE_STATUS)}, got {set(services)}"
        )
    if result["total_regions"] != len(SNAPSHOTS):
        raise AssertionError(
            f"total_regions mismatch: expected {len(SNAPSHOTS)}, got {result['total_regions']}"
        )
    if result["global_status"] != "DOWN":
        raise AssertionError(
            f"global_status mismatch: expected 'DOWN', got {result['global_status']}"
        )

    for service, summary in services.items():
        if not isinstance(summary, dict):
            raise AssertionError(f"{service} summary must be dict")
        if summary.get("status") != EXPECTED_SERVICE_STATUS[service]:
            raise AssertionError(
                f"{service} status mismatch: expected {EXPECTED_SERVICE_STATUS[service]}, got {summary.get('status')}"
            )
        regions = summary.get("regions")
        if not isinstance(regions, dict):
            raise AssertionError(f"{service}.regions must be dict")
        expected_regions = {
            region for svc, region in EXPECTED_REGION_STATUS if svc == service
        }
        if set(regions) != expected_regions:
            raise AssertionError(
                f"{service} regions mismatch: expected {expected_regions}, got {set(regions)}"
            )
        for region, payload in regions.items():
            if payload.get("status") != EXPECTED_REGION_STATUS[(service, region)]:
                raise AssertionError(
                    f"{service}/{region} status mismatch: "
                    f"expected {EXPECTED_REGION_STATUS[(service, region)]}, got {payload.get('status')}"
                )
        actions = summary.get("action_items")
        if actions is None:
            raise AssertionError(f"{service} missing action_items")
        action_set = set(actions)
        if not EXPECTED_ACTIONS[service].issubset(action_set):
            raise AssertionError(
                f"{service} action items mismatch:\nexpected subset {EXPECTED_ACTIONS[service]}\n got {action_set}"
            )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python service_health_dashboard.py <submission.py>")
    submission = Path(sys.argv[1])
    func = load_solution(submission)
    result = func(SNAPSHOTS)
    assert_dashboard_structure(result)
    print("PASS")


if __name__ == "__main__":
    main()
