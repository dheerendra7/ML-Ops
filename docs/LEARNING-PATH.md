# Learning Path: Kubernetes to MLOps

Use one session per topic. Read the snapshot, explain the concept without looking, run examples only in an environment you control, then test yourself with revision questions.

## Stage 1 — Foundations
Learn containers, Pods, Jobs, Deployments, namespaces, requests and limits. Read [workload basics](kubernetes-foundations/workloads-and-configuration.md) and [resource controls](kubernetes-foundations/resource-controls.md).
**You should be able to:** explain Pending Pods, memory OOM termination, and why quotas differ from per-container limits.

## Stage 2 — Kubeflow mental model
Read [architecture](kubeflow/architecture.md). A platform installation may not enable every component.
**You should be able to:** describe pipeline authoring, submission, execution, and observation at a high level.

## Stage 3 — Pipeline components
Read [KFP component types](kubeflow/kfp-component-types.md), then [KFP run lifecycle, artifacts, caching, retries, and quality gates](kubeflow/pipeline-lifecycle-artifacts-caching-retries.md). Also study [container image security and reproducibility](containers/image-security-and-reproducibility.md).
**You should be able to:** choose a component type, explain artifact hand-off, judge when caching/retries are safe, and explain how a quality gate blocks promotion.

## Stage 4 — Multi-user and resource isolation
Read [Profiles and namespaces](kubeflow/profiles-namespaces-isolation.md), then complete [Lab 01 — resource governance](labs/resource-governance.md), [Lab 02 — least-privilege RBAC](security/least-privilege-rbac-lab.md), and [Lab 03 — secrets and rotation](security/secrets-and-rotation-lab.md) in a disposable cluster. Then run [Lab 04 — Vault + External Secrets Operator](security/external-secrets-vault-lab.md) to practice provider-backed sync, scoped read permissions, and rotation using synthetic data only.
**You should be able to:** distinguish aggregate quota, per-object constraints, RBAC, workload identity, and the difference between a provider-side secret source and a Kubernetes Secret synchronized for a workload.

## Stage 5 — Operate and debug
Use the [debugging checklist](troubleshooting/debugging-checklist.md), [production-readiness checklist](production/readiness-checklist.md), [model evaluation/promotion guide](production/model-evaluation-and-promotion.md), and [observability guide](production/observability-for-ml-pipelines.md). Review the [container image security guide](containers/image-security-and-reproducibility.md), [reproducibility/lineage guide](production/reproducibility-and-lineage.md), and [cost/GPU scheduling guide](production/cost-controls-and-gpu-scheduling.md) before publishing runtimes. Start with evidence, not random changes.

## Stage 6 — Recall and interview
Use [revision cards](interview/revision-cards.md). Answer aloud, then verify against the topic guide and official references.

Before calling a lab tested, check the [lab validation matrix](testing/lab-validation-matrix.md) and confirm the latest commit's relevant CI jobs are green.

## Completion criteria
Explain the concept, review or run the example, identify two failure modes, and state what must be checked for your installed version.