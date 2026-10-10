# Kubeflow Architecture: A Mental Model

## 5-minute snapshot
Kubeflow is an ecosystem of components that help teams build and operate ML workflows on Kubernetes. It is not one universal binary with identical features everywhere. Installation choices, versions, and enabled components determine the actual platform.

## Mental model
- **Kubernetes** provides the underlying API, scheduling, workload execution, and resource controls.
- **Kubeflow components** add ML-oriented capabilities. A deployment may include pipeline orchestration, notebook experiences, training integrations, serving, or other components.
- **Your workflow** describes tasks and dependencies: prepare data, train, evaluate, then publish or register outputs.
- **Operations** include identity, permissions, resource budgets, storage, observability, upgrades, and ownership.

## Pipeline lifecycle at a high level
1. Author a pipeline using the supported SDK or interface.
2. Compile/package it in the format expected by the installed KFP version.
3. Submit it to the configured backend.
4. The backend coordinates task execution.
5. Inspect task states, logs, artifacts, and outputs; validate the model before promotion.

Exact APIs and deployment architecture vary across releases. Check the docs matching your installation.

## Boundaries
- Kubernetes runs workloads; it does not prove an ML result is statistically valid.
- A successful run does not prove model quality, data correctness, or safe deployment.
- A namespace is not a complete tenant-isolation mechanism.
- A platform needs storage, access control, resource governance, and operational ownership.

## Recall
1. What does Kubernetes provide that Kubeflow builds on?
2. Why can installations expose different features?
3. What evidence is needed before promoting a model?

## References
- https://www.kubeflow.org/docs/
- https://kubernetes.io/docs/concepts/