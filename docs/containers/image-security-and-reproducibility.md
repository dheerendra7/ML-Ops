# Container Images: Build, Security, and Reproducibility

> ML workload ka code tabhi repeatably run hota hai jab runtime aur dependencies ka version bhi known ho. Container image mein application ke saath runtime packages aur libraries pack hote hain; image build process ko repeatable aur image ko reviewable banana MLOps ka important part hai.

## 5-minute snapshot

- **Image tag** (for example, 3.12-slim) human-readable reference hai; registry tag ko baad mein kisi doosre image par point kar sakti hai.
- **Image digest** (sha256:...) content-specific identifier hai; digest pinning exact image version identify karne mein help karti hai.
- **Small image** build/pull time, attack surface aur unused packages reduce karne mein help karti hai, lekin small size alone security proof nahi hai.
- **Non-root runtime** aur least privilege container compromise ka impact limit karne mein help karte hain.
- **Scanning, provenance, SBOM, patching aur signature verification** ek layered process ka part hain; sirf successful image build enough nahi.

## 1. Repo ka sample image

Is folder ka sample simple Python process run karta hai:

- [Dockerfile](../../examples/container-image/Dockerfile)
- [app.py](../../examples/container-image/app.py)
- [.dockerignore](../../examples/container-image/.dockerignore)

Ye learning smoke-test image hai. Dockerfile base image ke liye version tag use karta hai so beginners locally build kar saken; **version tag alone immutable pin nahi hota**. Production pipeline mein review ke baad approved base image digest use karo.

Repo root se run karo:

~~~bash
docker build -t mlops-handbook-smoke:dev examples/container-image
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop=ALL --security-opt=no-new-privileges mlops-handbook-smoke:dev
docker image inspect mlops-handbook-smoke:dev --format '{{.Id}}'
~~~

Expected output mein application ka smoke-test message aana chahiye. Docker daemon, network aur base image pull available hona chahiye. Ye example local image ko build/run karta hai; image kisi registry mein publish nahi hoti.

## 2. Base image aur digest pinning

Kubernetes image tags ko digest ke saath resolve kar sakta hai, lekin tag mutable hota hai. Agar registry par stable tag move ho jaye, future deployment different image run kar sakti hai.

Team-approved base image choose karne ke baad registry se digest verify karo. General format:

~~~dockerfile
FROM python:3.12-slim@sha256:REPLACE_WITH_REVIEWED_DIGEST
~~~

Ye **format template** hai, directly runnable line nahi: placeholder ko actual registry-provided digest se replace kiye bina build mat karo. Digest select karte waqt platform architecture (for example amd64/arm64), support lifecycle, vulnerability status aur update policy samjho.

- Base image version/digest aur update date record karo.
- Security fixes ke liye base image ko intentionally refresh/rebuild karna hota hai; pinning patching ka replacement nahi hai.
- Image ko mutable tag se publish kar sakte ho for human navigation, lekin deployment manifests mein approved immutable digest prefer karo.
- Build ke output digest ko artifact/release record ke saath link karo.

## 3. Dockerfile design checklist

- **Minimal contents:** sirf runtime ke liye required application aur libraries copy karo.
- **Non-root user:** application ko default se unprivileged user ke taur par run karo.
- **No secrets in layers:** build arguments, environment variables, source files aur image layers mein long-lived credentials bake mat karo.
- **Explicit startup:** command/entrypoint ko clear rakho; startup behavior test karo.
- **Repeatable dependencies:** direct/transitive dependencies ko project ke mechanism se pin/lock karo.
- **Clean build context:** .dockerignore mein .git, virtual environments, caches, local .env aur credentials exclude karo.
- **Avoid root-only assumptions:** filesystem writes, file ownership aur mounted paths ko non-root user ke saath test karo.
- **No unnecessary package managers or debug tools:** build stage aur runtime contents ko separate rakhne par consider karo.
- **Graceful lifecycle:** long-running process ko signals handle karne aur clean shutdown ka behavior test karna chahiye.

Multi-stage builds tab useful ho sakte hain jab build tools ko final runtime image mein rakhne ki zaroorat na ho. Har image ke liye blindly multi-stage setup add karna required nahi; actual dependency/build flow evaluate karo.

## 4. .dockerignore ko seriously lo

Docker build context mein accidentally .env, test fixtures, Git history, cache files ya local credentials send ho sakte hain. .dockerignore unnecessary files context se exclude karta hai. Ye security boundary ya secret manager ka replacement nahi hai—credentials ko context mein hi mat rakho.

Repo sample .dockerignore ko inspect karo aur apne project ke mutabik adjust karo. Generic ignore list kisi application ke required files ko bhi exclude kar sakti hai, isliye build ko test karna zaroori hai.

## 5. Image scanning, SBOM, and provenance

Release process mein organization-approved tools se ye evidence generate/retain karo:

1. **Vulnerability scan:** OS packages aur app dependencies mein known vulnerabilities.
2. **Secret scan:** image/build context mein accidentally included credentials.
3. **SBOM (Software Bill of Materials):** image ke andar included packages/components ka inventory.
4. **Build provenance:** source commit, workflow, builder aur build inputs ka record.
5. **Signature/attestation verification:** deployment point par approved identity/source policy verify karna, agar platform support karta hai.

Scan ko release gate banane se pehle severity thresholds, exceptions ka owner, false-positive review aur rebuild policy define karo. Scan clean hona unknown vulnerability ya unsafe configuration ka proof nahi; repeated patching aur monitoring chahiye.

## 6. Kubernetes par deploy karte waqt

- Approved image digest reference karo where practical.
- Private registry pull authentication ko approved mechanism se configure karo; credentials image ya public repo mein mat daalo.
- Resource requests/limits, securityContext, service account aur Pod Security/admission policies review karo.
- imagePullPolicy ko registry access, tag/digest choice aur cluster behavior ke context mein samjho.
- Deployed Pod spec inspect karke verify karo ki expected image reference use ho raha hai.
- A deliberate rollback path rakho: previous approved digest aur configuration available honi chahiye.

ImagePullBackOff ke liye image name/digest, registry reachability, pull credentials aur Pod events check karo. Digest pinning wrong permissions ya missing registry connectivity fix nahi karti.

## 7. Supply-chain release checklist

- [ ] Source commit is identifiable.
- [ ] Dependencies and base image are reviewed and versioned.
- [ ] Image builds in a controlled CI environment.
- [ ] Image runs without root where the application allows it.
- [ ] Unneeded files and secrets are absent from build context/layers.
- [ ] Image vulnerability and secret scans are reviewed.
- [ ] SBOM/provenance evidence is generated where required.
- [ ] Release output is identified by immutable digest.
- [ ] Registry push/pull permissions are least-privilege.
- [ ] Rebuild, patch, deploy and rollback owners are known.

## Recall questions

1. Tag aur digest mein key difference kya hai?
2. Digest pin karne ke baad bhi base image refresh kyun chahiye?
3. Non-root user aur read-only filesystem ka security benefit kya hai?
4. .dockerignore build context ko kaise affect karta hai?
5. SBOM, vulnerability scan aur provenance alag-alag evidence kyun hain?

## References

- https://kubernetes.io/docs/concepts/containers/images/
- https://kubernetes.io/docs/concepts/security/security-checklist/
- https://docs.docker.com/build/building/best-practices/
