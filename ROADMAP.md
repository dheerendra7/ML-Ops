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
- [ ] Kubernetes workload basics: Pod, Job, Deployment, Service, ConfigMap, Secret
- [ ] Container image build, scanning, and digest pinning
- [ ] KFP lifecycle, artifacts, caching, retries, and parameters
- [ ] Model evaluation gates and promotion strategies
- [ ] Secrets, workload identity, and least-privilege RBAC labs
- [ ] Observability: logs, metrics, traces, and pipeline signals
- [ ] Reproducibility, lineage, and experiment tracking
- [ ] Cost controls and GPU scheduling
- [ ] Tested lab matrix for specific Kubernetes/Kubeflow versions

## Quality bar
Each guide should explain assumptions, link official sources, label risky commands, distinguish version-dependent behavior, and include verification steps. YAML should be syntax-checked and tested against a target cluster before being described as tested.