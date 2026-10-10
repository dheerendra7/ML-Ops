# Learning Path: Kubernetes to MLOps

Use one session per topic. Read the snapshot, explain the concept without looking, run examples only in an environment you control, then test yourself with revision questions.

## Stage 1 — Foundations
Learn containers, Pods, namespaces, requests and limits. Read [resource controls](kubernetes-foundations/resource-controls.md).
**You should be able to:** explain Pending Pods, memory OOM termination, and why quotas differ from per-container limits.

## Stage 2 — Kubeflow mental model
Read [architecture](kubeflow/architecture.md). A platform installation may not enable every component.
**You should be able to:** describe pipeline authoring, submission, execution, and observation at a high level.

## Stage 3 — Pipeline components
Read [KFP component types](kubeflow/kfp-component-types.md).
**You should be able to:** choose a component type and justify the dependency and runtime trade-offs.

## Stage 4 — Multi-user and resource isolation
Read [Profiles and namespaces](kubeflow/profiles-namespaces-isolation.md), then inspect the YAML examples. Then complete [Lab 01 — resource governance](labs/resource-governance.md) in a disposable cluster.
**You should be able to:** distinguish aggregate quota, per-object constraints, RBAC, and workload identity.

## Stage 5 — Operate and debug
Use the [debugging checklist](troubleshooting/debugging-checklist.md) and [production-readiness checklist](production/readiness-checklist.md). Start with evidence, not random changes.

## Stage 6 — Recall and interview
Use [revision cards](interview/revision-cards.md). Answer aloud, then verify against the topic guide and official references.

## Completion criteria
Explain the concept, review or run the example, identify two failure modes, and state what must be checked for your installed version.