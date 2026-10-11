# Roadmap

This roadmap describes learning-content priorities, not promised release dates.

## Initial foundation
- [x] Handbook entry point and learning path
- [x] Kubernetes resource controls
- [x] Kubeflow architecture overview
- [x] KFP component type comparison
- [x] Profiles, namespaces, and isolation overview
- [x] Troubleshooting and production-readiness checklists
- [x] Interview revision cards and glossary

## Next content milestones
- [x] Kubernetes workload basics: Pod, Job, Deployment, Service, ConfigMap, Secret
- [x] Container image build, scanning, and digest pinning guide plus a non-root smoke-test image
- [x] KFP lifecycle, artifacts, caching, retries, parameters, and quality-gate example with compile and DockerRunner local-runtime CI
- [x] Model evaluation gates and promotion strategies guide, linked to the synthetic KFP gate example
- [x] Namespace-scoped least-privilege RBAC verification lab
- [x] Kubernetes Secret handling and safe rotation lab (synthetic values only)
- [x] Add and verify the provider-specific HashiCorp Vault + External Secrets Operator lab on pinned chart versions; [run #38078803152](https://github.com/dheerendra7/ML-Ops/actions/runs/38078803152) passed scoped Vault access, Kubernetes Secret sync, non-root consumer mount, and mounted-file rotation with synthetic values. Production Vault identity/TLS/HA remains outside this lab.
- [x] Observability: logs, metrics, traces, alerts, and ML/data pipeline signals guide
- [x] Reproducibility, lineage, and experiment tracking guide plus illustrative run-record template
- [x] Cost controls and GPU scheduling guide plus explicitly non-runnable GPU Job template
- [x] Core Kubernetes integration labs executed in disposable Kind clusters for v1.34.3 and v1.35.0 via CI; see the [validation matrix](docs/testing/lab-validation-matrix.md) for run evidence
- [ ] Validate a full Kubeflow/community distribution and GPU hardware; verify production Vault Kubernetes auth/TLS/HA and additional cloud-provider secret-manager integrations in named target environments. The local KFP backend and Vault/ESO dev-mode workflows have passed their scoped integration tests.

## Quality engineering progress

- [x] Expand the core Kubernetes resource, Kubeflow architecture, KFP components, Profile/isolation, debugging, and production-readiness guides into beginner-friendly Hinglish.
- [x] Add a GitHub Actions workflow for local Markdown links, fenced-block closure, YAML syntax, Python source syntax, pinned KFP compilation, and container smoke testing.
- [x] Add a guided ResourceQuota and LimitRange lab with preflight checks, expected outcomes, troubleshooting, and cleanup.
- [x] Add a lightweight Kubernetes Job manifest and explain workload/configuration object choices.
- [x] Add container image guidance, a non-root sample image, and a CI smoke test.
- [x] Add an evidence-focused model evaluation and staged-promotion guide.
- [x] Add a namespace-scoped RBAC lab that tests both expected allow and deny outcomes.
- [x] Add a Secret handling/rotation lab that uses only synthetic values and documents external-provider prerequisites.
- [x] Add an actionable observability guide covering logs, metrics, traces, alert design and model/data signals.
- [x] Add a lineage/run-record template and practical cost/GPU scheduling guidance with cluster-specific caveats.
- [x] Add a synthetic KFP artifact-to-quality-gate pipeline and compile it in CI.
- [x] Run the synthetic KFP pipeline through KFP DockerRunner in CI; verify artifact hand-off, successful output, expected gate rejection, and 17 score/threshold type and boundary cases, malformed Dataset row checks, and invalid training-offset checks.
- [x] Extend repository checks to syntax-check Python files.
- [x] Pin external GitHub Actions to verified full commit SHAs and add a CI regression check plus a maintenance guide.
- [x] Add a dedicated disposable Kind workflow that installs standalone KFP and submits real API-based success/rejection runs; the latest backend verification passed in [run #38120495578](https://github.com/dheerendra7/ML-Ops/actions/runs/38120495578), confirming successful expected tasks and rejection specifically at the quality gate. The earlier task-state/artifact-binding revision passed in [run #38077683009](https://github.com/dheerendra7/ML-Ops/actions/runs/38077683009), and workflow concurrency hardening passed in [run #38078560808](https://github.com/dheerendra7/ML-Ops/actions/runs/38078560808).
- [x] Add fast KFP backend-contract regression tests for repeated internal executor nodes, required pipeline-task states, and compiled Dataset/Model artifact bindings; the regression CI passed in [run #38077670702](https://github.com/dheerendra7/ML-Ops/actions/runs/38077670702).
- [x] Verify the revised standalone KFP backend smoke test with compiled-binding checks, consumer-side artifact validation and gate-specific rejection; passed in [run #38120495578](https://github.com/dheerendra7/ML-Ops/actions/runs/38120495578) for standalone KFP 2.17.0 + Kind v1.34.3.
- [x] Add semantic regression assertions for RBAC, GPU, lineage, resource-policy, and container examples.
- [x] Add live disposable-Kubernetes integration checks for ResourceQuota, LimitRange defaults, Job completion, RBAC allow/deny, and synthetic Secret rotation on two pinned Kubernetes versions.
- [x] Document the environment-dependent validation boundaries in the README and lab matrix: full Kubeflow/community distribution, real GPU hardware, production Vault Kubernetes authentication/TLS/HA, and additional cloud secret-provider integrations remain unverified.

## Quality bar
Each guide should explain assumptions, link official sources, label risky commands, distinguish version-dependent behavior, and include verification steps. YAML should be syntax-checked and tested against a target cluster before being described as tested.