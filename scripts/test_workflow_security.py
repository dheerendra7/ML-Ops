#!/usr/bin/env python3
"""Fail closed when workflow dependencies use mutable action references."""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: install PyYAML before checking workflow actions.", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
FULL_SHA_REF = re.compile(r"^.+@[0-9a-f]{40}$")


def is_local_reference(reference: str) -> bool:
    """Local actions/workflows resolve from the same checked-out revision."""
    return reference.startswith("./")


def is_pinned_reference(reference: str) -> bool:
    """Return whether a non-local action/workflow ref uses a full lowercase SHA."""
    return bool(FULL_SHA_REF.fullmatch(reference))


def validate_reference(reference: object, location: str, failures: list[str]) -> int:
    """Validate an action or reusable-workflow reference; return refs inspected."""
    if not isinstance(reference, str) or not reference.strip():
        failures.append(f"{location}: reference must be a non-empty string.")
        return 0
    if is_local_reference(reference):
        return 0
    if not is_pinned_reference(reference):
        failures.append(
            f"{location}: {reference!r} is not pinned to a full "
            "40-character lowercase commit SHA."
        )
    return 1


def main() -> int:
    failures: list[str] = []
    checked_refs = 0
    workflow_paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not workflow_paths:
        failures.append("No GitHub Actions workflow files were found.")

    for path in workflow_paths:
        label = path.relative_to(ROOT).as_posix()
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            failures.append(f"{label}: unable to parse workflow YAML: {exc}")
            continue

        if not isinstance(data, dict):
            failures.append(f"{label}: workflow root must be a YAML mapping.")
            continue
        jobs = data.get("jobs")
        if not isinstance(jobs, dict):
            failures.append(f"{label}: workflow must define a jobs mapping.")
            continue

        # Reusable workflows may be referenced at job level as well as
        # actions referenced in individual steps. Enforce the same immutable
        # ref policy for both forms.
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                failures.append(f"{label}: job {job_name!r} must be a mapping.")
                continue
            if "uses" in job:
                checked_refs += validate_reference(
                    job["uses"], f"{label}: reusable workflow job {job_name!r}", failures
                )
            steps = job.get("steps", [])
            if not isinstance(steps, list):
                failures.append(f"{label}: job {job_name!r} steps must be a list.")
                continue
            for index, step in enumerate(steps, start=1):
                if not isinstance(step, dict) or "uses" not in step:
                    continue
                checked_refs += validate_reference(
                    step["uses"], f"{label}: job {job_name!r}, step {index}", failures
                )

    if checked_refs == 0:
        failures.append("No external action references were inspected; verify the workflow scan.")

    if failures:
        print("GitHub Actions supply-chain validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(
        f"GitHub Actions supply-chain validation passed: "
        f"{checked_refs} external action references checked; all use full commit SHAs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
