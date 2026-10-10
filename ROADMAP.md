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
- [x] Model evaluation gates and promotion strategies guide, linked to the synthetic KFP gate example
- [x] Namespace-scoped least-privilege RBAC verification lab
- [x] Kubernetes Secret handling and safe rotation lab (synthetic values only)
- [ ] Provider-specific external secret manager integration lab (requires a chosen provider and matching test environment)
- [x] Observability: logs, metrics, traces, alerts, and ML/data pipeline signals guide
- [x] Reproducibility, lineage, and experiment tracking guide plus illustrative run-record template
- [x] Cost controls and GPU scheduling guide plus explicitly non-runnable GPU Job template
- [ ] Tested lab matrix for specific Kubernetes/Kubeflow versions

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
- [x] Extend repository checks to syntax-check Python files.
- [ ] Run the lab on explicitly documented Kubernetes versions and record results; this has **not** been completed by the static CI checks.

## Quality bar
Each guide should explain assumptions, link official sources, label risky commands, distinguish version-dependent behavior, and include verification steps. YAML should be syntax-checked and tested against a target cluster before being described as tested.