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
    """Build a tiny baseline artifact so artifact hand-off is observable."""
    import json

    with open(dataset.path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not rows:
        raise ValueError("Training dataset must contain at least one row")

    mean_y = sum(float(row["y"]) for row in rows) / len(rows)
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
    """Return a synthetic score in [0, 1], not a statistical ML metric."""
    import json

    with open(model.path, "r", encoding="utf-8") as handle:
        toy_model = json.load(handle)

    prediction = float(toy_model["mean_prediction"])
    # The known synthetic dataset has mean y = 2.0.
    absolute_error = abs(prediction - 2.0)
    return 1.0 / (1.0 + absolute_error)


@dsl.component(base_image="python:3.12-slim")
def enforce_quality_gate(score: float, minimum_score: float) -> str:
    """Fail the pipeline if the illustrative acceptance score is too low."""
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Score must be in [0, 1], got {score}")
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
) -> None:
    dataset_task = create_toy_dataset()
    train_task = train_toy_model(
        dataset=dataset_task.outputs["dataset"],
        offset=offset,
    )
    score_task = evaluate_toy_model(model=train_task.outputs["model"])
    enforce_quality_gate(
        score=score_task.output,
        minimum_score=minimum_score,
    )


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
