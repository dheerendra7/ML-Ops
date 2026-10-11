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

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                failures.append(f"{label}: job {job_name!r} must be a mapping.")
                continue
            steps = job.get("steps", [])
            if not isinstance(steps, list):
                failures.append(f"{label}: job {job_name!r} steps must be a list.")
                continue
            for index, step in enumerate(steps, start=1):
                if not isinstance(step, dict) or "uses" not in step:
                    continue
                reference = step["uses"]
                location = f"{label}: job {job_name!r}, step {index}"
                if not isinstance(reference, str) or not reference.strip():
                    failures.append(f"{location}: action reference must be a non-empty string.")
                    continue
                # Local actions are part of the checked-out source tree and use
                # the same source revision as the workflow, so they do not use
                # an external owner/repository@ref expression.
                if reference.startswith("./"):
                    continue
                checked_refs += 1
                if not FULL_SHA_REF.fullmatch(reference):
                    failures.append(
                        f"{location}: {reference!r} is not pinned to a full "
                        "40-character lowercase commit SHA."
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
