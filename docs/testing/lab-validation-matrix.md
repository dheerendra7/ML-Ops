# Lab Validation Matrix and Evidence

This page distinguishes static checks from runtime tests. A check is considered **verified only when the corresponding GitHub Actions job for the current repository commit is completed successfully**. Queued or in-progress jobs are not evidence of a pass.

## Latest code/test baseline CI verification

The documentation/examples workflow completed successfully for commit [f4c9803](https://github.com/dheerendra7/ML-Ops/commit/f4c980305d262434a4a18eaea1a312362682e43f) in [run #38121503667](https://github.com/dheerendra7/ML-Ops/actions/runs/38121503667). All five jobs passed: docs/example checks, 17 backend-contract tests, KFP compile/local runtime, container smoke, and Kubernetes integration on v1.34.3/v1.35.0. The run also scanned 13 external action references for full commit-SHA pins and passed 10 workflow-pin policy tests. Later changes still require their own validation.

## Automated repository checks

| Check | What is actually exercised | What it does not prove |
|---|---|---|
| Markdown validator | Relative local Markdown links and code-fence closure | External web URLs stay available or claims are technically correct |
| YAML validation | Checked-in YAML and YAML code fences parse | Kubernetes admission or controller behavior |
| Python syntax | Python source parses using the runner's Python version | Every function behaves correctly at runtime |
| GitHub Actions supply-chain policy | 13 external step-action references are pinned to full commit SHAs; 10 tests verify the scanner rejects mutable step-action and job-level reusable-workflow references | Does not audit action source code, nested dependencies, or prove the selected revision is benign |
| Example regression tests | ResourceQuota values, LimitRange type, RBAC least privilege, lineage placeholders, GPU template placeholder/resource, non-root Dockerfile and ignore rules | Security posture of a real cluster or all possible manifest edits |
| Container smoke test | Docker image builds, configured runtime user is non-root, app starts with a read-only root filesystem and reduced Linux capabilities | Production image scanning, remote registry publishing or Kubernetes deployment |
| KFP compile job | Sample pipeline compiles with KFP SDK 2.17.0 and generated package is parseable YAML | Submission to, or execution on, a live KFP backend |
| KFP backend-contract regression | 17 backend-free tests cover required task outcomes, missing/duplicate task handling, compiled Dataset/Model artifact bindings, and the real CLI rejecting invalid timeout/retry settings before compilation | Live API calls, backend startup, or pipeline execution; those are separately covered by the standalone KFP smoke workflow |
| KFP local runtime regression | DockerRunner executes the synthetic artifact-to-gate pipeline; passing output is checked, an intentionally rejected candidate fails at the gate task, 17 score/threshold type and boundary checks run, and malformed Dataset rows plus invalid training offsets are rejected | Remote KFP auth/API, production artifact store, backend caching/retry behavior, real training or production model quality |
| Standalone KFP backend smoke workflow | A disposable Kind/KFP 2.17.0 cluster runs positive and negative remote cases; compiled Dataset/Model bindings are asserted and consumer tasks parse/validate the artifact inputs | Latest recorded pass: commit `842b1d3`, [run #38120495578](https://github.com/dheerendra7/ML-Ops/actions/runs/38120495578), with successful expected tasks and rejection specifically at the quality gate. This remains a focused integration test, not full Kubeflow, production artifact-store, GPU or production-security certification |
| Vault + External Secrets Operator integration | A disposable Kind v1.34.3 cluster installs pinned Vault/ESO Helm charts, checks a scoped Vault read token, syncs KV v2 data to a Kubernetes Secret without printing the value, and verifies rotation | The workflow after GitHub Action SHA pinning passed in [run #38121235556](https://github.com/dheerendra7/ML-Ops/actions/runs/38121235556). It verifies scoped token access, sync, non-root read-only consumer mount, and mounted-file rotation without logging secret values; it does not prove production identity/TLS, durability, or cloud-provider integration |

Verified baseline: [GitHub Actions run #108](https://github.com/dheerendra7/ML-Ops/actions/runs/38067726046) completed successfully for commit `91ffb91a34b93c1c804c74e2897f62cd9e91cc9d`; all five jobs passed, including KFP compilation, container smoke testing, and Kubernetes lab integration on v1.34.3 and v1.35.0. The standalone backend smoke test separately passed on commit `cc49c5be7d50aaf2392a679f4d3febcace8734da` in [workflow run #5](https://github.com/dheerendra7/ML-Ops/actions/runs/38067527101), with both expected remote run outcomes confirmed in its logs. For later commits, open [the latest GitHub Actions runs](https://github.com/dheerendra7/ML-Ops/actions) and verify the exact commit and each required job.

## Disposable Kubernetes integration matrix

The workflow creates ephemeral Kind clusters using digest-pinned node images. It runs the core Kubernetes lab script without requiring access to a personal or production cluster.

| Kubernetes version | Node image reference | Scenario coverage |
|---|---|---|
| v1.34.3 | kindest/node v1.34.3, digest-pinned in the workflow | ResourceQuota/LimitRange admission and defaults; smoke Job; namespace-scoped RBAC allow/deny; synthetic Secret create/rotation |
| v1.35.0 | kindest/node v1.35.0, digest-pinned in the workflow | Same core scenarios on a second Kubernetes minor release |

The version matrix above describes the configured test targets. Check the linked Actions jobs for the actual pass/fail outcome of the current commit. The version printed by the test runner is the evidence for the cluster that actually started.

Core scenarios include:

- Server-side dry-run and apply of ResourceQuota and LimitRange.
- Two Pods admitted within a 500m CPU request quota, followed by a third Pod rejected for exceeding that quota.
- Verification of the LimitRange CPU/memory request and limit defaults on an admitted Pod.
- Completion of the sample Kubernetes Job and confirmation of its expected log message.
- Allowed and denied ServiceAccount API actions using Kubernetes authorization checks.
- Rotation of synthetic-only Secret data while keeping the value out of the logs.

The test harness deletes the dedicated namespaces when it exits. These clusters are disposable CI environments; they do not share state with user clusters.

## Explicitly not covered yet

- A full Kubeflow installation and multi-user Profile controller behavior.
- The latest completed remote KFP smoke test passed in [run #38120495578](https://github.com/dheerendra7/ML-Ops/actions/runs/38120495578) on the pipeline/script revision at commit `842b1d3`. The SHA-pinned action-ref integration run #38121235557 was triggered on commit `65da92d` and is still running at the time of this report; do not treat it as a pass until it completes. KFP 2.17.0 task-detail conversion does not reliably populate runtime artifact-ID fields for Argo-executed tasks, so the smoke test checks compiled producer/consumer bindings, successful consumer reads, task states and gate-specific rejection. Production artifact-store durability, a full Kubeflow/community distribution, and other backend configurations remain unverified. The local DockerRunner regression test and standalone smoke test have different scopes.
- Production Vault Kubernetes authentication/TLS, identity federation, upstream credential revocation, and additional external-secret providers remain unverified. The local Vault/ESO workflow uses dev mode and does not certify production configuration.
- GPU execution. The GPU manifest is a deliberately non-runnable template until an approved GPU-enabled image/digest and compatible GPU hardware/plugin are selected.
- Production cluster sizing, network policies, cloud IAM, persistence, cost controls and organizational policies.
- A full integration matrix across multiple supported Kubeflow releases and KFP backend configurations.

A successful Kind run is runtime evidence for the scenarios and Kubernetes versions listed above. The KFP local run is runtime evidence for the SDK's local runner path only. Neither is **proof** that a production cluster or a full Kubeflow deployment behaves identically.

## Re-running locally

Use a disposable local Kubernetes cluster compatible with Kind and review [Lab 01](../labs/resource-governance.md), [Lab 02](../security/least-privilege-rbac-lab.md), [Lab 03](../security/secrets-and-rotation-lab.md), and [Lab 04 — Vault/ESO](../security/external-secrets-vault-lab.md) first. The automated harness is [scripts/test_kind_labs.sh](../../scripts/test_kind_labs.sh). Do not run its namespace-deletion steps against a cluster with resources you need.

## Contribution rule for new lab coverage

When adding a tested version, record the exact version/node image, the scenarios executed, actual CI result/link, and known exclusions. Never mark a cluster scenario tested because its YAML parsed or its CI job was merely started.
