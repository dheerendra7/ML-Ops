# Kubeflow Profiles, Kubernetes Namespaces, aur Isolation

> Is guide ka main point: **Profile, Namespace aur RBAC ek hi cheez nahi hain.** Ye alag layers par kaam karte hain, aur multi-user Kubeflow platform ko safe rakhne ke liye inke behavior ko installed environment mein verify karna zaroori hai.

## 5-minute snapshot

- **Namespace** Kubernetes ka namespaced objects ko scope karne ka mechanism hai. Policies aur team/resource administration mein useful hai.
- **Profile** Kubeflow-specific custom resource hai jo supported multi-user installations mein user/workspace abstraction represent kar sakta hai. Kuch setups mein controller Profile ke basis par namespace aur related resources provision karta hai.
- **RBAC** identity ko batata hai ki Kubernetes API par kaun-se actions allowed hain.
- **ResourceQuota / LimitRange** resource budget aur per-object defaults/constraints ke liye hain.
- **Network policies, Pod Security aur storage/secret permissions** additional isolation layers provide kar sakte hain.

Profile ke fields, creation behavior, namespace mapping aur installed controllers release/configuration ke hisaab se change ho sakte hain. Vanilla Kubernetes cluster mein Kubeflow Profile resource zaroori nahi ki available ho.

## 1. Mental model

Ek multi-user ML platform mein sawal sirf "user ka namespace kya hai?" nahi hota. Kam se kam ye alag sawal answer hone chahiye:

1. User ko platform kis identity se pehchanta hai?
2. Us identity ko kaunsa workspace/Profile diya gaya hai?
3. Profile ka namespace ya owned resources kaise provision hote hain?
4. Identity namespace mein kaun-se API actions kar sakti hai?
5. User ke workloads doosre users, secrets, storage, services aur network endpoints tak kahan tak pahunch sakte hain?

In sawalon ko ek hi Kubernetes object se solve assume mat karo.

## 2. Har concept ka role

| Concept | Responsibility | Iska matlab ye nahi |
|---|---|---|
| Kubeflow Profile | Supported Kubeflow multi-user setup mein user/workspace abstraction | Vanilla Kubernetes ka built-in resource nahi; har installation same behavior guarantee nahi karti |
| Kubernetes Namespace | Namespaced objects ko organize/scope karna aur namespace-scoped policies apply karna | Apne aap network traffic ya har cluster-wide resource ko isolate nahi karta |
| RBAC Role / RoleBinding | Namespace scope mein defined API permissions grant karna | Application ke andar data authorization ya network access automatically control nahi karta |
| ClusterRole / ClusterRoleBinding | Cluster-level ya reusable permissions ko bind karna | Har user ko cluster-wide permission dena safe nahi banata |
| ResourceQuota / LimitRange | Aggregate budget / individual object constraints | Identity authorization ya full tenant isolation ka replacement nahi |
| NetworkPolicy / Pod Security / storage policy | Traffic aur workload/data access ko deployment ke hisaab se constrain karna | Ye controls tabhi effective hain jab required platform support aur policy enforcement configured ho |

## 3. Profile behavior version-dependent kyun hai?

Profile Kubernetes Custom Resource Definition (CRD) aur usko reconcile karne wale controller par depend kar sakta hai. CRD available ho, tab bhi controller ki configuration decide karti hai ki namespace, role bindings, default resources ya related objects kaise manage honge.

Isliye deploy karne se pehle:

- installed Kubeflow release aur enabled components identify karo;
- Profile CRD aur controller actually installed hain ya nahi check karo;
- installed release ke official documentation/manifests ke saath fields aur lifecycle verify karo;
- profile create/update/delete karne par kaun-se resources provision ya modify honge samjho;
- upgrades ke baad behavior dobara verify karo.

Kisi blog post ya doosre cluster se copied Profile YAML ko universal config mat samjho.

## 4. Read-only inspection

Pehle cluster context aur namespaces inspect karo:

~~~bash
kubectl config current-context
kubectl get namespaces
kubectl get namespace <namespace> -o yaml
~~~

Kubeflow Profile resource check karo:

~~~bash
kubectl get profiles -A
kubectl describe profile <profile-name>
~~~

Agar command kahe ki resource type unknown/not found, to zaroori nahi ki cluster broken hai. Ho sakta hai Profile CRD installed na ho, resource name/release alag ho, ya tumhare account ke paas permission na ho. API resource list aur cluster admin ke saath installed CRD/component verify karo. Unknown state mein Profile create karne ki koshish mat karo.

