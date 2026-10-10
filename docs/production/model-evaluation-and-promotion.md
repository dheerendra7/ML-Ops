# Model Evaluation Gates and Promotion Strategies

> Training run successful hone ka matlab model production ke liye ready nahi. Evaluation gate ka kaam measurable evidence ko predefined acceptance criteria se compare karna aur failing output ko deployment/promotion se rokna hai.

## 5-minute snapshot

- **Baseline:** existing model, simple heuristic ya agreed benchmark jiske against candidate compare hota hai.
- **Evaluation dataset:** data used to estimate expected model behavior. Data leakage se result unrealistically optimistic ho sakta hai.
- **Metric and threshold:** measurable quality signal aur release ke liye agreed limit.
- **Quality gate:** automation jo metrics/data checks verify karke pass/fail decision deti hai.
- **Promotion:** candidate artifact ko next environment/stage/model registry/deployment tak move karna.
- **Rollback:** deployed candidate ko previous known-good version par return karne ka documented mechanism.

Gate ko training code se independent reviewable rakhna useful hai: threshold, evaluation evidence, decision aur approved model artifact traceable hone chahiye.

## 1. Training success vs model acceptance

| Signal | Kya prove karta hai | Kya prove nahi karta |
|---|---|---|
| Training process exit code success | Training task expected process completion tak pahunchi | Model useful, generalizable ya safe hai |
| Evaluation metric threshold pass | Chosen metric and evaluation dataset par defined criterion pass hua | Har user/group/input condition par quality pass hai |
| Data validation pass | Defined data contract/checks pass hue | Labels correct hain ya deployment safe hai |
| Pipeline green | Configured task graph successful hua | Missing gate, weak threshold ya bad dataset ke risk automatically resolved hain |
| Production monitoring healthy | Observed interval/signals mein monitored conditions acceptable hain | Future drift ya unmonitored failure impossible hai |

Production decision ko multiple relevant signals aur risk owner ki review par base karo, not one green status badge.

## 2. Evaluation dataset ko protect karo

- Train, validation aur final test data ke roles clearly define karo.
- Duplicate records, target leakage, temporal leakage aur train/test overlap investigate karo.
- Dataset source, extraction window, preprocessing version, label version aur data quality checks record karo.
- Imbalanced or grouped data ke liye random split automatically appropriate nahi hota; the sampling/splitting strategy should match expected real-world use.
- Threshold choose karne ke liye test set baar-baar tune mat karo; final test evidence ko independent rakhna usually more defensible hai.
- Sensitive data ko logs, CI output, issue reports ya public artifacts mein expose mat karo.

Time-series, user-group, medical, finance, vision aur text use-cases mein suitable split/evaluation methodology different ho sakti hai. Domain-risk review required hai.

## 3. Metric and threshold design

Promotion se pehle written acceptance policy define karo:

1. **Primary metric:** expected outcome ko directly represent kare.
2. **Guardrail metrics:** failure modes jo average metric hide kar sakta hai.
3. **Baseline:** candidate kitna improve/regress kar sakta hai relative to current solution.
4. **Minimum data/evidence:** sample size, valid rows, required labels, freshness aur missing-value tolerance.
5. **Subgroup checks:** important users, geography, device, class or operating conditions ke relevant slices.
6. **Uncertainty:** metric variation or confidence interval decision ko materially affect karta hai ya nahi.
7. **Cost/latency constraints:** acceptable quality ke saath runtime, memory, latency aur inference cost bhi fit honi chahiye.
8. **Approval and exception owner:** threshold fail ho to override kaun approve kar sakta hai, aur rationale kaise record hoga.

Har model ke liye universal threshold nahi hota. Threshold ko product objective, risk aur business constraints ke against justify karo.

## 4. What the automated gate must do

A robust gate should:

