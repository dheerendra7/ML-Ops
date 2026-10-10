# MLOps Production-Readiness Checklist

> Is checklist ko review gate ke roop mein use karo, certification ke roop mein nahi. Requirements model ke risk, workload, organization aur deployment environment par depend karti hain. Sirf pipeline ka green hona production readiness ka proof nahi hai.

## Is checklist ko kaise use karein

Har relevant item par evidence identify karo—jaise evaluation report, artifact URI, security review, monitoring dashboard, rollback exercise ya named owner. Agar item applicable nahi hai, reason likho aur reviewer se agree karo. High-risk unresolved issue ko sirf checkbox tick karke close mat karo.

Suggested review record:

| Field | Record |
|---|---|
| Model / pipeline version | Source commit, pipeline version, model/artifact identifier |
| Intended use | Users, target workflow, known limitations |
| Review owner | Responsible person/team |
| Evidence links | Sanitized evaluation, security and operational evidence |
| Decision | Promote / hold / reject |
| Rollback owner and trigger | Who acts and which signals trigger rollback |

## 1. Reproducibility and traceability

- [ ] Source code commit, pipeline definition, dependencies and container images versioned hain.
- [ ] Jahan practical ho, image digest aur dependency lockfiles record hote hain; mutable tags par akela depend nahi karte.
- [ ] Training dataset, feature inputs aur relevant preprocessing version/identity se traceable hain.
- [ ] Random seeds aur known nondeterministic steps document kiye gaye hain.
- [ ] Run output ke saath metrics, configuration aur metadata store hote hain, taaki result audit/reproduce kiya ja sake.
- [ ] Pipeline retry/re-run se external side effects (duplicate upload, billing action, registry publish) ka risk review hua hai.

**Evidence example:** source commit + input data version + image digest + run ID + output artifact/metrics record.

## 2. Model and data quality

- [ ] Evaluation strategy task ke risk aur data structure ke hisaab se appropriate hai.
- [ ] Baseline aur acceptance thresholds model promotion se pehle define kiye gaye hain.
- [ ] Data leakage, class imbalance, missing values aur distribution differences consider kiye gaye hain.
- [ ] Relevant subgroup performance aur likely failure cases review hue hain.
- [ ] Evaluation result invalid/missing ho ya threshold fail ho to promotion block hota hai.
- [ ] Dataset provenance, label quality aur evaluation data train data se appropriately separated hain.
- [ ] Human review ya additional approval jahan required hai, documented hai.

**Decision rule:** "Training task successful" aur "model acceptable" alag outcomes hain. Promotion gate ko metrics/data evidence evaluate karna chahiye, sirf exit code nahi.

## 3. Security and access

- [ ] User, service account aur workload identities least privilege follow karti hain.
- [ ] Secrets approved secret-management/injection mechanism se aate hain; source code, image layers, ordinary parameters ya logs mein nahi.
- [ ] Image provenance, vulnerability scanning, dependency updates aur base-image lifecycle covered hain.
- [ ] Private registry, object storage, database aur external service permissions reviewed hain.
- [ ] Network paths, namespace boundaries, RoleBindings/ClusterRoleBindings aur tenant access test hue hain.
- [ ] Sensitive data logs, artifacts aur issue reports mein leak nahi hota.
- [ ] Required Pod Security / admission policies aur cluster-specific controls verified hain.

## 4. Reliability and resource governance

- [ ] CPU/memory requests aur limits measured workload needs aur latency/cost trade-offs par based hain.
- [ ] Namespace ResourceQuota aur applicable LimitRange policies inspect/test ki gayi hain.
- [ ] Pending Pods, OOM termination, image pull failures, storage errors aur API permission failures ke runbooks available hain.
- [ ] Retry count bounded hai; retries idempotency aur duplicate side effects ko consider karte hain.
- [ ] Timeout, cancellation aur partial failure behavior understood hai.
- [ ] Logs, key metrics, alerts aur pipeline/run ownership defined hain.
- [ ] Backup/restore, recovery, rollback aur incident response process test hua hai.
- [ ] Kubernetes, Kubeflow/KFP, images aur critical dependencies upgrade/compatibility plan ke saath maintain hote hain.

## 5. Monitoring after release

- [ ] Infrastructure health ke saath application/task success, latency aur failure rates monitor hote hain.
- [ ] Relevant model/data signals (quality, drift, input distribution, delayed labels, as applicable) monitor hote hain.
- [ ] Alert ka owner, response expectation aur escalation path documented hai.
- [ ] Monitoring data ki retention aur privacy controls defined hain.
- [ ] Rollback/retraining decision thresholds practical evidence par based hain, sirf arbitrary alerts par nahi.
- [ ] Released model/version aur active production traffic ka mapping available hai.

## 6. Governance and ownership

- [ ] Model owner, intended users, purpose, limitations aur out-of-scope use documented hain.
- [ ] Data retention, lineage, privacy constraints aur access policies understood hain.
- [ ] Promotion decision aur approver auditable hain.
- [ ] Known risks, open issues aur residual risk acceptance owner ke saath recorded hain.
- [ ] Change ke baad re-evaluation/re-approval kab chahiye, define hai.
- [ ] Decommissioning, artifact retention aur access revocation process available hai.

## 7. Go / hold / no-go gate

### Go only when

- required model/data quality checks pass;
- no unresolved release-blocking security issue remains;
- monitoring and ownership are in place;
- rollback or recovery path is known and tested to the level appropriate for the risk;
- accountable reviewer promotion approve karta hai.

### Hold or reject when

- evaluation evidence missing hai ya agreed threshold fail hai;
- identity, secret handling ya data access unclear hai;
- output/artifact provenance verify nahi ho pa rahi;
- failure detect karne, impact limit karne ya rollback karne ka credible plan nahi hai;
- unresolved risk owner/approver ne accept nahi kiya.

## 8. Questions for the release review

1. Kya doosra engineer source, data version, dependencies aur model artifact trace kar sakta hai?
2. Model threshold fail hone par automatic promotion sach mein rukti hai?
3. Kaun-si identity data/model artifacts access kar sakti hai, aur kyun?
4. Pod/Pipeline failures detect aur diagnose karne ke liye kya evidence available hoga?
5. Rollback trigger kya hai aur use kaun execute karega?
6. Deployment ke baad model/data behavior mein change kaise detect hoga?

[Debugging checklist](../troubleshooting/debugging-checklist.md) operations ke liye aur [resource-governance lab](../labs/resource-governance.md) namespace budgets/defaults ke hands-on practice ke liye use karo.

## References

- https://www.kubeflow.org/docs/
- https://kubernetes.io/docs/concepts/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- https://kubernetes.io/docs/concepts/policy/resource-quotas/
