# Source Register

Prefer official documentation. Verify the version selector and installed release before relying on a detail.

## Kubernetes
- Concepts: https://kubernetes.io/docs/concepts/
- Container images and digest pinning: https://kubernetes.io/docs/concepts/containers/images/
- Kubernetes security checklist: https://kubernetes.io/docs/concepts/security/security-checklist/
- Namespaces: https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- Resource management: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- ResourceQuota: https://kubernetes.io/docs/concepts/policy/resource-quotas/
- GPU scheduling and device plugins: https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
- LimitRange: https://kubernetes.io/docs/concepts/policy/limit-range/
- Pods: https://kubernetes.io/docs/concepts/workloads/pods/
- Jobs: https://kubernetes.io/docs/concepts/workloads/controllers/job/
- Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Services: https://kubernetes.io/docs/concepts/services-networking/service/
- ConfigMaps: https://kubernetes.io/docs/concepts/configuration/configmap/
- Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Distribute credentials securely to Pods: https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/
- RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- kubectl auth can-i: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_auth/kubectl_auth_can-i/
- Debugging Pods: https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/
- kubectl apply and server-side dry run: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/
- kubectl run and supported flags/overrides: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_run/
- kubectl logs: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/
- kubectl describe: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_describe/

## Kubeflow
- Documentation: https://www.kubeflow.org/docs/
- KFP component guides: https://www.kubeflow.org/docs/components/pipelines/user-guides/components/
- KFP SDK docs: https://kubeflow-pipelines.readthedocs.io/
- KFP parameters and data types: https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/data-types/
- KFP artifacts: https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/
- KFP caching: https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/caching/
- KFP local pipeline execution: https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/execute-kfp-pipelines-locally/
- Docker SDK for Python: https://pypi.org/project/docker/
- KFP task configuration and retries: https://www.kubeflow.org/docs/components/pipelines/user-guides/components/compose-components-into-pipelines/
- Container build best practices: https://docs.docker.com/build/building/best-practices/
- Kubernetes observability: https://kubernetes.io/docs/concepts/cluster-administration/observability/
- Kubernetes logging architecture: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- OpenTelemetry signals: https://opentelemetry.io/docs/concepts/signals/
- Prometheus instrumentation guidance: https://prometheus.io/docs/practices/instrumentation/
- Prometheus alerting guidance: https://prometheus.io/docs/practices/alerting/
- KFP releases and SDK version notes: https://github.com/kubeflow/pipelines/releases
- Kind quick start for disposable Kubernetes clusters: https://kind.sigs.k8s.io/docs/user/quick-start/
- Kind GitHub Action releases: https://github.com/helm/kind-action/releases
- Profiles: https://www.kubeflow.org/docs/components/central-dash/profiles/

## External Secrets and Vault
- External Secrets Operator installation: https://external-secrets.io/main/introduction/getting-started/
- External Secrets Operator HashiCorp Vault provider: https://external-secrets.io/main/provider/hashicorp-vault/
- External Secrets Operator release history: https://github.com/external-secrets/external-secrets/releases
- HashiCorp Vault dev-server security warning: https://developer.hashicorp.com/vault/docs/concepts/dev-server
- HashiCorp Vault on Kubernetes with Helm: https://developer.hashicorp.com/vault/docs/deploy/kubernetes/helm/run
- HashiCorp Vault Helm chart releases: https://github.com/hashicorp/vault-helm/releases

Link the exact official page near the claim it supports. For version-sensitive behavior, include the release context. Confirm important community-sourced tips with official docs or a reproducible test.