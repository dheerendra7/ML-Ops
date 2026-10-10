# Kubernetes Resource Controls: Requests, Limits, ResourceQuota, and LimitRange

> Is lesson ka goal sirf definitions yaad karna nahi hai. Tumhe samajhna hai ki Pod schedule kyun nahi hota, container ko CPU kyun slow mil sakta hai, memory OOM kyun ho sakti hai, aur namespace ki quota policy Pod create hone se pehle kaise effect karti hai.

## 5-minute snapshot

- **Resource request** scheduler ko batata hai ki workload ke liye kitni CPU/memory capacity plan karni hai.
- **Resource limit** container ke resource use par upper bound set karta hai. CPU limit ke paas pahunchne par throttling ho sakti hai; memory limit cross hone par container OOM termination ka shikar ho sakta hai.
- **ResourceQuota** ek namespace ke andar aggregate budget ya object-count cap define karta hai.
- **LimitRange** individual container/Pod/PVC ke liye, configured type ke hisaab se, defaults, minimums aur maximums set kar sakta hai.
- **Namespace akela complete security boundary nahi hai.** RBAC aur doosre controls ki zaroorat phir bhi hoti hai.

Ye chaar controls alag problems solve karte hain; inhe interchangeable mat samajhna.

## 1. Mental model

Ek namespace ko team ka shared resource budget samjho.

- **Request**: workload ke liye planning/scheduling mein kitni capacity consider karni hai.
- **Limit**: ek container resource ka kitna use kar sakta hai, us par configured boundary.
- **ResourceQuota**: poori team ka total budget.
- **LimitRange**: ek individual container ke liye default aur allowed range.

Example: agar namespace ka total CPU-request quota **500m** hai, to **250m** request karne wale do Pods total **500m** request budget consume kar lenge. Teesre Pod ka **250m** request us quota ko cross karega, bhale hi cluster mein free CPU ho.

## 2. Requests aur limits ka difference

| Resource field | Kya karta hai | Kya guarantee nahi karta |
|---|---|---|
| CPU request | Scheduler placement aur resource accounting mein use hota hai | Workload ko har waqt utni CPU usage milne ki guarantee nahi deta |
| CPU limit | CPU use ko configured ceiling ke andar regulate karta hai; contention par throttling ho sakti hai | Ye CPU request ka replacement nahi hai |
| Memory request | Scheduler ko workload ke memory requirement ka estimate deta hai | Ye container ki hard memory ceiling nahi hai |
| Memory limit | Container ke memory use ki upper boundary set karta hai | Bad allocation ya memory pressure ka complete solution nahi hai |

### Units ko samjho

- **1000m CPU = 1 CPU**.
- **250m CPU = 0.25 CPU**.
- Memory quantities jaise **128Mi**, **512Mi**, **1Gi** commonly use hoti hain; **1Gi = 1024Mi**.
- Bahut high request scheduler ko suitable node dhoondhne mein fail kara sakta hai, isliye Pod **Pending** reh sakta hai.
- Memory limit cross hone par process/container OOM termination ka shikar ho sakta hai. Actual diagnosis ke liye Pod status aur events dekho; sirf restart count dekhkar conclusion mat nikalo.

CPU/memory values workload measurement, testing, latency aur cost constraints se choose karo. Is repo ke example values learning exercise ke liye hain, sizing recommendations nahi.

## 3. ResourceQuota: namespace ka aggregate budget

ResourceQuota namespace ke andar total resource consumption aur kuch Kubernetes objects ki count ko bound kar sakta hai. Is repo ke example mein:

- total CPU requests ka budget **500m**;
- total memory requests ka budget **1Gi**;
- total CPU limits ka budget **2**;
- total memory limits ka budget **2Gi**;
- namespace ke andar Pods ki count **5**.

Actual values [ResourceQuota manifest](../../examples/resource-policies/resource-quota.yaml) mein hain.

Quota usage check karo:

~~~bash
kubectl describe resourcequota team-resource-budget -n mlops-lab
kubectl get resourcequota team-resource-budget -n mlops-lab -o yaml
~~~

Output mein **Used** aur **Hard** values compare karo. **Used** budget ke barabar ho, to us quota dimension mein aur usage add karne wala object reject ho sakta hai. Exact error wording Kubernetes version aur object ke hisaab se vary kar sakti hai.

**Important admission detail:** agar quota CPU/memory requests ya limits ko track karti hai, to naye Pods ko un fields ki values provide karni hoti hain. Values explicit spec mein ho sakti hain ya configured LimitRange defaults se fill ho sakti hain. Isliye quota aur LimitRange ek saath configure karna useful hai.

## 4. LimitRange: individual object ke defaults aur bounds

LimitRange, selected **type** ke liye, minimum/maximum constraints aur defaults define kar sakta hai. Is repo ka manifest **type: Container** use karta hai; isliye example per-container resources par focus karta hai.

