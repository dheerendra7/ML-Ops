# Lab 03 — Kubernetes Secrets, Safe Rotation, and External Secret Boundaries

> Is lab ka focus secret value reveal karna nahi hai. Hum synthetic dummy credential use karenge, Kubernetes Secret access ko review karenge, rotation ke impact ko samjhenge, aur identify karenge ki external secret manager integration ko kaun configure karta hai.

## Learning goals

- Secret values ko source code, committed YAML, Docker image aur logs se bahar rakhna.
- Kubernetes Secret object, RBAC and workload consumption ko separate concepts samajhna.
- Safe demo credential ko disposable namespace mein create/update karna without printing its contents.
- Understand karna ki mounted files aur environment variables rotation ko alag tarah reflect karte hain.
- External secret provider/controller requirements ko identify karna without assuming they exist in every cluster.

## Preconditions and safety

Use a disposable cluster and only a synthetic value such as **lab-only-not-a-real-credential**. **Real password, cloud key, API token or production Secret is not part of this lab.** Never commit generated Secret YAML or paste secret values into logs/issues.

This exercise creates namespace **mlops-secrets-lab**; cleanup deletes that entire namespace. If the namespace exists, inspect it and choose a unique name instead of reusing it blindly.

Confirm context first:

~~~bash
kubectl config current-context
kubectl get nodes
kubectl get namespace mlops-secrets-lab
kubectl create namespace mlops-secrets-lab
~~~

If the namespace already exists, stop and verify that it is yours and disposable before continuing. Do not run namespace creation on a production/shared context.

## 1. Create a dummy credential without committing it

The following Bash example writes only a fake value to a temporary local file. It does not use a real credential. Do not add this file, its contents, or a rendered Secret manifest to Git.

~~~bash
umask 077
SECRET_FILE="$(mktemp)"
printf '%s' 'lab-only-not-a-real-credential' > "$SECRET_FILE"

kubectl create secret generic demo-api-credential \
  --namespace mlops-secrets-lab \
  --from-file=api_key="$SECRET_FILE"

rm -f "$SECRET_FILE"
unset SECRET_FILE
~~~

This command creates a Secret from a local file. For real secrets, follow the organization's approved secret manager and shell/session hygiene; don't put the secret value in a command-line literal or source file. A terminal, process, shell history, CI logs or local filesystem can leak credentials if used carelessly.

Verify only object metadata and keys, not the encoded value:

~~~bash
kubectl describe secret demo-api-credential -n mlops-secrets-lab
kubectl get secret demo-api-credential -n mlops-secrets-lab -o jsonpath='{.data.api_key}' > /dev/null
~~~

Do not print the value from the JSONPath command. Kubernetes Secret data is base64-encoded in API representations; base64 is **not encryption**.

## 2. Understand the security boundary

A Kubernetes Secret object is not a complete secret-management system by itself. Review all of these separately:

- **RBAC:** who can read, create, update, watch or delete Secrets in the namespace?
- **Encryption at rest:** is the API datastore configured to encrypt Secret data according to the platform's policy?
- **Audit and backups:** where do Secret values appear, who can access audit logs/backups, and how are they protected?
- **Workload identity:** which service account and external identity does the workload run as?
- **Delivery method:** Secret volume, environment variable, CSI integration or external controller? Each has lifecycle and access implications.
- **Rotation and revocation:** who rotates the upstream credential, updates Kubernetes/consumer state and confirms the old credential no longer works?

A namespace boundary alone does not grant or deny Secret access. Effective permission may be broader due to other RoleBindings or ClusterRoleBindings. Review the full identity and access policy.

## 3. Update the synthetic credential (rotation demonstration)

This is a demo-only rotation using a second fake value. It again avoids printing the value:

~~~bash
umask 077
NEXT_SECRET_FILE="$(mktemp)"
printf '%s' 'lab-only-rotated-not-a-real-credential' > "$NEXT_SECRET_FILE"

kubectl create secret generic demo-api-credential \
  --namespace mlops-secrets-lab \
  --from-file=api_key="$NEXT_SECRET_FILE" \
  --dry-run=client -o yaml |
  kubectl apply -f -

rm -f "$NEXT_SECRET_FILE"
unset NEXT_SECRET_FILE

kubectl describe secret demo-api-credential -n mlops-secrets-lab
kubectl get secret demo-api-credential -n mlops-secrets-lab -o jsonpath='{.data.api_key}' > /dev/null
~~~

