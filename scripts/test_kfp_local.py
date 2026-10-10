#!/usr/bin/env python3
"""Exercise the real KFP pipeline locally, including artifact hand-off and rejection."""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from kfp import local

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.kfp.pipeline_artifacts_caching import (  # noqa: E402
    artifact_and_quality_gate_pipeline,
    enforce_quality_gate,
    evaluate_toy_model,
    train_toy_model,
)

APPROVAL = "approved-for-teaching-example-only"


def expect_value_error(function: Callable[[], object], description: str) -> None:
    try:
        function()
    except ValueError:
        print(f"PASS: {description}")
        return
    raise AssertionError(f"Expected ValueError: {description}")


def check_gate_boundaries() -> int:
    checks = 0

    expect = enforce_quality_gate.python_func
    assert expect(score=1.0, minimum_score=1.0) == APPROVAL
    checks += 1
    print("PASS: score exactly at threshold is accepted")

    assert expect(score=0.8, minimum_score=0.8) == APPROVAL
    checks += 1
    print("PASS: equality at the configured threshold is accepted")

    expect_value_error(
        lambda: expect(score=0.5, minimum_score=0.8),
        "below-threshold score is rejected",
    )
    checks += 1

    for invalid_score in (-0.01, 1.01, math.nan, math.inf, -math.inf):
        expect_value_error(
            lambda value=invalid_score: expect(score=value, minimum_score=0.8),
            f"invalid score {invalid_score!r} is rejected",
        )
        checks += 1

    for invalid_threshold in (-0.01, 1.01, math.nan, math.inf, -math.inf):
        expect_value_error(
            lambda value=invalid_threshold: expect(score=0.9, minimum_score=value),
            f"invalid threshold {invalid_threshold!r} is rejected",
        )
        checks += 1

    return checks


def call_train_component(rows: Any, offset: float = 0.0) -> dict[str, Any]:
    """Call the component's Python function against a temporary Dataset artifact."""
    with tempfile.TemporaryDirectory(prefix="mlops-dataset-contract-") as temp_dir:
        dataset_path = Path(temp_dir) / "dataset.json"
        model_path = Path(temp_dir) / "model.json"
        dataset_path.write_text(json.dumps(rows, allow_nan=True), encoding="utf-8")
        output_model = SimpleNamespace(path=str(model_path), metadata={})
        train_toy_model.python_func(
            dataset=SimpleNamespace(path=str(dataset_path)),
            model=output_model,
            offset=offset,
        )
        return json.loads(model_path.read_text(encoding="utf-8"))


def call_evaluation_component(model_payload: Any) -> float:
    """Call the evaluator's Python function against a temporary Model artifact."""
    with tempfile.TemporaryDirectory(prefix="mlops-model-contract-") as temp_dir:
        model_path = Path(temp_dir) / "model.json"
        model_path.write_text(json.dumps(model_payload, allow_nan=True), encoding="utf-8")
        return evaluate_toy_model.python_func(model=SimpleNamespace(path=str(model_path)))


