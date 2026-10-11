# GitHub Actions Supply-Chain Hardening

This repository pins third-party GitHub Actions to full commit SHAs and checks the policy in CI. It is a small but meaningful supply-chain control: a tag such as `@v7` is a convenient label, but the tag can be moved; a commit SHA identifies the exact action revision selected for the workflow.

GitHub's [secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use) identifies a full-length commit SHA as the immutable way to reference a released action. See also the [workflow syntax reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

## What this repository enforces

- Every external action and reusable-workflow reference in `.github/workflows/` ends with a full 40-character commit SHA.
- An inline version comment (for example, `# v7`) retains the upstream version label for reviewers and maintainers.
- The `scripts/test_workflow_security.py` check runs in the normal validation workflow; a new tag- or branch-pinned action fails CI.
- Workflow permissions remain explicitly scoped to `contents: read` unless a specific job needs otherwise.

Local actions referenced with `uses: ./path` are exempt because they are read from the checked-out source revision rather than resolved from an external action repository. This validator checks workflow references; it does not inspect every dependency used internally by an action.

## Safely updating an action

1. Locate the intended release/tag in the action's **original upstream repository**, not a fork.
2. Verify the tag resolves to the commit SHA you intend to trust; inspect release notes and review the action code and requested permissions.
3. Update the reference to the full 40-character SHA and retain the human-readable version in an inline comment.
4. Run `python scripts/test_workflow_security.py`, then run the relevant CI jobs. Do not treat SHA pinning as a substitute for dependency updates, action-source review, least privilege or secret hygiene.

Example form:

~~~yaml
- name: Check out repository
  uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
~~~

The SHA above is pinned to the verified upstream `actions/checkout` tag used when this guide was written. Check the upstream repository again when intentionally upgrading it.

## Boundaries

SHA pinning prevents a workflow from silently following a moved tag; it does not prove the chosen action revision is harmless, prevent vulnerabilities inside that revision, or pin that action's own transitive downloads. Keep permissions minimal, review upstream changes, refresh pins deliberately, and never print credentials or secret values in logs.
