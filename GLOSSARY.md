# Glossary

- **Artifact:** File or object produced by a pipeline step, such as a model or metrics report.
- **Container image:** Packaged filesystem and metadata used to start containers.
- **Control plane:** Components that expose and reconcile desired cluster state.
- **DAG:** Directed acyclic graph; tasks connected by dependencies without cycles.
- **Image digest:** Content identifier for an image; more immutable than a mutable tag.
- **KFP:** Kubeflow Pipelines, a platform and SDK for defining and running ML workflows.
- **Kubernetes:** System for orchestrating containerized workloads.
- **LimitRange:** Namespaced policy for defaults and min/max resource constraints on individual objects.
- **MLOps:** Practices for reliably developing, deploying, observing, and maintaining ML systems.
- **Namespace:** Scope for namespaced Kubernetes objects and many policies; not a complete security boundary by itself.
- **Pod:** Smallest deployable Kubernetes unit, containing one or more co-located containers.
- **Profile:** Kubeflow custom resource commonly used in multi-user setups to represent a user/workspace; exact behavior varies by installation.
- **RBAC:** Role-based access control for Kubernetes API permissions.
- **Reconciliation:** Comparing observed state with desired state and taking action to converge them.
- **Resource request:** Resource amount used by Kubernetes scheduling decisions.
- **Resource limit:** Configured upper bound for supported container resources.
- **ResourceQuota:** Namespace-level policy limiting aggregate resource consumption or object counts.
- **Service account:** Kubernetes identity used by workloads or automation.
- **Workflow:** Dependency-driven series of tasks such as preparation, training, evaluation, and publishing.

See [SOURCES.md](SOURCES.md).