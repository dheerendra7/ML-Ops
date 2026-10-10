#!/usr/bin/env python3
"""Fast, backend-free regression tests for remote KFP result assertions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from test_kfp_backend import (  # noqa: E402
    normalise_state,
    verify_rejected_run,
    verify_successful_run,
)


def task(
    name: str,
    state: str,
    *,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "display_name": name,
        "state": state,
        "inputs": inputs or {},
        "outputs": outputs or {},
    }


def valid_run(gate_state: str = "SUCCEEDED") -> dict[str, Any]:
    dataset_artifact = {"artifact_ids": ["dataset-artifact-id"]}
    model_artifact = {"artifact_ids": ["model-artifact-id"]}
    return {
        "run_details": {
            "task_details": [
                task(
                    "create-toy-dataset",
                    "SUCCEEDED",
                    outputs={"dataset": dataset_artifact},
                ),
                task(
                    "train-toy-model",
                    "SUCCEEDED",
                    inputs={"dataset": dataset_artifact},
                    outputs={"model": model_artifact},
                ),
                task(
                    "evaluate-toy-model",
                    "SUCCEEDED",
                    inputs={"model": model_artifact},
                ),
                task("enforce-quality-gate", gate_state),
            ]
        }
    }


class KfpBackendContractTests(unittest.TestCase):
    def test_success_path_requires_tasks_and_artifact_references(self) -> None:
        verify_successful_run(valid_run("SUCCEEDED"))

    def test_rejection_path_requires_gate_itself_to_fail(self) -> None:
        verify_rejected_run(valid_run("FAILED"))

    def test_unrelated_upstream_failure_is_not_accepted_as_gate_rejection(self) -> None:
        run = valid_run("FAILED")
        run["run_details"]["task_details"][1]["state"] = "FAILED"
        with self.assertRaisesRegex(AssertionError, "train-toy-model"):
            verify_rejected_run(run)

    def test_missing_artifact_reference_is_rejected(self) -> None:
        run = valid_run("SUCCEEDED")
        run["run_details"]["task_details"][1]["outputs"]["model"]["artifact_ids"] = []
        with self.assertRaisesRegex(AssertionError, "model"):
            verify_successful_run(run)

    def test_missing_task_details_fail_closed(self) -> None:
        with self.assertRaisesRegex(AssertionError, "task_details"):
            verify_successful_run({"run_details": {"task_details": []}})

    def test_runtime_state_prefix_is_normalised(self) -> None:
        self.assertEqual(normalise_state("RUNTIME_STATE_SUCCEEDED"), "succeeded")
        self.assertEqual(normalise_state("FAILED"), "failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
