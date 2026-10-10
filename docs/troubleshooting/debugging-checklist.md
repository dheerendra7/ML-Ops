# Debugging Checklist: Start with Evidence

## 5-minute approach
1. State the symptom: Pending, CrashLoopBackOff, failed task, missing artifact, or permission denied.
2. Confirm the object and namespace.
3. Read status and events.
4. Inspect logs and effective configuration.
5. Change one thing at a time and capture before/after evidence.

## Quick commands
```bash
kubectl get pods -A
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace> --all-containers=true
kubectl logs <pod> -n <namespace> --previous
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

Logs may contain sensitive output; review before sharing.

## Symptom map
- **Pending:** inspect scheduling events, requests, quotas, node capacity, affinity, taints, and PVC binding.
- **CrashLoopBackOff:** inspect current/previous logs, exit code, startup command, config, and probe behavior.
- **ImagePullBackOff:** verify image name/tag/digest, registry reachability, and pull credentials.
- **Forbidden:** inspect effective identity, namespace, RoleBindings, ClusterRoleBindings, and requested API verb/resource.
- **Pipeline task failed:** inspect task logs, inputs, outputs, image, dependencies, and service identity.
- **Missing artifact:** verify task completion, output metadata/path, storage configuration, and permissions.

## Safe habits
- Never paste kubeconfig, tokens, secrets, or sensitive logs into public issues.
- Prefer read-only commands first.
- Avoid deleting resources until impact and recovery are understood.
- Capture relevant Kubernetes and Kubeflow/KFP versions.

## Reference
- https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/