- **defaultRequest**: request omit hone par default request.
- **default**: resource limit omit hone par default limit.
- **min / max**: individual container ke liye allowed resource range.

Actual values [LimitRange manifest](../../examples/resource-policies/limit-range.yaml) mein hain.

Check karo:

~~~bash
kubectl describe limitrange container-resource-defaults -n mlops-lab
kubectl get limitrange container-resource-defaults -n mlops-lab -o yaml
~~~

LimitRange **total namespace budget nahi** hai. Agar har container ke liye **500m** tak ka limit allowed hai, iska matlab ye nahi ki poora namespace sirf **500m** consume kar sakta hai; aggregate budget ke liye ResourceQuota alag hai.

Defaults admission ke waqt object mein apply ho sakte hain. Agar tumne Pod spec mein resources nahi likhe, to live Pod object inspect karo—assumption ke bajay API se admitted configuration dekho.

## 5. Dono ko saath kyun use karein?

| Question | Control |
|---|---|
| Ek namespace total kitna CPU/memory request ya limit kar sakta hai? | ResourceQuota |
| Namespace mein kitne Pods ho sakte hain? | ResourceQuota |
| Container resources omit kare to default kya lagna chahiye? | LimitRange |
| Ek container ka minimum/maximum resource value kya allowed hai? | LimitRange |
| Pod ko node par schedule karne ke liye resources available hain? | Scheduler, requests, node capacity aur doosre constraints |

In controls ke saath bhi RBAC, network policy, Pod Security standards aur platform-specific controls ko alag review karna hota hai.

## 6. Practical debugging checklist

### Pod **Pending** mein hai

~~~bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
kubectl describe nodes
~~~

Pod events mein **FailedScheduling** aur **Insufficient cpu** / **Insufficient memory** jaise messages dekho. High requests ek possible cause hain; node selectors, taints/tolerations, affinity aur cluster capacity bhi check karo.

### Pod creation quota ki wajah se fail hua

~~~bash
kubectl describe resourcequota -n <namespace>
kubectl get pods -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
~~~

Manifest mein **metadata.namespace**, ResourceQuota name, request/limit quantities aur current **Used** values verify karo. Kisi shared namespace mein quota delete/relax karke troubleshoot karna safe shortcut nahi hai—cluster owner se policy change approve karwao.

### Container **OOMKilled** hai

~~~bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
~~~

Container ka termination reason, recent logs, memory usage pattern aur configured request/limit dekho. Agar container previous run ki logs nahi rakhta, **--previous** output available na bhi ho sakta hai. Randomly limit badhane ke bajay workload ka memory profile samjho.

### Container CPU-bound ya slow hai

Container ka configured CPU limit, CPU throttling/usage metrics, application latency aur node contention observe karo. Sirf CPU request badha dena har performance issue ka fix nahi hai. Metrics availability monitoring stack par depend karti hai.

## 7. Hands-on practice

[Lab 01 — Kubernetes resource governance](../labs/resource-governance.md) follow karo. Usmein disposable namespace, server-side dry run, ResourceQuota/LimitRange apply, expected quota rejection, defaults inspect karna, troubleshooting aur cleanup ke steps diye gaye hain.

Server-side dry run API server se validation karwata hai, bina object persist kiye; lekin ye prove nahi karta ki Pod schedule ho jayega ya production workload stable hoga.

## 8. Common mistakes

- Request aur limit ko same cheez samajhna.
- CPU request badhakar memory OOM issue solve karne ki koshish karna.
- Sochna ki cluster mein free capacity hai, isliye quota reject nahi ho sakti.
- LimitRange defaults ko check kiye bina assume karna ki Pod mein koi requests/limits set nahi hain.
- Manifest ek namespace mein apply karna aur debugging doosre namespace mein karna.
- Quota values ko real workload measurement ke bina production mein copy kar dena.
- Namespace isolation ko RBAC/network/security controls ka replacement samajhna.

## 9. Recall questions

1. ResourceQuota aur LimitRange mein main difference kya hai?
2. **250m** CPU ka kya matlab hai?
3. CPU limit ke paas container ko throttling kyun ho sakti hai, aur memory limit ke case mein OOM termination ka risk kyun hota hai?
4. Agar quota ke **Used** requests budget ke equal hain to next similar Pod ke saath kya ho sakta hai?
5. Pod create ho gaya lekin **Pending** hai—kaun-se do areas alag-alag investigate karoge?
6. LimitRange defaults verify karne ke liye submitted manifest ke bajay admitted Pod object inspect kyun karna chahiye?

## References

- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://kubernetes.io/docs/concepts/policy/resource-quotas/
- https://kubernetes.io/docs/concepts/policy/limit-range/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_apply/
- https://kubernetes.io/docs/reference/kubectl/generated/kubectl_run/
