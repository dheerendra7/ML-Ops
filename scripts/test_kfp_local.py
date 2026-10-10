#!/usr/bin/env python3
"""Exercise the real KFP pipeline locally, including artifact hand-off and rejection."""

from __future__ import annotations

import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable

from kfp import local

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.kfp.pipeline_artifacts_caching import (  # noqa: E402
    artifact_and_quality_gate_pipeline,
    enforce_quality_gate,
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


def check_local_pipeline() -> int:
    # DockerRunner intentionally executes the same containerized component type
    # described in the guide. The local run is not a remote KFP backend test.
    with tempfile.TemporaryDirectory(prefix="mlops-kfp-local-") as pipeline_root:
        # Run task containers as the current runner user so files written to
        # mounted temporary paths remain removable by the host process.
        docker_runner_args = {"environment": {"HOME": "/tmp"}}
        if hasattr(os, "getuid") and hasattr(os, "getgid"):
            docker_runner_args["user"] = f"{os.getuid()}:{os.getgid()}"

        local.init(
            runner=local.DockerRunner(**docker_runner_args),
            pipeline_root=pipeline_root,
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
    pipeline_checks = check_local_pipeline()
    print(
        "KFP local regression tests passed: "
        f"{gate_checks} gate-boundary checks and {pipeline_checks} pipeline checks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
