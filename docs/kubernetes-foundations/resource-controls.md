# Kubernetes Resource Controls

## 5-minute snapshot
- **Requests** inform scheduling decisions for resources such as CPU and memory.
- **Limits** constrain supported resource use at runtime; CPU is generally throttled over its limit, while memory pressure can result in OOM termination.
- **ResourceQuota** constrains aggregate resource consumption or object counts within a namespace.
- **LimitRange** can define defaults, minimums, and maximums for individual objects.

These solve different problems and are often used together.

## Mental model
Think of a namespace as a shared team budget. ResourceQuota limits the team's total budget. LimitRange sets rules for each individual request. Container requests and limits describe a particular workload's expected and permitted resource usage.

## Diagnostic commands
```bash
kubectl describe pod <pod> -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
kubectl describe resourcequota -n <namespace>
kubectl describe limitrange -n <namespace>
```

Look for scheduling messages, quota rejections, defaulted values, and termination reasons. Names are placeholders.

## Practical notes
- A Pod can remain Pending when the scheduler cannot find capacity for its requests or constraints.
- A quota may reject creation or updates that exceed policy.
- LimitRange defaults may apply when resource fields are omitted; inspect the resulting Pod.
- CPU and memory limits have different runtime effects.
- GPU and extended resources are cluster-specific.

## Examples
- [ResourceQuota YAML](../../examples/resource-policies/resource-quota.yaml)
- [LimitRange YAML](../../examples/resource-policies/limit-range.yaml)

Read and adapt examples before applying; values are not a sizing recommendation.

## References
- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://kubernetes.io/docs/concepts/policy/resource-quotas/
- https://kubernetes.io/docs/concepts/policy/limit-range/