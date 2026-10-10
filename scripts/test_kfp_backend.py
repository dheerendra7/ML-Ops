#!/usr/bin/env python3
"""Submit pass/fail pipeline runs to a disposable standalone KFP backend."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from kfp import Client, compiler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.kfp.pipeline_artifacts_caching import (  # noqa: E402
    artifact_and_quality_gate_pipeline,
)

EXPECTED_APPROVAL = "approved-for-teaching-example-only"


def normalise_state(value: Any) -> str:
    return str(value or "").rsplit(".", 1)[-1].lower()


def wait_for_api(host: str, attempts: int, delay_seconds: int) -> Client:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            # Client construction itself probes the health endpoint, so it
            # must live inside the retry loop too. This covers the race where
            # kubectl port-forward has started as a process but is not serving
            # its local port yet.
            client = Client(host=host)
            client.list_experiments(page_size=1)
            print(f"PASS: standalone KFP API answered on attempt {attempt}")
            return client
        except Exception as exc:  # API may still be starting or dependencies warming up.
            last_error = exc
            if attempt < attempts:
                time.sleep(delay_seconds)
    raise RuntimeError(
        f"KFP API did not become ready after {attempts} attempts; "
        f"last error type={type(last_error).__name__}"
    ) from last_error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile and submit success/rejection runs to a disposable KFP backend."
    )
    parser.add_argument("--host", default="http://127.0.0.1:8888")
    parser.add_argument("--package", required=True, help="Output path for the compiled pipeline package.")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--api-attempts", type=int, default=60)
    parser.add_argument("--api-delay-seconds", type=int, default=2)
    args = parser.parse_args()

    package_path = Path(args.package).resolve()
    package_path.parent.mkdir(parents=True, exist_ok=True)
    compiler.Compiler().compile(
        pipeline_func=artifact_and_quality_gate_pipeline,
        package_path=str(package_path),
    )
    if not package_path.is_file() or package_path.stat().st_size == 0:
        raise AssertionError("KFP compiler did not write a non-empty pipeline package")
    print("PASS: compiled KFP pipeline package")

    client = wait_for_api(args.host, args.api_attempts, args.api_delay_seconds)
    experiment = client.create_experiment(name="mlops-handbook-backend-smoke")
    experiment_id = experiment.experiment_id

    passing = client.create_run_from_pipeline_package(
        pipeline_file=str(package_path),
        arguments={"offset": 0.0, "minimum_score": 0.8},
        experiment_id=experiment_id,
        run_name="handbook-backend-pass",
        enable_caching=False,
    )
    passing_result = client.wait_for_run_completion(
        run_id=passing.run_id,
        timeout=args.timeout_seconds,
        sleep_duration=5,
    )
    passing_state = normalise_state(passing_result.state)
    if passing_state != "succeeded":
        raise AssertionError(
            f"Remote passing pipeline run expected SUCCEEDED, got {passing_result.state!r}"
        )
    print(f"PASS: remote KFP success path completed (run_id={passing.run_id})")

    rejected = client.create_run_from_pipeline_package(
        pipeline_file=str(package_path),
        arguments={"offset": 1.0, "minimum_score": 0.8},
        experiment_id=experiment_id,
        run_name="handbook-backend-rejected-candidate",
        enable_caching=False,
    )
    rejected_result = client.wait_for_run_completion(
        run_id=rejected.run_id,
        timeout=args.timeout_seconds,
        sleep_duration=5,
    )
    rejected_state = normalise_state(rejected_result.state)
    if rejected_state != "failed":
        raise AssertionError(
            "Remote rejected-candidate run expected FAILED at the quality gate, "
            f"got {rejected_result.state!r}"
        )
    print(
        "PASS: remote KFP rejected-candidate path ended FAILED as expected "
        f"(run_id={rejected.run_id})"
    )
    print("KFP backend smoke test passed: API, run submission, artifact flow, and gate rejection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
