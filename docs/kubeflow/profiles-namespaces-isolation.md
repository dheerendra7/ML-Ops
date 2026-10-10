# Profiles, Namespaces, and Isolation

## 5-minute snapshot
A Kubernetes namespace scopes namespaced objects and is useful for policy and administration. In common Kubeflow multi-user installations, a **Profile** custom resource represents a user/workspace and may provision a namespace and related resources. Exact behavior and fields depend on the Kubeflow release and installation.

## Do not treat these as synonyms
- **Profile:** Kubeflow-specific abstraction used by supported multi-user setups.
- **Namespace:** Kubernetes scope for many resources and policies.
- **RBAC:** Controls which API actions an identity may perform.
- **ResourceQuota:** Limits aggregate consumption or object counts in a namespace.
- **LimitRange:** Sets defaults and constraints for individual objects.
- **Network policy/runtime controls:** May be needed to restrict traffic and workload behavior.

## Isolation checklist
1. Confirm multi-user mode and the installed Profile controller/version.
2. Verify how identities map to users or workspaces.
3. Inspect namespace creation and ownership behavior.
4. Review RoleBindings, ClusterRoleBindings, service accounts, and permitted API verbs.
5. Apply resource budgets and per-object defaults where appropriate.
6. Review network access, secret access, storage permissions, and pod security.
7. Test cross-namespace access with non-privileged test identities.
8. Record expected behavior and re-verify after upgrades.

A namespace alone is not a complete security boundary.

## Read-only inspection commands
```bash
kubectl get namespaces
kubectl get profiles -A
kubectl get resourcequota,limitrange -A
kubectl get rolebindings,serviceaccounts -n <namespace>
```

The profiles resource may not exist if the relevant CRD is not installed. Confirm target cluster and permissions before running commands.

## References
- https://www.kubeflow.org/docs/components/central-dash/profiles/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/