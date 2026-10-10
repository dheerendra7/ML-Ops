# Lab 01 — Kubernetes Resource Governance

This lab demonstrates how a namespace-level budget and per-container defaults work together. It uses small resource values and a lightweight pause image; it is a learning exercise, not a production sizing guide.

Related concepts: [Kubernetes resource controls](../kubernetes-foundations/resource-controls.md), [ResourceQuota example](../../examples/resource-policies/resource-quota.yaml), [LimitRange example](../../examples/resource-policies/limit-range.yaml).

## What you will learn

- Inspect the Kubernetes context before making changes.
- Validate manifests against the API server without persisting them.
- Apply a ResourceQuota and LimitRange in a dedicated namespace.
- Observe a Pod admitted by the quota and a third Pod rejected by the aggregate CPU request budget.
- Verify defaults applied to a Pod whose container omits resource fields.
- Clean up the test resources.

## Prerequisites and safety

You need **kubectl**, a reachable development Kubernetes cluster, permission to create namespaces and Pods, and permission to create ResourceQuota and LimitRange objects.

**Do not run this lab in production or in a namespace used by other people.** The commands create and delete resources. The namespace name below is only a default: if **mlops-lab** already exists, inspect it and do not reuse it unless you know it is a disposable namespace that belongs to you. Otherwise choose a unique namespace and change **metadata.namespace** in both example YAML files before continuing.

## 1. Check the cluster context

~~~bash
kubectl config current-context
kubectl get nodes
kubectl get namespace mlops-lab
~~~

Read the current context carefully. If it points at a production or shared cluster, stop and switch to a disposable development cluster.

Create the lab namespace only after confirming the context:

~~~bash
kubectl create namespace mlops-lab
~~~

If Kubernetes reports that the namespace already exists, do not assume it is safe to use. Choose a unique namespace or verify that it is exclusively yours.

## 2. Validate the manifests before applying

From the repository root, run:

~~~bash
kubectl apply --dry-run=server -f examples/resource-policies/resource-quota.yaml
kubectl apply --dry-run=server -f examples/resource-policies/limit-range.yaml
~~~

Server-side dry run asks the API server to validate the submitted objects without saving them. It requires a reachable API server and the namespace referenced by the manifests to exist. It does not prove that workloads will schedule or behave correctly.

If you changed the namespace, ensure both manifest files use the same namespace as the one you created.

## 3. Apply and inspect the policies

~~~bash
kubectl apply -f examples/resource-policies/resource-quota.yaml
kubectl apply -f examples/resource-policies/limit-range.yaml

kubectl describe resourcequota team-resource-budget -n mlops-lab
kubectl describe limitrange container-resource-defaults -n mlops-lab
kubectl get resourcequota,limitrange -n mlops-lab
~~~

The lab's ResourceQuota intentionally has a small CPU request budget: 500 millicores in total. The LimitRange permits each container to request up to 1 CPU and sets defaults when resource fields are omitted.

## 4. Prove the aggregate quota is enforced

Create two small Pods. Each requests 250 millicores of CPU, so together they use the full 500m request budget.

~~~bash
kubectl run quota-probe-1 --image=registry.k8s.io/pause:3.10 --restart=Never -n mlops-lab --requests='cpu=250m,memory=128Mi' --limits='cpu=500m,memory=256Mi'
kubectl run quota-probe-2 --image=registry.k8s.io/pause:3.10 --restart=Never -n mlops-lab --requests='cpu=250m,memory=128Mi' --limits='cpu=500m,memory=256Mi'
kubectl describe resourcequota team-resource-budget -n mlops-lab
~~~

Now attempt a third Pod with the same request:

~~~bash
kubectl run quota-probe-3 --image=registry.k8s.io/pause:3.10 --restart=Never -n mlops-lab --requests='cpu=250m,memory=128Mi' --limits='cpu=500m,memory=256Mi'
~~~

**Expected result:** the third Pod creation is rejected because the total CPU requests would exceed the namespace's quota. The exact error wording varies by Kubernetes version. If it is accepted, stop and inspect the manifest, namespace, and quota usage rather than assuming the test passed.

A Pod being admitted does not mean it has reached **Running**; scheduling also depends on cluster capacity, image availability, and other constraints. Admission/quota enforcement and scheduling are separate steps.

Inspect actual quota usage and Pod events:

~~~bash
kubectl describe resourcequota team-resource-budget -n mlops-lab
kubectl get pods -n mlops-lab
kubectl get events -n mlops-lab --sort-by=.lastTimestamp
~~~

## 5. Observe LimitRange defaults

Delete the two probe Pods first so their requests no longer consume the quota:

~~~bash
kubectl delete pod quota-probe-1 quota-probe-2 --ignore-not-found -n mlops-lab
~~~

Create a Pod without explicit resource requests or limits:

~~~bash
kubectl run defaulted-pod --image=registry.k8s.io/pause:3.10 --restart=Never -n mlops-lab
kubectl get pod defaulted-pod -n mlops-lab -o yaml
~~~

Inspect **spec.containers[0].resources** in the output. The API server should show the defaults configured by the LimitRange. The final admitted Pod is the source of truth; defaults can be affected by admission configuration and platform setup.

## 6. Clean up

Remove the Pods you created:

~~~bash
kubectl delete pod defaulted-pod quota-probe-1 quota-probe-2 quota-probe-3 --ignore-not-found -n mlops-lab
~~~

If, and only if, you created **mlops-lab** for this exercise and confirmed it contains no other resources you need, remove the namespace to delete the lab policies as well:

~~~bash
kubectl delete namespace mlops-lab
~~~

## Troubleshooting

| Symptom | What to check |
|---|---|
| **Forbidden** | Your account's RBAC permissions; ask the cluster administrator rather than bypassing access controls. |
| **NotFound** for the quota or LimitRange | The active context, namespace, manifest path, and object name. |
| The third Pod is accepted | Quota values and usage, resource requests on each Pod, and whether the policies were applied to that namespace. |
| Pod stays **Pending** | **kubectl describe pod** and namespace events; node capacity or other scheduling constraints may be the cause. |
| **ImagePullBackOff** | Cluster image-registry connectivity and events; quota admission can still be tested independently of a successful image pull. |

## Completion check

You have completed the lab when you can explain, without looking:

1. Why ResourceQuota is aggregate while LimitRange applies defaults or bounds to individual objects.
2. Why admission success and Pod scheduling are different.
3. Why namespace isolation alone does not replace RBAC or other security controls.

## References

- https://kubernetes.io/docs/concepts/policy/resource-quotas/
- https://kubernetes.io/docs/concepts/policy/limit-range/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_run/