Namespace-scoped permissions aur service accounts inspect karo:

~~~bash
kubectl get rolebindings,serviceaccounts -n <namespace>
kubectl get resourcequota,limitrange -n <namespace>
kubectl auth can-i list pods -n <namespace>
~~~

**kubectl auth can-i** current kubeconfig identity ke liye API permission check karta hai. Cross-user testing karni ho to non-privileged test identity use karo; **--as** impersonation sirf tab use karo jab tumhare account ko explicitly permission mili ho. Production users ke permissions ko test karne ke liye privileged personal identity se shortcuts mat lo.

## 5. Isolation review checklist

Multi-user environment mein deploy/upgrade se pehle ye items evidence ke saath verify karo:

1. **Identity mapping:** identity provider/user claims ko Kubeflow user/Profile/workspace se kaise map kiya jata hai?
2. **Ownership lifecycle:** kaun Profile create kar sakta hai? Namespace aur RoleBinding create/update/delete ka owner kaun hai?
3. **RBAC least privilege:** users aur service accounts ke Roles/RoleBindings mein required API verbs hi hain?
4. **Namespace scope:** workloads expected namespace mein hi hain? Cluster-scoped resources ke permissions alag review hue?
5. **Resource governance:** ResourceQuota aur LimitRange configured hain? Defaults aur rejected workload ka behavior test hua?
6. **Network access:** Kya cross-namespace traffic block karna chahiye? NetworkPolicy enforce karne wala CNI/policy engine available aur configured hai?
7. **Secrets and storage:** doosre workspace ke secrets, volumes, object storage paths, credentials ya datasets ka access test hua?
8. **Pod/workload security:** Pod Security settings, service accounts, privilege escalation aur image policy review hui?
9. **Negative tests:** restricted test identity se doosre namespace ke Pods/secrets read karne ki koshish expected outcome deti hai?
10. **Upgrade plan:** version change ke baad Profile controller, RBAC aur namespace policies verify karne ka repeatable checklist hai?

Namespace create ho jana isolation ka proof nahi hai. Explicit allow/deny tests aur policy evidence record karo.

## 6. Common symptoms aur diagnosis

| Symptom | Possible explanation | Next check |
|---|---|---|
| **profiles** resource not found | CRD absent, name/version mismatch, ya discovery/permission issue | API resources, installed Kubeflow release aur CRD/controller configuration |
| User ko namespace dikh raha hai, but Pod create nahi kar pa raha | RBAC permission, quota, LimitRange ya admission policy | API error, RoleBindings, quota usage aur namespace events |
| User doosre namespace ke objects read kar sakta hai | RBAC grants wider than intended | User/group bindings aur effective API permissions review karo |
| Pod doosre workload ko network par reach kar pa raha hai | NetworkPolicy absent/not enforced, ya policy allow karti hai | CNI support, NetworkPolicy objects aur controlled connectivity test |
| Profile/namespace expected se alag provision hua | Controller/config/release behavior mismatch | Controller logs/events aur installed version ke source manifests |

**Forbidden** error ko bypass karne ki koshish mat karo. Pehle identity aur intended permission confirm karo; admin approval ke bina wide bindings add karna safe fix nahi hai.

## 7. Lab ka next step

Resource budgets ko separately verify karne ke liye [Lab 01 — Kubernetes resource governance](../labs/resource-governance.md) complete karo. Wo lab namespace-level ResourceQuota, per-container LimitRange, admission behavior aur cleanup cover karta hai. Ye Profile controller ya cross-tenant security ko prove nahi karta; woh installation-specific follow-up test hai.

## 8. Recall questions

1. Profile aur Namespace mein kya difference hai?
2. RBAC API permissions control karta hai; kya woh apne aap network traffic block karta hai?
3. Profile CRD install na ho to Profile-list command se kya conclusion nikalna chahiye?
4. Namespace existence isolation ke proof ke liye sufficient kyun nahi hai?
5. Cross-tenant test ke liye privileged personal identity use karna risky kyun hai?
6. Kubeflow upgrade ke baad kaun-se Profile/RBAC/isolation behaviors re-verify karoge?

## References

- https://www.kubeflow.org/docs/components/central-dash/profiles/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- https://kubernetes.io/docs/concepts/policy/resource-quotas/
- https://kubernetes.io/docs/concepts/policy/limit-range/
