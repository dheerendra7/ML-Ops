#!/usr/bin/env python3
"""Unit and scanner-level tests for the GitHub Actions immutable-ref policy."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import sys
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import test_workflow_security as policy  # noqa: E402
from test_workflow_security import (  # noqa: E402
    is_local_reference,
    is_pinned_reference,
)


class WorkflowSecurityPolicyTests(unittest.TestCase):
    def test_full_lowercase_commit_sha_is_accepted(self) -> None:
        self.assertTrue(is_pinned_reference("actions/checkout@" + "a" * 40))

    def test_version_tag_is_not_immutable(self) -> None:
        self.assertFalse(is_pinned_reference("actions/checkout@v7"))

    def test_branch_reference_is_not_immutable(self) -> None:
        self.assertFalse(is_pinned_reference("org/action@main"))

    def test_short_sha_is_rejected(self) -> None:
        self.assertFalse(is_pinned_reference("actions/checkout@" + "a" * 39))

    def test_uppercase_hex_is_rejected_by_repository_convention(self) -> None:
        self.assertFalse(is_pinned_reference("actions/checkout@" + "A" * 40))

    def test_local_action_reference_is_identified_as_local(self) -> None:
        self.assertTrue(is_local_reference("./.github/actions/local-action"))

    def test_external_action_is_not_treated_as_local(self) -> None:
        self.assertFalse(is_local_reference("actions/checkout@" + "a" * 40))

    def run_checker_on_fixture(self, content: str) -> tuple[int, str]:
        with TemporaryDirectory(prefix="workflow-pin-fixture-") as temp_dir:
            root = Path(temp_dir)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "fixture.yml").write_text(content, encoding="utf-8")
            output = StringIO()
            with (
                patch.object(policy, "ROOT", root),
                patch.object(policy, "WORKFLOWS", workflows),
                redirect_stdout(output),
            ):
                result = policy.main()
            return result, output.getvalue()

    def test_scanner_rejects_mutable_step_action(self) -> None:
        result, output = self.run_checker_on_fixture(
            """
name: fixture
on:
  workflow_dispatch:
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
"""
        )
        self.assertEqual(result, 1)
        self.assertIn("actions/checkout@v7", output)
        self.assertIn("step 1", output)

    def test_scanner_rejects_mutable_reusable_workflow(self) -> None:
        result, output = self.run_checker_on_fixture(
            """
name: fixture
on:
  workflow_dispatch:
jobs:
  call:
    uses: org/repo/.github/workflows/ci.yml@main
"""
        )
        self.assertEqual(result, 1)
        self.assertIn("reusable workflow job 'call'", output)
        self.assertIn("ci.yml@main", output)

    def test_scanner_accepts_pinned_reusable_workflow(self) -> None:
        result, output = self.run_checker_on_fixture(
            """
name: fixture
on:
  workflow_dispatch:
jobs:
  call:
    uses: org/repo/.github/workflows/ci.yml@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
"""
        )
        self.assertEqual(result, 0)
        self.assertIn("1 external action references checked", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
