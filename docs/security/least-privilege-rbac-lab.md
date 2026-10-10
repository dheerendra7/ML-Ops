# Lab 02 — Least-Privilege RBAC for a Read-Only Inspector

> Is lab mein ek namespace-scoped ServiceAccount ko sirf Pods read/list/watch karne ki permission di jaati hai. Allowed aur denied API actions dono check karo. Goal permission grant karna hi nahi, unwanted permission absent hone ka evidence bhi collect karna hai.

## What you will learn

- Kubernetes ServiceAccount aur RBAC Role/RoleBinding ke roles distinguish karna.
- Namespace-scoped permissions apply aur inspect karna.
- Verify karna ki intended read actions allowed aur create/secret-read actions denied hain.
- Understand karna ki ServiceAccount token auto-mount disable karne se workload ko token by default nahi milta.
- RBAC checks ko secret management, network policies aur full tenant isolation ka replacement na samajhna.

## Safety and prerequisites

You need a disposable development cluster, kubectl, and permission to create a namespace, ServiceAccount, Role and RoleBinding. The test identity running the impersonation commands also needs permission to impersonate the ServiceAccount.

**Production or shared namespace mein run mat karo.** This lab creates the namespace **mlops-rbac-lab**, and the cleanup step deletes that entire namespace. Agar name already exist karta hai, use inspect karo aur blindly reuse mat karo; unique namespace choose karo aur YAML mein all namespace references update karo.

## 1. Verify context and create the dedicated namespace

~~~bash
kubectl config current-context
kubectl get nodes
kubectl get namespace mlops-rbac-lab
~~~

Confirm the current context is the disposable cluster you intend to use. Then create the namespace:

~~~bash
kubectl create namespace mlops-rbac-lab
~~~

If it already exists, stop and verify ownership and contents before deciding what to do.

## 2. Review and validate the policy

Open [rbac-readonly-inspector.yaml](../../examples/security/rbac-readonly-inspector.yaml) and inspect the whole file before applying it.

~~~bash
kubectl apply --dry-run=server -f examples/security/rbac-readonly-inspector.yaml
~~~

Server-side dry run checks the API server's validation without saving the resources. The namespace must exist first. This does not prove the policy's effective permissions; verify them after applying.

Apply the policy:

~~~bash
kubectl apply -f examples/security/rbac-readonly-inspector.yaml
kubectl get serviceaccount,role,rolebinding -n mlops-rbac-lab
kubectl describe role pod-reader -n mlops-rbac-lab
kubectl describe rolebinding pod-reader-binding -n mlops-rbac-lab
~~~

The Role grants only the namespace-scoped verbs get, list and watch on Pods. It does not grant Pod creation/deletion, exec, Secret read, or access to other namespaces.

## 3. Verify allowed and denied actions

Use the ServiceAccount identity for the permission checks:

~~~bash
kubectl auth can-i list pods -n mlops-rbac-lab --as=system:serviceaccount:mlops-rbac-lab:read-only-inspector
kubectl auth can-i get pods -n mlops-rbac-lab --as=system:serviceaccount:mlops-rbac-lab:read-only-inspector
kubectl auth can-i create pods -n mlops-rbac-lab --as=system:serviceaccount:mlops-rbac-lab:read-only-inspector
kubectl auth can-i get secrets -n mlops-rbac-lab --as=system:serviceaccount:mlops-rbac-lab:read-only-inspector
kubectl auth can-i list pods -n default --as=system:serviceaccount:mlops-rbac-lab:read-only-inspector
~~~

Expected results in order:

- list Pods in the lab namespace: **yes**
- get Pods in the lab namespace: **yes**
- create Pods in the lab namespace: **no**
- get Secrets in the lab namespace: **no**
- list Pods in another namespace: **no**, because this RoleBinding is namespace-scoped

If a command reports a Forbidden error about impersonation, that does **not** prove the Role is incorrect. It means your current identity may not be allowed to impersonate that ServiceAccount. Run checks through an authorized cluster administrator or an approved test identity; do not grant broad extra permissions merely to make the test command work.

## 4. Understand the ServiceAccount token setting

The ServiceAccount sets **automountServiceAccountToken: false**. This prevents Kubernetes from automatically mounting the ServiceAccount API token into Pods that use this account, unless the Pod configuration explicitly overrides the setting.

This is a useful least-privilege default when the workload does not need to call the Kubernetes API. It does not remove the Role/RoleBinding, and it does not prove the identity is isolated from network, storage, other credentials or application-level data access.

If a workload genuinely needs Kubernetes API access, decide which verbs/resources it needs, configure credentials intentionally, and verify its effective permissions. Do not turn token auto-mount on by default for every workload.

## 5. Common failure modes

| Symptom | What it means / what to check |
|---|---|
| Namespace not found | Create the dedicated namespace first, or update all YAML namespace references consistently. |
| Apply says Forbidden | The current identity cannot create one of the resources; get approved permissions rather than bypassing RBAC. |
| Allowed action returns no | Check that the RoleBinding subject is the intended ServiceAccount and the Role is in the expected namespace. |
| Denied action returns yes | Find other RoleBindings, ClusterRoleBindings, groups or inherited privileges granting access. RBAC permissions are additive. |
| Impersonation Forbidden | The user running the test lacks impersonation permission; this is separate from the target ServiceAccount's effective permissions. |
| Pod can call the API unexpectedly | Check ServiceAccount selection, Pod-level automount overrides and how credentials are delivered. |

The effective result includes all applicable bindings and privileges, not only this one Role. A Role manifest by itself is not proof that the whole cluster has least privilege.

## 6. Cleanup

Only if you created this namespace exclusively for the lab and verified it contains no resources you need:

~~~bash
kubectl delete namespace mlops-rbac-lab
~~~

Namespace deletion removes all lab objects within it. Never run it against a shared/production namespace to clean up one example.

## 7. What this lab does not cover

This lab is deliberately narrow. It does not test or configure:

- Secret creation, external secret managers, rotation or revocation.
- NetworkPolicy behavior or service-to-service connectivity.
- Cloud workload identity, object-storage permissions or external credential exchange.
- Kubeflow Profile controllers and multi-user installation-specific behavior.
- Full tenant isolation or a production RBAC review.

Those require their own design and environment-specific tests.

## Completion check

- [ ] Server-side dry run and apply succeed in the disposable namespace.
- [ ] Read/list Pods checks return yes for the test identity.
- [ ] Create Pods and get Secrets checks return no.
- [ ] Cross-namespace Pod listing returns no.
- [ ] Any impersonation failure is diagnosed separately from the ServiceAccount's permissions.
- [ ] Lab namespace is removed after confirming it is safe to delete.

## References

- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_can-i/
- https://kubernetes.io/docs/concepts/configuration/secret/
- https://kubernetes.io/docs/concepts/security/security-checklist/
