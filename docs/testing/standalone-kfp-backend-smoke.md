# Standalone Kubeflow Pipelines Backend Smoke Test

This repository has two separate KFP test layers:

1. **Local KFP DockerRunner test** — compiles and executes components locally through the SDK's DockerRunner.
2. **Standalone backend smoke test** — installs the open-source Kubeflow Pipelines (KFP) v2.17.0 platform-agnostic manifests into a disposable Kind cluster, then submits runs through the actual KFP API.

The second layer is deliberately separate from the normal handbook CI because installing a standalone KFP control plane takes substantially longer and pulls multiple backend/container images.

## What the backend smoke test is supposed to verify

The workflow at [kfp-backend-smoke.yml](../../.github/workflows/kfp-backend-smoke.yml) creates a disposable Kubernetes 1.34.3 cluster, installs the KFP 2.17.0 cluster-scoped resources and platform-agnostic overlay, then submits two runs with the pinned Python SDK:

| Run | Parameters | Expected evidence |
|---|---|---|
| handbook-backend-pass | offset=0.0, minimum_score=0.8 | Run `SUCCEEDED`; dataset, training, evaluation, and gate tasks succeed; Dataset/Model artifact IDs are present on producer outputs and consumer inputs |
| handbook-backend-rejected-candidate | offset=1.0, minimum_score=0.8 | Run `FAILED`; the dataset, training, and evaluation tasks succeed; the quality-gate task itself is `FAILED`; artifact references are still present upstream |

The example pipeline uses synthetic rows and an illustrative score. It is not a real model-training benchmark or a production-quality metric. The failed candidate is a deliberate negative test.

The runner waits for the KFP API before creating the experiment, compiles the package, and waits for each run's terminal state. It then fetches each full run detail and asserts task-level states plus non-empty Dataset/Model artifact IDs for producer outputs and consumer inputs. The negative case fails closed unless all upstream tasks succeeded and the gate task itself failed. A successful installation step, API health check, or generic `FAILED` run alone is not enough.

## Running the workflow

The optional workflow triggers on changes to the KFP example, backend test script, or workflow itself. It can also be started manually using GitHub Actions workflow_dispatch.

- [Open all GitHub Actions runs](https://github.com/dheerendra7/ML-Ops/actions)
- [Standalone backend smoke workflow source](../../.github/workflows/kfp-backend-smoke.yml)
- [Remote submission test script](../../scripts/test_kfp_backend.py)
- [Synthetic pipeline source](../../examples/kfp/pipeline_artifacts_caching.py)

Check the exact commit, workflow run and job conclusion. A queued, running, failed or cancelled run does not count as backend validation.

## Why the workflow installs platform-agnostic

KFP 2.17.0's platform-agnostic Kustomize overlay includes the core pipeline installation and its required supporting components, including workflow orchestration, metadata and the selected backing stores. The test uses the version-tagged upstream manifests rather than pretending the previously installed Kubernetes CRDs represent a complete KFP deployment.

Upstream release manifests used by the workflow:

- Cluster-scoped resources: https://github.com/kubeflow/pipelines/tree/2.17.0/manifests/kustomize/cluster-scoped-resources
- Platform-agnostic KFP environment: https://github.com/kubeflow/pipelines/tree/2.17.0/manifests/kustomize/env/platform-agnostic
- KFP v2.17.0 release source: https://github.com/kubeflow/pipelines/tree/2.17.0

## What a successful run proves

For the specific KFP version, Kubernetes node image, SDK pin and CI environment tested, successful outcomes provide evidence that:

- the standalone manifests can install and reach the configured Deployment readiness criteria;
- the Python SDK can connect through the configured API endpoint;
- a compiled synthetic pipeline package can be submitted as a remote run;
- the backend schedules the sample tasks and exposes non-empty artifact references for Dataset/Model producer outputs and consumer inputs;
- every expected task on a valid candidate completes successfully;
- the intentionally below-threshold candidate fails specifically at the quality-gate task after its upstream tasks succeed.

It is still only a focused smoke test. It does not establish production availability, performance, security certification, multi-user Profile behavior, a full community Kubeflow distribution, cloud IAM, external secret-manager integration, GPU execution or data/model quality for a real ML use-case.

## Troubleshooting by stage

| Stage | Initial diagnosis |
|---|---|
| Kind cluster creation | Check cluster action logs, runner resources and pinned node image |
| Cluster-scoped KFP resources | Check API validation errors and CRD establishment |
| Platform-agnostic rollout | Inspect Pods, events, Deployment availability, image pulls, resource pressure and database/storage readiness |
| Client SDK installation | Check Python interpreter and installable pinned SDK |
| API health check | Verify the port-forward process and service HTTP port; retry SDK client initialization while startup completes. Start kubectl before isolating HOME for the KFP client, otherwise kubectl may lose the Kind kubeconfig. |
| Experiment/run submission | Inspect API response, namespace/context and backend logs without printing credentials |
| Run waits but does not finish | Check workflow-controller/task Pods, image pulls, task logs, artifact store and admission/quota issues |
| Negative run fails for an unrelated reason | The test checks task-level states, verifies that upstream tasks succeeded, and requires the quality-gate task itself to be FAILED; inspect that task's detail and pod logs without exposing credentials |
| Artifact hand-off is missing | The test requires Dataset/Model artifact IDs on declared producer outputs and consumer inputs; inspect task details and KFP metadata/artifact-store configuration |

The workflow prints safe Kubernetes diagnostics if the backend job fails. Use those diagnostics instead of claiming remote execution passed just because the control plane started.

## Safety and resource boundaries

The test runs only in a temporary CI-created Kind cluster. It has no credentials to the user's personal or production Kubernetes cluster. The workflow uses upstream KFP 2.17.0 manifests and a Python SDK pin selected for package-index availability.

Do not copy the standalone install commands into a shared/production cluster without reviewing storage durability, auth, TLS, access boundaries, resource requests, image versions, backup/restore, multi-user configuration and upgrade strategy.
