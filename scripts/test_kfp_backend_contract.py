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
    verify_artifact_wiring,
    verify_rejected_run,
    verify_successful_run,
)


def task(name: str, state: str) -> dict[str, Any]:
    return {"display_name": name, "state": state}


def valid_run(gate_state: str = "SUCCEEDED") -> dict[str, Any]:
    return {
        "run_details": {
            "task_details": [
                task("create-toy-dataset", "SUCCEEDED"),
                task("train-toy-model", "SUCCEEDED"),
                task("evaluate-toy-model", "SUCCEEDED"),
                task("enforce-quality-gate", gate_state),
                # Internal KFP implementation nodes can reuse display names.
                task("executor", "SUCCEEDED"),
                task("executor", "SUCCEEDED"),
            ]
        }
    }


def valid_pipeline_spec() -> dict[str, Any]:
    return {
        "root": {
            "dag": {
                "tasks": {
                    "create-toy-dataset": {},
                    "train-toy-model": {
                        "inputs": {
                            "artifacts": {
                                "dataset": {
                                    "taskOutputArtifact": {
                                        "producerTask": "create-toy-dataset",
                                        "outputArtifactKey": "dataset",
                                    }
                                }
                            }
                        }
                    },
                    "evaluate-toy-model": {
                        "inputs": {
                            "artifacts": {
                                "model": {
                                    "taskOutputArtifact": {
                                        "producerTask": "train-toy-model",
                                        "outputArtifactKey": "model",
                                    }
                                }
                            }
                        }
                    },
                    "enforce-quality-gate": {},
                }
            }
        }
    }


class KfpBackendContractTests(unittest.TestCase):
    def test_success_path_requires_expected_pipeline_tasks(self) -> None:
        verify_successful_run(valid_run("SUCCEEDED"))

    def test_rejection_path_requires_gate_itself_to_fail(self) -> None:
        verify_rejected_run(valid_run("FAILED"))

    def test_unrelated_upstream_failure_is_not_accepted_as_gate_rejection(self) -> None:
        run = valid_run("FAILED")
        run["run_details"]["task_details"][1]["state"] = "FAILED"
        with self.assertRaisesRegex(AssertionError, "train-toy-model"):
            verify_rejected_run(run)

    def test_missing_task_details_fail_closed(self) -> None:
        with self.assertRaisesRegex(AssertionError, "task_details"):
            verify_successful_run({"run_details": {"task_details": []}})

    def test_internal_executor_duplicates_do_not_look_like_pipeline_duplicates(self) -> None:
        verify_successful_run(valid_run("SUCCEEDED"))

    def test_duplicate_expected_pipeline_task_is_rejected(self) -> None:
        run = valid_run("SUCCEEDED")
        run["run_details"]["task_details"].append(
            task("enforce-quality-gate", "SUCCEEDED")
        )
        with self.assertRaisesRegex(AssertionError, "duplicate pipeline task"):
            verify_successful_run(run)

    def test_runtime_state_prefix_is_normalised(self) -> None:
        self.assertEqual(normalise_state("RUNTIME_STATE_SUCCEEDED"), "succeeded")
        self.assertEqual(normalise_state("FAILED"), "failed")

    def test_compiled_artifact_wiring_is_accepted(self) -> None:
        verify_artifact_wiring(valid_pipeline_spec())

    def test_wrong_dataset_producer_is_rejected(self) -> None:
        spec = valid_pipeline_spec()
        binding = spec["root"]["dag"]["tasks"]["train-toy-model"]["inputs"]["artifacts"]["dataset"]["taskOutputArtifact"]
        binding["producerTask"] = "some-other-task"
        with self.assertRaisesRegex(AssertionError, "train-toy-model.dataset"):
            verify_artifact_wiring(spec)

    def test_wrong_model_output_key_is_rejected(self) -> None:
        spec = valid_pipeline_spec()
        binding = spec["root"]["dag"]["tasks"]["evaluate-toy-model"]["inputs"]["artifacts"]["model"]["taskOutputArtifact"]
        binding["outputArtifactKey"] = "wrong-output"
        with self.assertRaisesRegex(AssertionError, "evaluate-toy-model.model"):
            verify_artifact_wiring(spec)

    def test_missing_artifact_binding_is_rejected(self) -> None:
        spec = valid_pipeline_spec()
        del spec["root"]["dag"]["tasks"]["evaluate-toy-model"]["inputs"]["artifacts"]["model"]
        with self.assertRaisesRegex(AssertionError, "evaluate-toy-model.model"):
            verify_artifact_wiring(spec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
