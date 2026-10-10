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
- [x] KFP lifecycle, artifacts, caching, retries, parameters, and quality-gate example with compile CI
- [x] Model evaluation gate and promotion-control concepts covered in the KFP guide/sample
- [ ] Secrets, workload identity, and least-privilege RBAC labs
- [ ] Observability: logs, metrics, traces, and pipeline signals
- [ ] Reproducibility, lineage, and experiment tracking
- [ ] Cost controls and GPU scheduling
- [ ] Tested lab matrix for specific Kubernetes/Kubeflow versions

## Quality engineering progress

- [x] Expand the core Kubernetes resource, Kubeflow architecture, KFP components, Profile/isolation, debugging, and production-readiness guides into beginner-friendly Hinglish.
- [x] Add a GitHub Actions workflow for local Markdown links, fenced-block closure, and YAML syntax checks.
- [x] Add a guided ResourceQuota and LimitRange lab with preflight checks, expected outcomes, troubleshooting, and cleanup.
- [x] Add a lightweight Kubernetes Job manifest and explain workload/configuration object choices.
- [x] Add container image guidance, a non-root sample image, and a CI smoke test.
- [x] Add a synthetic KFP artifact-to-quality-gate pipeline and compile it in CI.
- [x] Extend repository checks to syntax-check Python files.
- [ ] Run the lab on explicitly documented Kubernetes versions and record results; this has **not** been completed by the static CI checks.

## Quality bar
Each guide should explain assumptions, link official sources, label risky commands, distinguish version-dependent behavior, and include verification steps. YAML should be syntax-checked and tested against a target cluster before being described as tested.