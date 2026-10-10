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
    state = str(value or "").rsplit(".", 1)[-1].lower()
    # The v2beta1 API uses values such as SUCCEEDED, while some generated
    # clients may expose the enum name with its RUNTIME_STATE_ prefix.
    if state.startswith("runtime_state_"):
        state = state.removeprefix("runtime_state_")
    return state


def read_field(value: Any, name: str) -> Any:
    """Read an API model field without coupling tests to dict vs SDK objects."""
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def run_task_details(run_detail: Any) -> dict[str, Any]:
    """Return unique named task details; fail closed if the API omitted them."""
    runtime = read_field(run_detail, "run_details")
    details = read_field(runtime, "task_details")
    if not isinstance(details, (list, tuple)) or not details:
        raise AssertionError(
            "KFP run response did not include non-empty run_details.task_details"
        )

    named: dict[str, Any] = {}
    for detail in details:
        name = str(read_field(detail, "display_name") or "").strip()
        if not name:
            raise AssertionError("KFP task detail is missing display_name")
        if name in named:
            raise AssertionError(f"KFP response contains duplicate task name {name!r}")
        named[name] = detail
    return named


def require_task_state(
    tasks: dict[str, Any], task_name: str, expected_state: str
) -> Any:
    detail = tasks.get(task_name)
    if detail is None:
        raise AssertionError(
            f"Expected task {task_name!r} was not present in KFP run details; "
            f"observed tasks={sorted(tasks)}"
        )
    actual = normalise_state(read_field(detail, "state"))
    if actual != expected_state:
        error = read_field(detail, "error")
        message = read_field(error, "message") if error is not None else None
        raise AssertionError(
            f"Task {task_name!r} expected state {expected_state!r}, got "
            f"{actual!r}; error_message={message!r}"
        )
    return detail


def artifact_ids_for(task: Any, direction: str, artifact_name: str) -> list[str]:
    """Return non-empty artifact IDs, without logging IDs or artifact metadata."""
    artifacts = read_field(task, direction)
    artifact_list = (
        artifacts.get(artifact_name) if isinstance(artifacts, dict) else None
    )
    artifact_ids = read_field(artifact_list, "artifact_ids")
    if (
        not isinstance(artifact_ids, (list, tuple))
        or not artifact_ids
        or any(not isinstance(value, (str, int)) or not str(value).strip() for value in artifact_ids)
    ):
        raise AssertionError(
            f"Expected a recorded {direction} artifact reference "
            f"for {artifact_name!r}; no valid artifact IDs were returned"
        )
    return [str(value) for value in artifact_ids]


def require_artifact_reference(
    task: Any, direction: str, artifact_name: str
) -> None:
    """Assert an artifact ID was recorded without printing metadata values."""
    artifact_ids_for(task, direction, artifact_name)


def require_artifact_handoff(
    producer_task: Any, consumer_task: Any, artifact_name: str
) -> None:
    """Ensure consumer inputs reference the same artifacts the producer emitted."""
    produced_ids = artifact_ids_for(producer_task, "outputs", artifact_name)
    consumed_ids = artifact_ids_for(consumer_task, "inputs", artifact_name)
    if set(produced_ids) != set(consumed_ids):
        raise AssertionError(
            f"Artifact hand-off mismatch for {artifact_name!r}: "
            "producer output IDs and consumer input IDs differ"
        )


def verify_successful_run(run_detail: Any) -> None:
    tasks = run_task_details(run_detail)
    dataset = require_task_state(tasks, "create-toy-dataset", "succeeded")
    trainer = require_task_state(tasks, "train-toy-model", "succeeded")
    evaluator = require_task_state(tasks, "evaluate-toy-model", "succeeded")
    require_task_state(tasks, "enforce-quality-gate", "succeeded")
    require_artifact_reference(dataset, "outputs", "dataset")
    require_artifact_reference(trainer, "inputs", "dataset")
    require_artifact_reference(trainer, "outputs", "model")
    require_artifact_reference(evaluator, "inputs", "model")
    require_artifact_handoff(dataset, trainer, "dataset")
    require_artifact_handoff(trainer, evaluator, "model")
    require_artifact_handoff(dataset, trainer, "dataset")
    require_artifact_handoff(trainer, evaluator, "model")
    print(
        "PASS: remote run task states and Dataset/Model artifact references "
        "confirm the expected end-to-end success path"
    )


def verify_rejected_run(run_detail: Any) -> None:
    tasks = run_task_details(run_detail)
    # A generic FAILED run is not enough: every upstream task must succeed and
    # the quality-gate task itself must be the one that rejects the candidate.
    dataset = require_task_state(tasks, "create-toy-dataset", "succeeded")
    trainer = require_task_state(tasks, "train-toy-model", "succeeded")
    evaluator = require_task_state(tasks, "evaluate-toy-model", "succeeded")
    require_task_state(tasks, "enforce-quality-gate", "failed")
    require_artifact_reference(dataset, "outputs", "dataset")
    require_artifact_reference(trainer, "inputs", "dataset")
    require_artifact_reference(trainer, "outputs", "model")
    require_artifact_reference(evaluator, "inputs", "model")
    print(
        "PASS: remote rejected-candidate run failed specifically at the "
        "quality gate after successful upstream execution and artifact hand-off"
    )


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
    # Fetch the full run again so task details and artifact references are
    # checked explicitly rather than inferred from the terminal run state.
    verify_successful_run(client.get_run(passing.run_id))
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
    verify_rejected_run(client.get_run(rejected.run_id))
    print(
        "PASS: remote KFP rejected-candidate path ended FAILED at the expected task "
        f"(run_id={rejected.run_id})"
    )
    print(
        "KFP backend smoke test passed: API, run submission, upstream task "
        "states, Dataset/Model artifact references, and gate-specific rejection."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
