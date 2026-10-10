# Cost Controls and GPU Scheduling for MLOps

> Efficient MLOps ka aim sirf machine-hours kam karna nahi. Goal hai reliable, reproducible results ko right-sized resources, bounded concurrency aur predictable storage/accelerator use ke saath produce karna.

## 5-minute snapshot

- **Right-sizing:** CPU, memory, disk and accelerator resources ko measured workload ke hisaab se request karo.
- **Concurrency controls:** pipelines/tasks ko cluster, namespace, API and external-system capacity ke according bound karo.
- **Caching:** repeated expensive work avoid kar sakti hai, but only when declared inputs actually capture task dependencies.
- **Cost observability:** spend ko workload/team/model/run identity se correlate karo, sensitive metric labels ke bina.
- **GPU scheduling:** Kubernetes ko vendor device plugin or compatible resource integration ke through GPU resource advertise karna hota hai; container ko matching driver/runtime stack aur required libraries bhi chahiye.
- **Retention:** intermediate artifacts/logs useful hote hain, but storage and retention policy intentional honi chahiye.

GPU request specify karne se GPU available create nahi ho jata. Cluster administrator ko compatible nodes, driver and supported device plugin/resource integration configure karni hoti hai.

## 1. Measure useful outcomes, not only compute time

Machine-hours or GPU-hours alone don't tell whether a pipeline is efficient. Useful measures can include:

- cost per successful training run or accepted model candidate;
- cost per evaluation cycle or useful experiment;
- proportion of runs failing due to avoidable setup/configuration problems;
- time spent waiting in queue versus running;
- GPU utilization when trustworthy telemetry is available;
- artifact/storage/egress cost and retention duration;
- number of redundant runs avoided through caching or deduplication.

Define what counts as a useful result. A fast but invalid model, duplicated run or pipeline that passes without valid evaluation is not good resource efficiency.

Cloud and on-prem cost models differ. Prices depend on region, machine type, commitment, spot/preemptible policy, storage, network egress, license and idle capacity. This handbook does not recommend a universal price or instance size.

## 2. Right-size CPU, memory and storage

1. Start with baseline requests based on representative runs rather than guessing.
2. Observe CPU/memory use and peak patterns, not just averages.
3. Set requests to give the scheduler realistic placement information.
4. Set limits where appropriate with awareness of CPU throttling and memory OOM behavior.
5. Include sidecars, init containers, downloads, temporary files, checkpoints and output serialization in resource estimates.
6. Set ephemeral storage expectations where supported and monitor disk pressure.
7. Re-measure when data volume, framework, image or model size changes.

Very high requests can leave Pods pending and waste scarce capacity. Too-low memory limits may OOM; overly tight CPU limits can throttle compute-heavy steps. ResourceQuota controls aggregate namespace usage, while LimitRange constrains/defaults individual objects.

Related reference: [resource controls](../kubernetes-foundations/resource-controls.md).

## 3. Bound pipeline concurrency and retries

- Set task/run concurrency according to cluster schedulable capacity and external dependencies.
- Account for each concurrent Pod's request, init-container/sidecar overhead, GPU usage, storage and temporary data.
- Use namespace quotas and appropriate request/limit policy to avoid one workload exhausting shared resources.
- Bound retries and exponential backoff where applicable. A permanent schema error should not trigger repeated costly training attempts.
- Make side-effecting tasks idempotent before retrying or parallelizing them.
- Use queueing or workload priorities only where your platform supports and your operations team has agreed their behavior.

A pipeline can be expensive even when each task is small if repeated runs, retries or parallel branches fan out uncontrollably.

## 4. Use caching only for valid dependencies

Cache reuse can save time and compute for identical work. It is not inherently correct for tasks that read mutable external state or should deliberately run every time.

Before enabling caching, check:

- all meaningful inputs and configuration are declared/versioned;
- source/dependency image is tracked;
- data version and relevant preprocessing are explicit;
- external API/DB state, current time and secret-controlled behavior are not hidden dependencies;
- cache hit/miss behavior is visible enough for debugging and cost attribution.

See [KFP caching and retries guide](../kubeflow/pipeline-lifecycle-artifacts-caching-retries.md) and [reproducibility/lineage](reproducibility-and-lineage.md).

## 5. GPU scheduling prerequisites

For traditional NVIDIA GPU device-plugin setups, check these layers in order:

1. **Node hardware:** expected GPU model/count exists on the intended node.
2. **Host driver:** vendor-supported driver is correctly installed.
3. **Device plugin/resource integration:** cluster advertises an extended resource such as **nvidia.com/gpu**.
4. **Runtime image:** container image contains compatible user-space CUDA/runtime/framework libraries for that setup.
5. **Resource request:** Pod/Job requests the advertised resource using its exact name.
6. **Placement rules:** labels, affinity, taints/tolerations or topology constraints (if the cluster uses them) match the intended nodes.
7. **Quota/permissions:** namespace quotas and admission policies allow the request.
8. **Runtime verification:** application can see/use the accelerator and logs/metrics capture device-related failures.

