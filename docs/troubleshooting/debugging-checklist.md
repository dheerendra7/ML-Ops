# Debugging Checklist: Evidence se Start Karo

> Debugging ka aim random changes try karna nahi hai. Pehle symptom ko narrow karo, evidence collect karo, ek hypothesis test karo, aur har change ka before/after result note karo.

## 5-minute approach

1. **Symptom ko exact bolo:** Pod **Pending** hai, container **CrashLoopBackOff** mein hai, image pull fail ho raha hai, task fail hui, ya artifact nahi mila?
2. **Context verify karo:** active cluster, namespace, object name aur resource type.
3. **Status aur events padho:** Kubernetes aksar pehla useful clue event mein deta hai.
4. **Logs aur effective configuration inspect karo:** Pod spec, resource requests/limits, command, image, identity aur inputs/outputs.
5. **Ek waqt mein ek change karo:** change ka reason aur expected result pehle likho.
6. **Verify aur record karo:** symptom resolve hua ya sirf aage shift ho gaya? versions aur evidence save karo.

## 1. Pehle context aur scope verify karo

~~~bash
kubectl config current-context
kubectl get pods -A
kubectl get namespaces
kubectl get events -n <namespace> --sort-by=.lastTimestamp
~~~

**-A** cluster-wide output deta hai aur noisy ho sakta hai. Shared cluster mein sirf woh resources inspect karo jinhe access karne ki permission hai. Agar cluster context galat hai, aage ke commands wrong environment ko affect kar sakte hain.

## 2. Quick diagnostic commands

~~~bash
kubectl get pod <pod-name> -n <namespace> -o wide
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --all-containers=true
kubectl logs <pod-name> -n <namespace> --previous
kubectl get events -n <namespace> --sort-by=.lastTimestamp
~~~

- **describe** status, conditions, recent events aur scheduling/termination clues dikhata hai.
- **logs** container output dikhata hai; **--previous** previous terminated container instance ke logs maangta hai.
- **--previous** tabhi useful output dega jab previous container instance/logs available hon.
- Logs sensitive ho sakte hain. Public issue mein share karne se pehle tokens, credentials, private URLs, user data aur secrets redact karo.

## 3. Symptom map

| Symptom | Pehle kya check karna hai | Typical next step |
|---|---|---|
| **Pending** | **describe pod** output aur scheduling events | CPU/memory requests, ResourceQuota, node capacity, affinity, taints/tolerations, PVC binding |
| **CrashLoopBackOff** | Current/previous logs, exit reason/code, startup command, config aur probes | Startup error ko isolate karo; probe failure aur application crash ko alag samjho |
| **ImagePullBackOff** | Image name/tag/digest, event message, registry reachability aur pull credentials | Registry access aur image reference verify karo; secret value kabhi log/share mat karo |
| **Forbidden** | Current identity, namespace, requested API verb/resource aur RoleBindings | Intended permission confirm karo; cluster admin se least-privilege correction maango |
| **Pod create nahi hota** | API error, ResourceQuota, LimitRange, admission policy | Namespace, missing resources, min/max aur aggregate quota inspect karo |
| **Pipeline task failed** | Task state/logs, runtime image, dependencies, inputs/outputs aur service identity | Compile/submission problem ko runtime task failure se separate karo |
| **Artifact missing** | Previous task completion, declared output, artifact URI/store aur permissions | Local container path ko shared artifact storage assume mat karo |
| **Run pass hua par model bad hai** | Evaluation metrics, validation data, baseline aur promotion gate | Pipeline success ko model-quality approval ke equivalent mat samjho |

## 4. Symptom-wise commands

### Scheduling / quota clues

~~~bash
kubectl describe pod <pod-name> -n <namespace>
kubectl describe resourcequota -n <namespace>
kubectl describe limitrange -n <namespace>
kubectl describe nodes
~~~

Agar event **Insufficient cpu** bole to node capacity aur requests check karo. Agar API creation error quota exceed bole to namespace ke **Used/Hard** values inspect karo. Ye dono alag stages hain: admission par quota object reject kar sakti hai; admitted Pod baad mein scheduler par bhi fail ho sakta hai.

### Crash ya restart

~~~bash
kubectl logs <pod-name> -n <namespace> --all-containers=true
kubectl logs <pod-name> -n <namespace> --previous
kubectl describe pod <pod-name> -n <namespace>
~~~

Container termination reason, exit code, probe failures, required environment/config aur recent rollout changes compare karo. OOM suspicion ho to memory request/limit, termination reason aur available usage metrics inspect karo.

### Permission issue

~~~bash
kubectl auth can-i get pods -n <namespace>
kubectl auth can-i create pods -n <namespace>
kubectl get rolebindings -n <namespace>
kubectl get serviceaccounts -n <namespace>
~~~

**kubectl auth can-i** current kubeconfig identity ki API permission test karta hai. Workload service account ya doosre user ki access alag ho sakti hai. Test identity/impersonation use karne se pehle required authorization confirm karo; permission error ko broad ClusterRoleBinding add karke hide mat karo.

## 5. Kubeflow/KFP failures ko layers mein divide karo

1. **Authoring/compile:** SDK version, import, type/annotation ya pipeline definition problem?
2. **Submission/backend:** endpoint, auth, run configuration ya platform permission problem?
3. **Task startup:** image pull, container command, dependencies ya service account problem?
4. **Task execution:** code exception, bad input, memory/CPU pressure, external service ya data access problem?
5. **Output/artifact:** task ne expected output banaya? Output declare/upload hua? Agla task sahi reference aur permission use kar raha hai?

Har layer ke evidence ko saath record karo. Sirf top-level "pipeline failed" message root cause nahi batata.

## 6. Safe debugging habits

- Read-only commands se start karo; deletion, restart, quota change ya permissions change ka impact samjhe bina run mat karo.
- Kubeconfig, bearer tokens, cloud credentials, secrets ya sensitive logs public issues/commits mein mat paste karo.
- Kubernetes, Kubeflow, KFP SDK aur cluster installation versions record karo.
- Event/log timestamps aur failing run ID note karo.
- Hypothesis aur expected result likho; ek baar mein ek change test karo.
- Recovery step aur rollback path samjho, khaaskar shared environments mein.
- Agar evidence inconclusive ho, random configuration edits ke bajay smallest reproducible case banao.

## 7. Incident note template

Issue resolve karne ke liye ye information kaafi useful hoti hai. Secrets aur private data include mat karo.

~~~text
Symptom:
First seen (timestamp/timezone):
Cluster and namespace:
Kubernetes / Kubeflow / KFP versions:
Affected Pod or run ID:
Exact sanitized error/event:
What changed recently:
Hypothesis:
One change tested and observed result:
Current impact:
Next safe action / owner:
~~~

## Recall questions

1. Pod create reject hona aur Pod **Pending** rehna kaise different hain?
2. Current logs aur previous container logs kab use karoge?
3. Pipeline task failure ko kaun-si five layers mein isolate kar sakte ho?
4. Kyu kubeconfig/token ko issue report mein include nahi karna chahiye?
5. Model ki pipeline green hone ke baad bhi evaluation gate kyun chahiye?

## References

- https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_describe/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
