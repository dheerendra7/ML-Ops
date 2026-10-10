# Reproducibility, Experiment Tracking, and Artifact Lineage

> Reproducibility ka matlab sirf same Python file dobara run kar dena nahi. Useful MLOps practice mein code, data, dependencies, runtime, parameters aur evaluation evidence ko ek saath identify karna hota hai, taaki result ko explain, compare aur audit kiya ja sake.

## 5-minute snapshot

- **Experiment tracking:** training/evaluation runs ke parameters, metrics, status aur artefacts record/compare karna.
- **Artifact lineage:** output model ko us inputs, dataset, pipeline task aur source/runtime context se link karna jisne use produce kiya.
- **Reproducibility:** documented inputs/environment se sufficiently similar result dobara produce kar pana; exact numerical identity model/runtime ke hisaab se possible na bhi ho.
- **Provenance:** evidence about how an artifact was produced, by which source/build/workflow and with which inputs.
- **Immutability:** release reference ko aise identify karna ki baad mein wahi reference silently different bytes ko point na kare.

KFP parameters and artifacts pass/track kar sakta hai, but teams ko data versions, container digests, evaluation reports and release metadata bhi deliberately retain karna chahiye.

## 1. What should one run record contain?

| Category | Record | Why it matters |
|---|---|---|
| Run identity | Run ID, pipeline name/version, timestamps, result status | Run ko logs/metrics/evidence se correlate karna |
| Source | Repository, source commit, pipeline definition version | Identify which code/pipeline produced the result |
| Dataset/input | Dataset ID/version, URI/reference, content fingerprint where available, preprocessing version | Mutable path se data silently change na ho |
| Runtime | Container image digest, dependency lockfile/version, SDK/runtime versions | Explain environment differences |
| Parameters | Training/evaluation parameters, seeds, feature/config version | Experiment compare/reproduce karna |
| Outputs | Model/dataset/report artifact URIs, digests/checksums where appropriate, metadata | Exact output identify aur access-control karna |
| Quality evidence | Evaluation dataset/version, metrics, thresholds, gate outcome, policy version | Model acceptance decision ko audit karna |
| Ownership/governance | Owner, intended use, approval, known limitations | Handoff aur incident response ko clear rakhna |

Values organization-specific systems mein store ho sakte hain. This repository's example YAML is a **custom teaching template**, not an official KFP schema, ML Metadata contract or universally accepted manifest format.

## 2. Input identity is more than a URI

Ek dataset URI ya mutable object path alone complete identity nahi hoti. Path same reh sakta hai lekin uske bytes badal sakte hain.

Useful practices:

- Dataset/version identifier aur extraction time/window retain karo.
- Preprocessing code/config aur feature definitions ko version karo.
- Where appropriate, data artifact ke content digest/checksum record karo; ensure the digest is actually computed over the intended content.
- External table/view ke case mein source snapshot, partition/window, query/version ya equivalent immutable input reference define karo.
- Avoid logging raw sensitive dataset rows just to make a run reproducible; keep governed references and sanitized metadata.

Large datasets ke hashes compute karna expensive ho sakta hai; choose a content identity strategy appropriate for data size, storage format and governance needs.

## 3. Runtime identity

Repeatable deployment ke liye record karo:

- container image reference by digest where practical;
- dependency lockfile or exact resolved dependency set;
- Python/framework/runtime and accelerator configuration;
- KFP SDK and backend version;
- relevant OS/system packages when they affect behavior;
- deterministic random seeds, where supported, and known nondeterministic operations.

Digest pinning exact image content identify karne mein help karti hai, lekin old vulnerable image par permanently stuck rehna goal nahi. Patch updates deliberately review/rebuild karo aur new digest ko updated release record mein store karo. See the [container image security guide](../containers/image-security-and-reproducibility.md).

## 4. Parameters, caching and nondeterminism

- All material task inputs should be declared; hidden environment variables, current time, mutable APIs or unversioned database reads undermine reproducibility.
- Random seeds record karo, but don't claim they guarantee deterministic output when libraries/hardware/distributed training allow nondeterminism.
- KFP caching can reuse a result when the component and declared inputs match. If the task depends on mutable external state not represented in the inputs, cached output can be inappropriate.
- A rerun that reuses cache is not the same as executing every component again. Record whether cache reuse is acceptable for the experiment.
- If a step needs fresh external state, explicitly choose the caching behavior and capture that state/version.

Related guide: [KFP lifecycle, artifacts, caching and retries](../kubeflow/pipeline-lifecycle-artifacts-caching-retries.md).

## 5. KFP artifacts and lineage

KFP's artifact interface can make data flow explicit through declared inputs/outputs and artifact metadata. For traditional artifact syntax, a component can read from the input artifact path and write an output artifact to the path provided by the SDK/backend; the configured backend handles storage integration.

For each important output, record a link to relevant context:

1. output model artifact -> training task/run;
2. training task -> dataset and preprocessing outputs;
3. dataset -> original source/version and transformation;
4. task -> source commit, dependency/image version and parameters;
5. model -> evaluation report, metric policy and gate decision.

An artifact URI tells you where to look; lineage explains why and how that output exists. Access permissions and retention still apply.

## 6. Example run record

The sample template is at [run-record.example.yaml](../../examples/lineage/run-record.example.yaml). It intentionally contains replacement placeholders and no real credentials, dataset, model or artifact URI.

Use it as a design prompt:

- replace placeholders with references from your actual source/data/runtime systems;
- remove fields your system cannot reliably capture, or explicitly mark them unavailable;
- add the minimum required fields for audit, compliance, and rollback;
- do not copy the YAML into a KFP API expecting it to be accepted as a native resource.

## 7. What reproducibility cannot guarantee

A run record cannot prove that the source data is correct, the labels are trustworthy, the evaluation split is valid, the model is fair, or a deployment is safe. Hardware kernels, distributed ordering, library versions and external dependencies can affect exact outputs.

Distinguish these goals:

- **Traceable:** identify the inputs and environment used.
- **Repeatable:** rerun the same declared procedure under controlled conditions.
- **Reproducible:** independently reconstruct a comparable result from the recorded materials.
- **Auditable:** recover the evidence and approvals behind the release decision.

Choose the required level according to model risk and operational use; record known limits rather than calling every run fully reproducible.

## 8. Operational checklist

- [ ] Source commit and pipeline definition version are recorded for each run.
- [ ] Inputs/datasets have a version or another defensible identity.
- [ ] Preprocessing and feature transformation versions are retained.
- [ ] Container image digest and resolved dependencies are recorded.
- [ ] Material parameters, seeds and relevant nondeterminism are captured.
- [ ] Output model and evaluation artefacts can be located and accessed by authorized reviewers.
- [ ] Metrics, threshold policy and promotion decision are linked to the candidate model.
- [ ] Cache usage is understood for every task with mutable external dependencies.
- [ ] Sensitive data is protected; run records don't duplicate raw confidential content.
- [ ] Artifact retention, deletion and restore policies have an owner.

## Recall questions

1. Dataset URI aur dataset identity mein kya difference ho sakta hai?
2. Container digest aur dependency lockfile dono kyun record karne chahiye?
3. Cache reuse ka run-history interpretation par kya effect hai?
4. Artifact location aur artifact lineage kaise different hain?
5. Traceable aur reproducible claims ko separate rakhna kyun useful hai?

## References

- https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/data-types/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/caching/
- https://kubernetes.io/docs/concepts/containers/images/
- https://kubernetes.io/docs/concepts/security/security-checklist/
