# KFP Component Types: Lightweight Python vs Container Components

> Is guide ka focus decision-making hai: kaun-sa component style kab choose karna chahiye, dependencies kaise package hoti hain, aur local machine par chalne wala code pipeline task mein kyun fail ho sakta hai.

## 5-minute snapshot

Kubeflow Pipelines (KFP) mein **component** ek reusable task hota hai jiska declared input/output contract hota hai. Pipeline components ko order aur dependencies ke saath connect karti hai; component ke andar actual computation run hota hai.

Do common authoring patterns:

- **Lightweight Python component:** chhote, self-contained Python task ke liye convenient. KFP SDK us function ko apne supported packaging/runtime model ke hisaab se task ke roop mein prepare karta hai.
- **Container component:** image, command aur arguments ko explicitly define karne deta hai. Custom OS packages, specialized dependencies ya non-Python executable ke liye zyada control milta hai.

Exact decorator, parameter names aur packaging behavior installed KFP SDK version par depend karte hain. Version match kiye bina internet se copied code ko production mein mat use karo.

## 1. Component ko task contract samjho

Ek achha component clearly define karta hai:

- **Inputs:** task ko kya data ya parameters chahiye.
- **Outputs:** task kya produce karega—value, artifact, model file, metrics, ya koi aur declared result.
- **Runtime:** task kis Python environment ya container image mein execute hoga.
- **Failure behavior:** task fail ho to logs, exit status aur retry expectations kya hain.

Pipeline orchestration aur task runtime alag responsibilities hain. Pipeline decide karti hai kaunsa task pehle chalega aur data/outputs ka dependency path kya hai. Component decide karta hai task ke andar computation kaise execute hota hai.

**Mental model:** component ko ek small service/function samjho jiske inputs aur outputs ka contract clear ho. Pipeline us contract ko use karke multiple tasks ko jodti hai.

## 2. Dono styles ka comparison

| Concern | Lightweight Python | Container component |
|---|---|---|
| Authoring | Python function aur supported SDK annotations/decorator | Explicit image, command aur arguments |
| Runtime control | SDK ke packaging/runtime behavior ko samajhna zaroori | Image aur command par zyada direct control |
| Dependencies | SDK-supported mechanism se dependencies declare karo | Image build karke Python libraries aur OS packages include kar sakte ho |
| Non-Python task | Usually awkward ya unsuitable | CLI, binary ya non-Python tool run karne ke liye natural fit |
| Build/operations | Small tasks mein kam image-maintenance work | Image build, scan, publish, pull permissions aur upgrades manage karne padte hain |
| Reproducibility | Dependency versions aur packaging behavior pin/verify karo | Image ko practical ho to immutable digest se identify karo |
| Good fit | Small transformation, validation, simple feature prep | Custom system libraries, large dependency stack, CUDA/runtime needs, non-Python tools |

Ye convenience-vs-control trade-off hai; koi universal winner nahi hai.

## 3. Lightweight Python component kab choose karein?

Is path ko tab prefer karo jab:

- task chhota aur mainly Python-based hai;
- dependencies ko installed KFP SDK ke supported way mein declare kar sakte ho;
- custom OS package ya specialized runtime ki zaroorat nahi;
- team simple authoring ko prioritize karti hai.

### Common trap: local environment ko assume kar lena

Tumhare laptop par pandas ya koi private package installed ho sakta hai; pipeline task container mein woh automatically available nahi hota. Runtime isolated ho sakta hai aur packaging rules SDK version se badal sakte hain.

Dependency configuration ko component definition mein explicit rakho, supported mechanism use karo, versions pin karo, aur usi KFP SDK version se compile/test karo jo project support karta hai. Kuch SDK versions dependency lists ko component decorator ke through support karte hain; exact support aur behavior official version-matched reference se confirm karo.

## 4. Container component kab choose karein?

Container-based approach consider karo jab:

- task ko custom OS library, system executable ya non-Python tool chahiye;
- runtime environment par clear control chahiye;
- dependencies lightweight function packaging model mein manage karna difficult ho;
- same image ko CI, local integration test aur pipeline environment mein reuse karna ho.

Image ko build, test aur publish karna extra responsibility hai. Production-aware workflow mein:

1. dependencies ko pin karo;
2. image build ko repeatable rakho;
3. image scan aur vulnerability review run karo;
4. mutable tag par akela depend mat karo—jahan practical ho digest pin karo;
5. private registry pull permissions aur image retention verify karo;
6. base image aur dependencies upgrade karne ka process define karo.

Container component bhi automatically reproducible ya secure nahi ho jata. Mutable dependency, untrusted image, leaked secret ya missing permission ka issue phir bhi reh sakta hai.

## 5. Decision examples

| Task | Starting choice | Reason |
|---|---|---|
| Small Python function jo input validate karke numeric summary produce kare | Lightweight Python | Dependencies limited hain aur custom runtime ki zaroorat nahi |
| CLI tool jo Python ke bahar compiled binary use karta hai | Container component | Binary aur OS-level dependencies ko image mein package kar sakte ho |
| Specialized ML runtime ya custom system library | Usually container component | Runtime ko image ke saath version/control karna easier hota hai |
| Simple Python task jise bahut saari pinned dependencies chahiye | Compare both | Supported lightweight packaging vs maintained image ki operational cost evaluate karo |

Yeh starting recommendations hain, hard rules nahi. Actual choice dependency size, cold-start cost, security policy, SDK behavior aur team ke build/release process par depend karti hai.

## 6. Inputs, outputs aur data movement

- Component inputs/outputs ko explicit define karo; hidden assumptions debugging mushkil kar dete hain.
- Task ke container ke local filesystem ko pipeline ke future task ke saath automatically shared storage mat samjho.
- Doosre tasks ko output dena ho to declared output/artifact mechanism use karo; large model files ko giant inline parameter ke roop mein pass karna avoid karo.
- Secrets ko normal input parameter, source code, image layer ya logs mein put mat karo. Secret injection aur identity mechanism installation/platform configuration par depend karta hai.
- Paths, object storage access, artifact permissions aur serialization format ko contract ka part samjho.

## 7. Common failure modes

| Symptom | Likely area | Investigation |
|---|---|---|
| Import/module not found | Dependency packaging | Component runtime, installed package versions aur build logs inspect karo |
| Image pull error | Registry/auth/network | Image name, tag/digest, pull secret/identity aur registry reachability verify karo |
| Local file missing | Hidden machine-local state | File ko declared input/artifact ya image/package ke through deliver karo |
| Output next task tak nahi pahunchta | Input/output contract | Output declaration, artifact reference, URI aur permissions verify karo |
| Laptop par pass, pipeline mein fail | Environment mismatch | SDK/compiler version, image, dependency locks aur environment variables compare karo |
| Rerun par result change hota hai | Non-determinism | Data version, random seeds, external services aur mutable dependencies inspect karo |

Randomly retry karna fix nahi hai agar root cause persistent dependency ya permission failure hai. Pehle task logs, image/runtime aur inputs/outputs ko isolate karke investigate karo.

## 8. Component readiness checklist

Pipeline task share karne se pehle verify karo:

- [ ] Inputs/outputs explicit hain, names aur types samajhne layak hain.
- [ ] Required dependencies declared/pinned hain.
- [ ] Runtime/SDK version documented hai.
- [ ] Task undeclared laptop files ya hidden credentials par depend nahi karta.
- [ ] Failure exit code aur useful, non-sensitive logs deta hai.
- [ ] Retry karne par duplicate external side effects ka risk samjha gaya hai.
- [ ] Container image use ho rahi ho to tag/digest, registry access aur scanning process known hai.
- [ ] Output artifact/parameter agle task tak pass karke verify kiya gaya hai.

## 9. Recall questions

1. Component aur pipeline ke responsibilities mein kya difference hai?
2. Lightweight Python task mein laptop ke installed packages kyun assume nahi karne chahiye?
3. Container component ka extra maintenance burden kya hai?
4. Mutable image tag reproducibility ko kaise affect kar sakta hai?
5. Do pipeline tasks ke beech large model output pass karne ka preferred contract kya hona chahiye?
6. Import error aur image pull error ko debug karne ke initial steps kaise different hain?

## References

- https://www.kubeflow.org/docs/components/pipelines/user-guides/components/
- https://kubeflow-pipelines.readthedocs.io/