def check_component_artifact_contracts() -> int:
    checks = 0
    valid_rows = [
        {"x": 0.0, "y": 1.0},
        {"x": 1.0, "y": 2.0},
        {"x": 2.0, "y": 3.0},
    ]
    model = call_train_component(valid_rows)
    assert model["model_type"] == "synthetic-mean-baseline"
    assert model["mean_prediction"] == 2.0
    assert model["training_rows"] == 3
    checks += 1
    print("PASS: training reads a valid Dataset and writes a well-formed Model")

    invalid_datasets = (
        ([], "empty Dataset artifact is rejected"),
        ({ "x": 1.0, "y": 2.0 }, "non-list Dataset artifact is rejected"),
        ([{"y": 1.0}], "Dataset row missing x is rejected"),
        ([{"x": "not-numeric", "y": 1.0}], "non-numeric Dataset values are rejected"),
        ([{"x": math.nan, "y": 1.0}], "non-finite Dataset values are rejected"),
    )
    for rows, description in invalid_datasets:
        expect_value_error(lambda value=rows: call_train_component(value), description)
        checks += 1

    score = call_evaluation_component(
        {
            "model_type": "synthetic-mean-baseline",
            "mean_prediction": 2.0,
            "training_rows": 3,
        }
    )
    assert score == 1.0
    checks += 1
    print("PASS: evaluation reads a valid Model and returns the expected teaching score")

    invalid_models = (
        ([], "non-object Model artifact is rejected"),
        (
            {"model_type": "unexpected", "mean_prediction": 2.0, "training_rows": 3},
            "unexpected model type is rejected",
        ),
        (
            {"model_type": "synthetic-mean-baseline", "mean_prediction": 2.0, "training_rows": 0},
            "Model with no training rows is rejected",
        ),
        (
            {"model_type": "synthetic-mean-baseline", "mean_prediction": "bad", "training_rows": 3},
            "non-numeric model prediction is rejected",
        ),
        (
            {"model_type": "synthetic-mean-baseline", "mean_prediction": math.inf, "training_rows": 3},
            "non-finite model prediction is rejected",
        ),
    )
    for payload, description in invalid_models:
        expect_value_error(
            lambda value=payload: call_evaluation_component(value),
            description,
        )
        checks += 1
    return checks


def check_local_pipeline() -> int:
    # DockerRunner intentionally executes the same containerized component type
    # described in the guide. The local run is not a remote KFP backend test.
    with tempfile.TemporaryDirectory(prefix="mlops-kfp-local-") as pipeline_root:
        # Keep the KFP workspace inside our own temporary root rather than
        # letting KFP create an implicit top-level /tmp workspace. This makes
        # the path lifecycle explicit and lets the outer TemporaryDirectory
        # clean up any remaining files even after an intentionally failed task.
        workspace_root = str(Path(pipeline_root) / "workspace")
        Path(workspace_root).mkdir()

        # Run task containers as the current runner user so files written to
        # mounted temporary paths remain removable by the host process.
        docker_runner_args = {"environment": {"HOME": "/tmp"}}
        if hasattr(os, "getuid") and hasattr(os, "getgid"):
            docker_runner_args["user"] = f"{os.getuid()}:{os.getgid()}"

        local.init(
            runner=local.DockerRunner(**docker_runner_args),
            pipeline_root=pipeline_root,
            workspace_root=workspace_root,
            raise_on_error=True,
            enable_caching=False,
        )

        successful_run = artifact_and_quality_gate_pipeline(
            offset=0.0,
            minimum_score=0.8,
        )
        actual = successful_run.output
        if actual != APPROVAL:
            raise AssertionError(
                f"Expected approval marker {APPROVAL!r}, got {actual!r}"
            )
        print("PASS: local pipeline transfers artifacts and returns the passing gate result")

        try:
            artifact_and_quality_gate_pipeline(
                offset=1.0,
                minimum_score=0.8,
            )
        except RuntimeError as exc:
            # Do not accept an arbitrary Docker/network/runtime error as a good
            # negative test: the pipeline's failing inner task must be the gate.
            detail = str(exc).lower().replace("_", "-")
            if "inner task failed" not in detail or "enforce-quality-gate" not in detail:
                raise AssertionError(
                    "The negative pipeline run failed for an unexpected reason: "
                    f"{exc}"
                ) from exc
            print("PASS: local pipeline fails at the quality-gate task for a rejected candidate")
        else:
            raise AssertionError("Expected the below-threshold pipeline run to fail")
    return 2


def main() -> int:
    gate_checks = check_gate_boundaries()
    artifact_checks = check_component_artifact_contracts()
    pipeline_checks = check_local_pipeline()
    print(
        "KFP local regression tests passed: "
        f"{gate_checks} gate-boundary checks, {artifact_checks} artifact-contract "
        f"checks and {pipeline_checks} pipeline checks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
