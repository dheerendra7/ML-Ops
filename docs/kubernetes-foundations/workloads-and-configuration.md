# Kubernetes Workloads and Configuration: Pod, Job, Deployment, Service, ConfigMap, Secret

> MLOps mein har task ek tarah ka workload nahi hota. Training/preprocessing jaisa kaam complete hoke exit ho sakta hai; model-serving endpoint ko continuously available rehna hota hai. Sahi Kubernetes object choose karne se retries, rollout, networking aur debugging ka behavior predictable hota hai.

## 5-minute snapshot

- **Pod:** Kubernetes ka smallest schedulable workload unit; ek ya zyada closely-coupled containers run karta hai.
- **Job:** finite task ko completion tak run karne ke liye controller. Batch/preprocessing/smoke-test jobs ke liye useful.
- **Deployment:** long-running stateless workload ke replicas aur rollout lifecycle ko manage karta hai.
- **Service:** selected Pods ko stable network endpoint/DNS abstraction deta hai; ye app ko expose karne ki policy aur service type par depend karta hai.
- **ConfigMap:** non-sensitive configuration ko image se alag rakhta hai.
- **Secret:** sensitive values ke liye Kubernetes object; base64 encoding ko encryption mat samjho. Access control aur encryption-at-rest configuration separately review karo.

Ye objects ek doosre ke replacements nahi hain; practical application mein ek saath bhi use ho sakte hain.

## 1. Pod vs Job vs Deployment

| Object | Kab choose karein | Lifecycle |
|---|---|---|
| Bare Pod | Learning, diagnostics, ya jab higher-level controller ki zaroorat na ho | Pod fail/delete ho to higher-level controller ke bina desired replacement lifecycle manage nahi hota |
| Job | One-off task jo successful completion ke baad finish hona chahiye | Job failed attempt par configured retry behavior follow kar sakta hai; success/failure status track hota hai |
| CronJob | Recurring scheduled batch task | Schedule ke mutabik Jobs create karta hai; overlap, deadlines aur missed schedule policy review karni hoti hai |
| Deployment | Long-running app/service | Desired replicas, replacements aur rolling updates manage karta hai |

Rule of thumb: **finite computation → Job; continuously running stateless service → Deployment**. Actual ML pipeline task ka backend implementation KFP version/configuration par depend karta hai; is table ka matlab ye nahi ki har KFP component direct ek Kubernetes Job hi hoga.

## 2. Example: finite task ke liye Job

Repo ke [handbook smoke Job manifest](../../examples/workloads/handbook-smoke-job.yaml) mein ek lightweight Python container short message print karta hai aur exit hota hai. Ye learning/smoke-test example hai—actual training code nahi.

Pehle cluster context verify karo aur dedicated namespace ka use karo:

~~~bash
kubectl config current-context
kubectl get namespace mlops-lab
~~~

Agar namespace existing hai, verify karo ki wo disposable aur tumhare control mein hai. Shared/production namespace ko reuse mat karo. Fresh lab namespace chahiye to, active context confirm karne ke baad:

~~~bash
kubectl create namespace mlops-lab
~~~

Manifest ko API server par validate karo, bina resource persist kiye:

~~~bash
kubectl apply --dry-run=server -f examples/workloads/handbook-smoke-job.yaml
~~~

Agar server-side dry run successful ho aur manifest ka namespace sahi ho, tabhi Job create karo:

~~~bash
kubectl apply -f examples/workloads/handbook-smoke-job.yaml
kubectl get jobs,pods -n mlops-lab
kubectl describe job handbook-smoke-job -n mlops-lab
kubectl logs job/handbook-smoke-job -n mlops-lab
~~~

Expected behavior: Job successful completion report kare aur logs mein smoke-test message ho. Exact Pod state/timing cluster scheduling aur image-pull conditions par depend karega. Agar Job **Failed** ya Pod **Pending** ho, pehle **describe job**, **describe pod** aur namespace events inspect karo.

**Important:** server-side dry run API server se validation karwata hai, bina object persist kiye; ye guarantee nahi deta ki container image pull hogi, node resources available honge ya task successful hoga.

## 3. Deployment aur Service ka difference