- evaluation result artifact/record ko current candidate model and data version se link kare;
- required metrics present hon aur correct type/range mein hon, ye validate kare;
- missing, NaN, infinite, malformed or stale metrics ko an unapproved result treat kare;
- required thresholds and guardrails evaluate kare;
- pass/fail reason, metric values and policy version record kare without leaking private data;
- fail closed by default when required evidence is missing or invalid;
- failure ko actual downstream promote/deploy step tak propagate kare;
- gate logic ko test kare for pass, fail, missing metric, bad type and boundary values.

Sirf log mein "quality gate failed" print karna enforcement nahi hai. DAG dependency ya condition ko verify karo taaki failing evaluation ke baad promotion task sach mein execute na ho.

## 5. Synthetic KFP example in this repo

[Pipeline artifact and quality-gate example](../../examples/kfp/pipeline_artifacts_caching.py) intentionally synthetic hai. It builds a tiny mean-baseline artifact, calculates an illustrative score and fails when an input offset pushes that score below a selected threshold.

Ye demonstration artifact wiring, threshold checking aur compile-time checks sikhane ke liye hai. Iska score actual statistical validation, fairness, calibration, safety, or business acceptance ka substitute nahi hai.

Compile the pipeline using the pinned dependency file; CI checks that the source compiles into a non-empty package. Compile success **does not** submit a run or verify a target Kubeflow backend. Remote run and real evaluation require compatible installation, real evaluation data, storage access and a deployment-specific test.

## 6. Promotion strategies

| Strategy | How it works | Main guardrail |
|---|---|---|
| Offline evaluation | Candidate is compared to baseline using versioned evaluation data | Leakage checks, repeatable metrics and documented threshold |
| Staging | Candidate runs in a pre-production environment | Integration, permission, latency, resource and data-path validation |
| Shadow | Candidate receives representative traffic/data without serving the authoritative response | Privacy, cost, traffic mirroring and output comparison controls |
| Canary | Candidate serves a controlled subset before broader rollout | Health/quality metrics, clear stop criteria and fast rollback |
| Full promotion | Candidate becomes the primary approved version | Named owner, release record, monitoring and rollback readiness |

Not every workload needs every stage. Higher-risk models and systems that influence consequential decisions need a review proportionate to impact.

## 7. Evidence to keep with a release

For each candidate, record:

- source commit and pipeline definition/version;
- dataset/version and evaluation split details;
- dependency lockfile and container image digest;
- candidate model/artifact URI plus integrity/provenance metadata where available;
- evaluation metrics, thresholds and policy version;
- gate result, reason and approver;
- intended uses, known limitations and unresolved risks;
- target environment, monitoring owner and rollback procedure.

Avoid placing raw sensitive datasets, credentials or personally identifiable information in the release record. Store references and sanitized evidence under appropriate access controls.

## 8. Failure modes

| Symptom | Likely weakness | Improvement |
|---|---|---|
| Excellent score but poor live performance | Leakage, evaluation mismatch or distribution shift | Review split strategy and monitor representative production signals |
| Pipeline green despite missing metric | Gate ignores absent result or isn't in the DAG | Fail closed when required metrics are absent and test the promotion dependency |
| Candidate passes average metric but harms subgroup | Aggregate hides a slice regression | Add relevant subgroup/guardrail checks |
| Same model appears under multiple identifiers | Artifact/version metadata incomplete | Link immutable artifact ID/digest, source commit and run ID |
| Failed gate is manually bypassed without trail | Exception path has no governance | Require recorded approval, reason, owner and risk expiry |
| Rollback takes too long | Previous artifact/config wasn't retained or tested | Practice rollback and preserve known-good release references |

## 9. Recall questions

1. Training process success aur model quality acceptance mein kya difference hai?
2. Evaluation data mein leakage threshold decision ko kaise mislead kar sakta hai?
3. Missing metric par gate fail-closed kyun hona chahiye?
4. Average metric subgroup failure ko kaise hide kar sakta hai?
5. Gate pass hone ke baad bhi staging/canary/monitoring ki zaroorat kyun ho sakti hai?
6. Release record mein model artifact ko dataset, code aur image version se kaise link karoge?

## References

- https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/data-types/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/components/compose-components-into-pipelines/
- https://kubernetes.io/docs/concepts/containers/images/
