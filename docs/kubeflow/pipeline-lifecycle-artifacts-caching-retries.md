# KFP Run Lifecycle: Parameters, Artifacts, Caching, Retries, and Quality Gates

> Pipeline ka green run sirf itna batata hai ki configured tasks successful hue. Usse ye prove nahi hota ki dataset sahi tha, model quality acceptable thi, ya release safe tha. Is guide ka focus task orchestration se aage data flow aur release decisions tak jaana hai.

## 5-minute snapshot

- **Parameters** small scalar/config values pass karte hain, jaise threshold, epoch count ya feature flag.
- **Artifacts** datasets, models, reports aur doosre file-based outputs represent karte hain. KFP unhe task outputs/inputs ke roop mein track kar sakta hai.
- **Caching** same component/input configuration ke successful result ko reuse kar sakti hai; hidden external state caching ko unsafe bana sakti hai.
- **Retries** failed task ko dobara execute karte hain. Ye transient failures ke liye hain, deterministic code/quality failures ko hide karne ke liye nahi.
- **Quality gate** evaluation evidence ko explicit acceptance rule ke against check karta hai aur fail hone par promotion rokna chahiye.

Exact SDK API aur backend support installed KFP version ke saath verify karo. Is repo ka example KFP SDK v2.17.0 par compile smoke test karta hai; live cluster version isse different ho sakta hai.

## 1. Pipeline run lifecycle

~~~text
Pipeline parameters
       |
       v
Author -> Compile/package -> Submit run to configured KFP backend
                                  |
                                  v
                         Resolve task dependencies
                                  |
                                  v
                       Execute each component task
                                  |
                    +-------------+-------------+
                    |             |             |
                    v             v             v
               Data prep       Training     Evaluation
                    |             |             |
                    +------ artifacts/params ---+
                                  |
                                  v
                            Quality gate
                                  |
                      pass ------+------ fail
                        |                  |
                        v                  v
                 Eligible for       Stop promotion,
                 review/release     preserve evidence
~~~

Ye conceptual flow hai. Actual storage, metadata services, run API aur orchestration details installation/backend ke hisaab se vary karte hain.

## 2. Parameters vs artifacts

| Need | Use | Example |
|---|---|---|
| Small scalar or configuration | Parameter | learning-rate value, split seed, acceptance threshold |
| A dataset file/folder | Artifact | Dataset |
| Saved model file/folder | Artifact | Model |
| Evaluation results with metadata | Artifact/metrics interface where appropriate | evaluation report and recorded metrics |

Badi file contents ko plain scalar parameter mein embed karna avoid karo. Declared input/output contracts se pipeline ka data flow visible hota hai aur compiler task types validate kar sakta hai.

Artifact properties ko samjho:

- **path:** task runtime ka local filesystem path jahan read/write kar sakte ho.
- **uri:** underlying artifact ka configured storage location.
- **metadata:** artifact ke saath attach ki gayi metadata.
- **name:** artifact name.

Traditional artifact syntax mein component ko **Input[Dataset]** ya **Output[Model]** mil sakta hai. Output ke path par file likho; supported KFP backend us output ko configured artifact storage tak persist/track kar sakta hai. Input artifact ko immutable treat karo. Pythonic artifact authoring syntax ka support backend ke hisaab se vary karta hai; current open-source KFP backend compatibility confirm kiye bina syntax swap mat karo.

## 3. Working example: synthetic artifact-to-gate pipeline

Repo mein ye sample hai:

- [Pipeline source](../../examples/kfp/pipeline_artifacts_caching.py)
- [Pinned SDK requirement](../../examples/kfp/requirements.txt)

Example teen rows ka synthetic dataset banata hai, usse ek toy mean-baseline model artifact write karta hai, synthetic score calculate karta hai aur threshold se compare karta hai. Ye **real training algorithm ya production metric nahi** hai; iska purpose artifact wiring aur gate behavior demonstrate karna hai.

### Compile locally, run on no cluster

Python environment create karo aur pinned SDK install karo:

~~~bash
python -m venv .venv
~~~

Linux/macOS shell par:

~~~bash
source .venv/bin/activate
python -m pip install -r examples/kfp/requirements.txt
python examples/kfp/pipeline_artifacts_caching.py --output /tmp/artifact-gate-pipeline.yaml
~~~

Windows PowerShell mein environment activate karne ke liye:

~~~powershell
.venv\Scripts\Activate.ps1
python -m pip install -r examples/kfp/requirements.txt
python examples/kfp/pipeline_artifacts_caching.py --output $env:TEMP\artifact-gate-pipeline.yaml
~~~

Expected result: compiler output mein generated pipeline file ka path print hota hai aur YAML file non-empty hoti hai. Is command se **pipeline compile hoti hai; remote KFP run submit nahi hota**. CI bhi isi compilation step ko validate karta hai.

Real run ke liye target KFP backend ka compatible SDK use karo aur configured API endpoint, authentication, pipeline root/artifact storage, permissions aur required infrastructure verify karo. Remote credentials is repo mein nahi rakhe jate.

### Quality gate ko deliberately fail karke samjho

Default **offset=0.0** toy model ko expected synthetic mean ke kareeb rakhta hai, isliye synthetic score gate pass karta hai. Offset ko **1.0** aur threshold ko **0.8** karne par toy score threshold se neeche jaata hai, aur gate component fail hota hai.

