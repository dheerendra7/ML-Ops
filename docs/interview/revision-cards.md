# Interview Revision Cards

Answer before checking the suggested points. Understanding matters more than memorizing exact wording.

## Kubernetes basics

**Q: Request vs limit?**
- Request is used in scheduling decisions.
- Limit is a runtime constraint for supported resources. CPU limits generally throttle; memory over limit can result in OOM termination.

**Q: ResourceQuota vs LimitRange?**
- ResourceQuota constrains aggregate usage or object counts in a namespace.
- LimitRange applies defaults and min/max constraints to individual objects.

**Q: Why can a Pod be Pending?**
Insufficient schedulable capacity, oversized requests, taints/tolerations, affinity, unbound volumes, quota, or admission issues. Inspect describe output and events first.

**Q: Is a namespace a full security boundary?**
No. Consider RBAC, service accounts, network controls, admission/runtime settings, storage permissions, and platform-specific isolation.

## Kubeflow / KFP

**Q: What is Kubeflow?**
An ecosystem of ML-oriented components built around Kubernetes. Features depend on release and deployment choices.

**Q: Lightweight Python vs container component?**
Lightweight Python is convenient for small Python tasks supported by the SDK packaging model. Container components provide explicit image/command control for custom runtimes and dependencies.

**Q: Does a successful pipeline prove model quality?**
No. It shows execution completed according to the pipeline's status semantics. Model quality requires suitable evaluation and promotion gates.

**Q: Why pin dependencies and images?**
To reduce surprise from mutable tags or dependency updates and improve reproducibility. A digest identifies image content more precisely than a mutable tag.

## Operations

**Q: How do you debug CrashLoopBackOff?**
Check describe output, current and previous logs, exit code, startup command, configuration, secrets, and probes.

**Q: How do you debug Forbidden?**
Identify the effective identity, exact API verb/resource/namespace, then inspect relevant role bindings.

**Q: What does production-ready mean for an ML pipeline?**
Reproducibility, evaluation gates, access control, bounded retries, observability, resource governance, rollback, lineage, and ownership.

## Practice prompts
1. Design quotas for a shared team namespace and explain trade-offs.
2. A training Pod is Pending after a policy change. Walk through diagnosis.
3. A run succeeded but model quality regressed. What controls would you add?
4. How would you safely verify cross-namespace restrictions?

Use topic guides and official sources to refine answers.