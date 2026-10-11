"""Toy KFP v2 pipeline demonstrating artifacts and a quality gate.

This uses synthetic values. It is a teaching example, not a real ML model.
Compile with the pinned SDK in this directory's requirements.txt.
"""

import argparse
from pathlib import Path

from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Model, Output


@dsl.component(base_image="python:3.12-slim")
def create_toy_dataset(dataset: Output[Dataset]) -> None:
    """Write a tiny synthetic dataset as a declared output artifact."""
    import json

    rows = [
        {"x": 0.0, "y": 1.0},
        {"x": 1.0, "y": 2.0},
        {"x": 2.0, "y": 3.0},
    ]
    with open(dataset.path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle)
    dataset.metadata["row_count"] = len(rows)
    dataset.metadata["purpose"] = "synthetic-teaching-data"


@dsl.component(base_image="python:3.12-slim")
def train_toy_model(
    dataset: Input[Dataset],
    model: Output[Model],
    offset: float,
) -> None:
    """Read and validate a Dataset artifact, then write a tiny baseline Model."""
    import json
    import math

    with open(dataset.path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Training dataset must be a non-empty JSON list")
    if (
        isinstance(offset, bool)
        or not isinstance(offset, (int, float))
        or not math.isfinite(offset)
    ):
        raise ValueError("Training offset must be a finite number")

    targets = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or "x" not in row or "y" not in row:
            raise ValueError(f"Dataset row {index} must contain numeric x and y fields")
        try:
            x_value = float(row["x"])
            y_value = float(row["y"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Dataset row {index} has non-numeric x/y values") from exc
        if not math.isfinite(x_value) or not math.isfinite(y_value):
            raise ValueError(f"Dataset row {index} has non-finite x/y values")
        targets.append(y_value)

    mean_y = sum(targets) / len(targets)
    toy_model = {
        "model_type": "synthetic-mean-baseline",
        "mean_prediction": mean_y + offset,
        "training_rows": len(rows),
    }
    with open(model.path, "w", encoding="utf-8") as handle:
        json.dump(toy_model, handle)

    model.metadata["model_type"] = toy_model["model_type"]
    model.metadata["training_rows"] = len(rows)


@dsl.component(base_image="python:3.12-slim")
def evaluate_toy_model(model: Input[Model]) -> float:
    """Read and validate a Model artifact, then return an illustrative score."""
    import json
    import math

    with open(model.path, "r", encoding="utf-8") as handle:
        toy_model = json.load(handle)
    if not isinstance(toy_model, dict):
        raise ValueError("Model artifact must contain a JSON object")
    if toy_model.get("model_type") != "synthetic-mean-baseline":
        raise ValueError("Model artifact has an unexpected model_type")

    training_rows = toy_model.get("training_rows")
    if (
        not isinstance(training_rows, int)
        or isinstance(training_rows, bool)
        or training_rows < 1
    ):
        raise ValueError("Model artifact must record a positive training_rows count")
    try:
        prediction = float(toy_model["mean_prediction"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Model artifact must contain a numeric mean_prediction") from exc
    if not math.isfinite(prediction):
        raise ValueError("Model artifact mean_prediction must be finite")

    # The known synthetic dataset has mean y = 2.0. This is an illustrative
    # teaching score, not a statistically meaningful production metric.
    absolute_error = abs(prediction - 2.0)
    return 1.0 / (1.0 + absolute_error)


@dsl.component(base_image="python:3.12-slim")
def enforce_quality_gate(score: float, minimum_score: float) -> str:
    """Fail closed for invalid scores/thresholds or an unmet quality criterion."""
    import math

    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0.0 <= score <= 1.0
    ):
        raise ValueError(f"Score must be a finite number in [0, 1], got {score!r}")
    if (
        isinstance(minimum_score, bool)
        or not isinstance(minimum_score, (int, float))
        or not math.isfinite(minimum_score)
        or not 0.0 <= minimum_score <= 1.0
    ):
        raise ValueError(
            "Minimum score must be a finite number in [0, 1], "
            f"got {minimum_score!r}"
        )
    if score < minimum_score:
        raise ValueError(
            f"Quality gate rejected output: score={score:.3f}, "
            f"required={minimum_score:.3f}"
        )
    return "approved-for-teaching-example-only"


@dsl.pipeline(
    name="artifact-and-quality-gate-demo",
    description=(
        "Synthetic KFP v2 example showing Dataset/Model artifact hand-off "
        "and a failing evaluation gate."
    ),
)
def artifact_and_quality_gate_pipeline(
    offset: float = 0.0,
    minimum_score: float = 0.8,
) -> str:
    dataset_task = create_toy_dataset()
    train_task = train_toy_model(
        dataset=dataset_task.outputs["dataset"],
        offset=offset,
    )
    score_task = evaluate_toy_model(model=train_task.outputs["model"])
    gate_task = enforce_quality_gate(
        score=score_task.output,
        minimum_score=minimum_score,
    )
    return gate_task.output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile the synthetic KFP pipeline without submitting a run."
    )
    parser.add_argument(
        "--output",
        default="pipeline.yaml",
        help="Destination for the compiled pipeline package.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    compiler.Compiler().compile(
        pipeline_func=artifact_and_quality_gate_pipeline,
        package_path=str(output_path),
    )
    print(f"Compiled KFP pipeline to {output_path}")


if __name__ == "__main__":
    main()