GPU drivers and device-plugin lifecycle are cluster-admin responsibilities, not something a regular Pod manifest installs. Different vendor/plugin/DRA deployments may expose different resource names and configuration. Use the docs for the actual cluster integration.

## 6. Example GPU Job manifest

See [gpu-job.example.yaml](../../examples/cost/gpu-job.example.yaml). It is a **deliberately non-runnable template**: replace the example image with an approved image that actually contains your GPU framework/runtime, and replace the placeholder digest with the registry-verified digest before using it.

The example requests **nvidia.com/gpu: 1** under container limits, along with modest CPU/memory resources. Kubernetes generally exposes device-plugin GPUs as an extended resource; those resources cannot be overcommitted, and if both request and limit are set they must be equal. Check the official documentation for the target Kubernetes release and vendor plugin.

Do not apply the sample while its **registry.example.invalid** image or digest placeholder remains. It is suitable for YAML syntax validation and policy review, not as an immediately runnable workload.

## 7. GPU quota and placement

An administrator may choose to set a namespace quota for the GPU extended resource. For the traditional **nvidia.com/gpu** resource, the quota key has the form:

~~~yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gpu-budget
  namespace: replace-with-reviewed-namespace
spec:
  hard:
    requests.nvidia.com/gpu: "2"
~~~

This is an illustrative snippet; validate it against the cluster and namespace policy before applying. GPU quota limits aggregate namespace requests, not each user's fairness, model quality or GPU utilization.

If a Pod stays Pending, inspect:

~~~bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get nodes -o wide
kubectl describe resourcequota -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
~~~

The node wide listing does not directly show all extended-resource allocatable fields; use **kubectl describe node <node>** or inspect node status YAML to confirm GPU capacity. If the extended resource is absent, check node inventory, driver health, device-plugin DaemonSet and cluster integration. If the resource is present but scheduling fails, check free allocatable capacity, existing allocations, quota, labels, taints/tolerations and affinity.

## 8. Storage, artifacts and idle capacity

- Keep only intermediate artifacts needed for recovery, audit, lineage, reproducibility or model review.
- Apply retention tiers for temporary runs, failed-run diagnostics, evaluation evidence and release artifacts.
- Remove orphaned test resources and development clusters using an approved process.
- Check artifact size, duplicate uploads, object-store request volume and network egress where relevant.
- Use checkpoints for long-running expensive work when supported and operationally worth maintaining.
- Avoid shutting down or deleting resources blindly; consider owners, active runs, recovery and data retention.

## 9. Cost guardrails and alerting

Define local guardrails instead of copy/pasting universal numbers:

- max concurrent training jobs per namespace/team;
- per-namespace CPU/memory/GPU quota;
- maximum run duration and bounded retries;
- storage/egress limits or alert thresholds;
- budget alerts tied to owner/project;
- policy for expensive or unusual accelerator requests;
- approved process for overrides and urgent high-priority runs.

Cost signals need attribution and an owner. A budget alert that no one can map to a team/run is hard to action. Use the [observability guide](observability-for-ml-pipelines.md) to connect usage/failure signals with actionable alerts.

## 10. Checklist

- [ ] Representative runs were profiled before choosing resource defaults.
- [ ] Requests, limits and quota values have a named owner and review trigger.
- [ ] Concurrent runs/retries are bounded and side effects are safe to repeat.
- [ ] Caching policy reflects true dependencies and required freshness.
- [ ] Image/framework/driver compatibility is documented for GPU workloads.
- [ ] GPU nodes advertise the expected extended resource.
- [ ] Placement and namespace quota match intended access/capacity policy.
- [ ] Cost/spend can be attributed to workload/team/project without exposing secrets.
- [ ] Artifact/storage/retention and cleanup have an owner.
- [ ] Production examples have been validated on a named environment before being described as tested.

## Recall questions

1. Machine-hours ke comparison mein cost per successful/accepted result kya extra information deta hai?
2. Under-requesting aur over-requesting CPU/memory ke possible consequences kya hain?
3. GPU request add karne se pehle node par kaun-si components ready honi chahiye?
4. Caching cost reduce karte hue stale output ka risk kab create karti hai?
5. **requests.nvidia.com/gpu** quota namespace mein kya limit karti hai?
6. GPU Pod Pending ho to insufficient GPU resource aur missing allocatable GPU ko kaise differentiate karoge?

## References

- https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/
- https://kubernetes.io/docs/concepts/policy/resource-quotas/
- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://kubernetes.io/docs/concepts/containers/images/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/caching/
- https://opentelemetry.io/docs/concepts/signals/
