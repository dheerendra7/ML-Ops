#!/usr/bin/env python3
"""Submit pass/fail pipeline runs to a disposable standalone KFP backend."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import yaml
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


EXPECTED_PIPELINE_TASKS = {
    "create-toy-dataset",
    "train-toy-model",
    "evaluate-toy-model",
    "enforce-quality-gate",
}


def run_task_details(run_detail: Any) -> dict[str, Any]:
    """Select required pipeline tasks and ignore duplicated internal executor nodes."""
    runtime = read_field(run_detail, "run_details")
    details = read_field(runtime, "task_details")
    if not isinstance(details, (list, tuple)) or not details:
        raise AssertionError(
            "KFP run response did not include non-empty run_details.task_details"
        )

    named: dict[str, Any] = {}
    observed_names: set[str] = set()
    for detail in details:
        name = str(read_field(detail, "display_name") or "").strip()
        if not name:
            continue
        observed_names.add(name)
        # A KFP run may include internal implementation nodes such as repeated
        # "executor" entries. Only named pipeline components are used for
        # these assertions; duplicate expected component names remain errors.
        if name not in EXPECTED_PIPELINE_TASKS:
            continue
        if name in named:
            raise AssertionError(
                f"KFP response contains duplicate pipeline task {name!r}"
            )
        named[name] = detail

    missing = EXPECTED_PIPELINE_TASKS - set(named)
    if missing:
        raise AssertionError(
            f"KFP run details omitted expected pipeline task(s): {sorted(missing)}; "
            f"observed display names={sorted(observed_names)}"
        )
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


def verify_artifact_wiring(pipeline_spec: Any) -> None:
    """Check that the compiled KFP IR wires Dataset and Model artifacts correctly.

    KFP 2.17's run-task API can omit runtime artifact IDs for Argo-backed tasks.
    Validate the compiled bindings directly, then let task-level remote execution
    prove that the consumer components successfully open and validate those files.
    """
    root = read_field(pipeline_spec, "root")
    dag = read_field(root, "dag")
    tasks = read_field(dag, "tasks")
    if not isinstance(tasks, dict):
        raise AssertionError("Compiled KFP package has no root.dag.tasks mapping")

    missing = EXPECTED_PIPELINE_TASKS - set(tasks)
    if missing:
        raise AssertionError(
            f"Compiled KFP package omitted expected pipeline tasks: {sorted(missing)}"
        )

    expected_bindings = (
        ("train-toy-model", "dataset", "create-toy-dataset", "dataset"),
        ("evaluate-toy-model", "model", "train-toy-model", "model"),
    )
    for consumer_name, input_name, producer_name, output_name in expected_bindings:
        consumer = tasks[consumer_name]
        inputs = read_field(consumer, "inputs") or {}
        artifacts = read_field(inputs, "artifacts") or {}
        binding = read_field(artifacts, input_name)
        task_output = read_field(binding, "taskOutputArtifact")
        actual_producer = read_field(task_output, "producerTask")
        actual_output = read_field(task_output, "outputArtifactKey")
        if actual_producer != producer_name or actual_output != output_name:
            raise AssertionError(
                f"Compiled artifact binding {consumer_name}.{input_name} expected "
                f"{producer_name}.{output_name}, got "
                f"{actual_producer!r}.{actual_output!r}"
            )


def verify_compiled_artifact_wiring(package_path: Path) -> None:
    try:
        pipeline_spec = yaml.safe_load(package_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AssertionError(f"Unable to read compiled KFP package YAML: {exc}") from exc
    verify_artifact_wiring(pipeline_spec)
    print(
        "PASS: compiled KFP package wires Dataset -> training and "
        "Model -> evaluation artifact inputs"
    )


def verify_successful_run(run_detail: Any) -> None:
    tasks = run_task_details(run_detail)
    require_task_state(tasks, "create-toy-dataset", "succeeded")
    require_task_state(tasks, "train-toy-model", "succeeded")
    require_task_state(tasks, "evaluate-toy-model", "succeeded")
    require_task_state(tasks, "enforce-quality-gate", "succeeded")
    print(
        "PASS: remote run completed every expected pipeline task; the training "
        "and evaluation components consumed their declared artifacts"
    )


def verify_rejected_run(run_detail: Any) -> None:
    tasks = run_task_details(run_detail)
    # A generic FAILED run is not enough: every upstream task must succeed and
    # the quality-gate task itself must be the one that rejects the candidate.
    require_task_state(tasks, "create-toy-dataset", "succeeded")
    require_task_state(tasks, "train-toy-model", "succeeded")
    require_task_state(tasks, "evaluate-toy-model", "succeeded")
    require_task_state(tasks, "enforce-quality-gate", "failed")
    print(
        "PASS: remote rejected-candidate run failed specifically at the "
        "quality gate after successful Dataset/Model-consuming upstream tasks"
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
    verify_compiled_artifact_wiring(package_path)

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
    # Fetch full run details so task-level states are checked explicitly rather
    # than inferred from the terminal run state.
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
        "KFP backend smoke test passed: API, run submission, expected task "
        "states, compiled Dataset/Model bindings, and gate-specific rejection."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