The same Secret object's data has been updated. This exercise does not demonstrate integration with an upstream vault or prove an application has refreshed its credentials.

**Important consumer behavior:**

- Secret values injected as environment variables into an already-running container do not update automatically. A consumer process generally needs a restart/rollout or an explicit supported reload mechanism.
- Secret values mounted through Kubernetes Secret volumes can be updated eventually, but applications must reopen/reload the projected file and tolerate rotation timing. **subPath** mounts have different update behavior; consult the current Kubernetes documentation.
- An application may cache a credential in memory even after the mounted file changes. Verify consumer state instead of assuming the change took effect.
- Changing a Kubernetes Secret is not enough if the credential must also be rotated/revoked with an upstream provider. Coordinate provider-side rotation, consumer update, verification and old-credential revocation.

For production rotations, define an owner, schedule, validation and rollback/recovery procedure. Avoid a manual rotation that briefly leaves the old and new credentials unusable.

## 4. External secret manager: what must exist?

A vendor-neutral architecture can look like this:

~~~text
Approved secret manager / vault
             |
     Controller / CSI integration
             |
             v
   Kubernetes workload boundary
             |
             v
      Application consumer
~~~

This is conceptual only. A controller or CSI driver must be installed and configured for the chosen provider. Required provider credentials/identity, CRDs, permissions, network connectivity and refresh behavior vary by integration.

Before configuring an external secret controller:

1. Confirm the chosen integration's version matches Kubernetes and provider requirements.
2. Configure provider authentication with least privilege, ideally through an approved workload identity where supported.
3. Limit which namespaces and Secret objects the controller may manage.
4. Understand refresh intervals, rotation propagation, deletion policy and failure behavior during provider outage.
5. Verify audit trail, encryption, data residency, backup and break-glass procedures.
6. Test rotation with a dummy credential in a development namespace before onboarding real workloads.

Do not install a provider controller or apply vendor-specific custom resources from an unreviewed blog post. The cluster may not have the matching CRD/controller installed, and a Secret-sync controller can have broad access if misconfigured.

## 5. Safe diagnostic checks

Review the object and the identity's permission without showing secret contents:

~~~bash
kubectl get rolebindings -n mlops-secrets-lab
kubectl get serviceaccounts -n mlops-secrets-lab
kubectl auth can-i get secrets -n mlops-secrets-lab
kubectl auth can-i list secrets -n mlops-secrets-lab
kubectl describe secret demo-api-credential -n mlops-secrets-lab
~~~

The authorization checks test the identity from the current kubeconfig, not a hypothetical application service account unless you explicitly use an authorized impersonation/test identity. Do not paste the output of a full Secret YAML into issues or commits.

## 6. Common failure modes

| Symptom | What to check |
|---|---|
| Secret value is missing | Correct namespace/name/key, file path, identity and creation error; don't print the actual value for diagnosis |
| Application still uses old credential | Env-variable lifecycle, mounted file update, process-level cache, provider-side rotation and reload mechanism |
| API says Forbidden | Current identity, RoleBindings/ClusterRoleBindings, requested verb/resource, and intended policy |
| External controller does not sync | Controller/CRD installed, provider identity/permissions, network connectivity, provider path/version and controller events |
| Rotation causes an outage | Consumer reload, old/new credential overlap, upstream revocation order, readiness/health checks and rollback plan |

## 7. Cleanup

Only after verifying that the namespace was created solely for this lab and no resources must be preserved:

~~~bash
kubectl delete namespace mlops-secrets-lab
~~~

This deletes all resources in the namespace. Never run it against a shared or production namespace as a generic cleanup shortcut.

## Completion criteria

- [ ] Only synthetic demo values were used; no real secret was written to repository files.
- [ ] Secret metadata/key existence was verified without printing the value.
- [ ] The demo Secret was updated using a second fake value.
- [ ] Secret access, encryption-at-rest, delivery and rotation were treated as separate controls.
- [ ] The differences between env-var refresh and volume projection were explained.
- [ ] Provider-specific integration requirements are documented before installing any controller.
- [ ] The disposable namespace was deleted only after checking it was safe.

## References

- https://kubernetes.io/docs/concepts/configuration/secret/
- https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- https://kubernetes.io/docs/concepts/security/security-checklist/
