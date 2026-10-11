#!/usr/bin/env python3
"""Unit tests for the GitHub Actions immutable-reference policy helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