Fail gate ka expected meaning: output ko promotion eligible mat samjho. Real pipelines mein metric, data validation, policy checks aur baseline thresholds ko actual task ke risk ke hisaab se define karna hoga. Ek arbitrary synthetic score ko business acceptance metric mat banao.

## 4. Caching: speed-up ya stale result?

KFP caching same component definition aur matching declared inputs/parameters ke liye pehle ke available output ko reuse kar sakti hai. Isse expensive preprocessing/train steps baar-baar run karne ki cost kam ho sakti hai.

Caching tabhi reliable hai jab task ke true dependencies declared hon:

- Source code/dependency image aur runtime meaningful version se identified hain.
- Input parameters aur input artifacts correct hain.
- Task hidden mutable external state (untracked database row, URL ka latest content, secret config, current time) par silently depend nahi karta.
- Artifact availability aur backend cache behavior expected hain.

Agar task ko har run par execute karna zaroori hai, task-level caching explicitly disable ki ja sakti hai:

~~~python
external_check_task.set_caching_options(enable_caching=False)
~~~

Ye snippet tab use karo jab **external_check_task** tumhare pipeline mein bana hua real task ho. Har task par caching disable karna performance/cost ko hurt kar sakta hai; har task par caching enable chhodna bhi safe assumption nahi hai. Fresh external state ke saath kaam karne wale task ki caching policy deliberately choose karo.

## 5. Retries: transient failure ko handle karo

Retries tab useful hote hain jab error transient ho sakta hai—jaise short network interruption ya temporarily unavailable external dependency—and task safely repeat ho sakta ho.

KFP SDK task configuration ka example:

~~~python
remote_io_task.set_retry(
    num_retries=2,
    backoff_duration="10s",
    backoff_factor=2.0,
    backoff_max_duration="60s",
)
~~~

Ye snippet existing **remote_io_task** par apply karne ke liye hai; sample toy pipeline mein unnecessary retries deliberately configured nahi hain. SDK/backend version mein available retry configuration aur actual semantics verify karo.

Retry policy choose karne se pehle:

- Task idempotent hai ya repeat se duplicate side effects honge?
- Failure transient lagta hai ya invalid input/bug hai?
- Attempts aur backoff se total runtime/cost kitna badhega?
- External system rate limits ya quota par kya impact hoga?
- Failure status, logs aur last attempt ka evidence retain hoga?

**Deterministic schema validation, bad model metric, missing required parameter ya programming bug ko blindly retry mat karo.** Quality gate fail hua to threshold/data/model ko investigate karna chahiye, retries badha dena nahi.

## 6. Evaluation gate and promotion are different

A production-minded sequence:

1. Train task versioned model artifact produce kare.
2. Evaluation task documented holdout/validation data aur agreed metric use kare.
3. Gate metric, minimum threshold, missing-metric handling aur required checks validate kare.
4. Failed evaluation par downstream promote/deploy step execute na ho.
5. Passed evaluation ko bhi required security/review approvals milen.
6. Release record mein model artifact, dataset version, source commit, metrics aur approval evidence link ho.

Pipeline DAG/conditions backend aur SDK ke supported control flow se implement karo. Agar gate step fails, verify karo ki publish/deploy step genuinely blocked hai—sirf gate ka log message de dena control enforcement nahi hai.

## 7. Common failure modes

| Symptom | Investigation |
|---|---|
| Artifact path not found | Task output declaration, path write, input/output wiring and task logs |
| Output task ko accessible nahi | Artifact URI/storage configuration, service identity and backend permissions |
| Unexpected cache reuse | Declared inputs, task code/image versions, cache configuration and external state |
| Same transient error repeats | Retry count/backoff, external dependency health, network/auth and logs |
| Repeated writes cause duplicates | Idempotency key, output naming, external side effects and retry semantics |
| Evaluation task green but deploy still happens after failure | DAG dependency/condition and actual promotion task execution |
| Compile pass but backend rejects run | SDK/backend compatibility, pipeline spec support, authentication and artifact root configuration |

## 8. Run review checklist

- [ ] SDK/compiler version aur target backend compatibility noted hai.
- [ ] Pipeline parameters aur artifacts clearly typed/declared hain.
- [ ] Artifact files declared output path par write hoti hain.
- [ ] Caching hidden or mutable dependencies ko consider karti hai.
- [ ] Retries bounded hain aur task safe-to-repeat hai.
- [ ] Evaluation uses the intended dataset and documented metric.
- [ ] Failed gate actual promotion/deployment ko block karta hai.
- [ ] Logs/output metadata mein secrets ya sensitive data leak nahi hote.
- [ ] Run ID, code commit, data version, image digest aur evaluation evidence retain hote hain.

## Recall questions

1. Parameter aur artifact ka use-case kaise different hai?
2. **Input[Dataset]** aur **Output[Model]** data flow ko kaise explicit banate hain?
3. Caching unsafe kab ban sakti hai?
4. Retries ke saath idempotency kyun important hai?
5. Compilation pass hone ke baad bhi remote pipeline run kyun fail ho sakta hai?
6. Model evaluation pass aur deployment approval ko separate kyun rakhna chahiye?

## References

- https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/data-types/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/caching/
- https://www.kubeflow.org/docs/components/pipelines/user-guides/components/compose-components-into-pipelines/
- https://kubeflow-pipelines.readthedocs.io/en/stable/source/dsl.html
- https://github.com/kubeflow/pipelines/releases