Deployment desired replicas aur rolling updates manage karta hai. Service selected Pods ko stable endpoint provide kar sakti hai, even jab Pod names/IPs replace hote rahein.

Conceptually:

~~~text
Client
  |
  v
Service (stable endpoint)
  |
  +----> Pod replica A (managed by Deployment)
  |
  +----> Pod replica B (managed by Deployment)
~~~

Service tabhi useful endpoint banegi jab selector expected Pod labels se match kare aur app container required port par listen kare. Service create karna khud se public internet exposure guarantee nahi karta; ClusterIP, NodePort, LoadBalancer, Ingress/Gateway aur cluster networking configuration ka role alag hai.

Model serving ke liye readiness/liveness probes, resource requests/limits, graceful shutdown, replica strategy aur traffic exposure ko separately design karo.

## 4. ConfigMap: non-sensitive configuration

ConfigMap app configuration ko image ke andar hard-code karne se bachata hai. Examples: non-secret log level, feature name, ya harmless mode switch.

ConfigMap ko environment variables ya mounted files ke through consume kiya ja sakta hai, depending on workload design. Environment variable ke roop mein inject ki gayi values existing process mein automatically refresh nahi hoti; change rollout/restart strategy ka part ho sakta hai. App behavior ko verify karo rather than assume a config change took effect.

Passwords, private keys, tokens ya credential values ko ConfigMap mein mat rakho.

## 5. Secret: data ko sensitive treat karo

Kubernetes Secret object sensitive values carry kar sakta hai, lekin sirf Secret type use karna complete security plan nahi hai.

- Secret manifests mein actual credentials GitHub par commit mat karo.
- Base64 encoding **encryption nahi** hai.
- RBAC access ko minimum required users/service accounts tak restrict karo.
- Encryption at rest, API audit policy, backups aur secret rotation deployment/configuration par depend karte hain.
- Workload ko sirf required secret/credential access do; secret ko command-line args ya logs mein expose mat karo.
- Production mein organization-approved secret manager ya external integration prefer ho sakti hai.

Exact secret delivery method platform/version ke hisaab se verify karna hoga. Handbook mein koi real credential sample intentionally include nahi hai.

## 6. Common debugging paths

| Symptom | First checks |
|---|---|
| Job create nahi hota | API error, namespace, ResourceQuota, LimitRange, admission policy |
| Job created but Pod Pending | Scheduling events, requests, node capacity, taints/affinity |
| Job repeatedly fails | Job status, Pod events, container exit code, logs, bounded retry policy |
| Deployment rollout stuck | Deployment/ReplicaSet/Pod conditions, readiness probe, image pull, events |
| Service has no working endpoint | Selector/Pod labels, readiness, target port, app listening port, NetworkPolicy |
| Config change ignored | ConfigMap reference/mount, process refresh behavior, rollout/restart |
| Secret access denied | Service account, RoleBindings, secret namespace/name, secret integration configuration |

First inspect current evidence. Randomly delete Pods or widen permissions as the first debugging step mat banao.

## 7. Cleanup

Agar tumne namespace sirf is lab ke liye create kiya tha aur verify kar liya hai ki usmein koi doosre required resources nahi hain, to poora namespace delete kar sakte ho:

~~~bash
kubectl delete namespace mlops-lab
~~~

Namespace deletion uske andar ke resources ko bhi delete karegi. Shared namespace mein ye command blindly mat run karna.

## 8. Recall questions

1. Bare Pod aur Job ke lifecycle mein kya difference hai?
2. Long-running app ke liye Deployment kyun, aur one-off task ke liye Job kyun useful hai?
3. Service ka stable endpoint Pod IP/name ke comparison mein kya value deta hai?
4. ConfigMap aur Secret mein kya difference hai?
5. Secret ka base64 encoded hona encryption ke barabar kyun nahi hai?
6. Server-side dry run pass hone ke baad bhi Job fail kyun ho sakta hai?

## References

- https://kubernetes.io/docs/concepts/workloads/pods/
- https://kubernetes.io/docs/concepts/workloads/controllers/job/
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- https://kubernetes.io/docs/concepts/services-networking/service/
- https://kubernetes.io/docs/concepts/configuration/configmap/
- https://kubernetes.io/docs/concepts/configuration/secret/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/
