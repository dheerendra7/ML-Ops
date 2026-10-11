# MLOps Engineering Handbook

> Free, practical, production-aware MLOps learning material — from first principles to advanced engineering, explained in Hinglish.

Learn how machine-learning systems are built, packaged, orchestrated, deployed, observed, and operated responsibly. This repository is a learning handbook, not a product or a claim that example configurations are production-ready without review.

## Who this is for

- Students building a foundation in Kubernetes and MLOps
- Developers learning Kubeflow Pipelines (KFP)
- Engineers who want practical debugging and production-readiness habits
- Interview candidates who need concise revision after understanding the concepts

## Learning path

1. **Foundations** — containers, Kubernetes objects, namespaces, requests and limits.
2. **Kubeflow architecture** — how platform components fit together and where responsibilities live.
3. **Pipeline components** — lightweight Python components vs container components, with trade-offs.
4. **Isolation and governance** — Profiles, namespaces, RBAC, ResourceQuota, and LimitRange.
5. **Operations** — troubleshooting, reliability, security, observability, and cost awareness.
6. **Revision** — active recall and interview prompts after completing the lessons.

Start with [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md), then use the topic guides below.

## Guides

- [Kubeflow architecture](docs/kubeflow/architecture.md)
- [KFP component types](docs/kubeflow/kfp-component-types.md)
- [Profiles, namespaces, and isolation](docs/kubeflow/profiles-namespaces-isolation.md)
- [Kubernetes resource controls](docs/kubernetes-foundations/resource-controls.md)
- [Kubernetes workloads and configuration](docs/kubernetes-foundations/workloads-and-configuration.md)
- [Container image security and reproducibility](docs/containers/image-security-and-reproducibility.md)
- [KFP lifecycle, artifacts, caching, retries, and quality gates](docs/kubeflow/pipeline-lifecycle-artifacts-caching-retries.md)
- [Model evaluation gates and promotion](docs/production/model-evaluation-and-promotion.md)
- [Observability for ML pipelines](docs/production/observability-for-ml-pipelines.md)
- [Reproducibility, experiment tracking, and lineage](docs/production/reproducibility-and-lineage.md)
- [Cost controls and GPU scheduling](docs/production/cost-controls-and-gpu-scheduling.md)
- [Standalone KFP backend smoke test](docs/testing/standalone-kfp-backend-smoke.md)
- [External secrets with HashiCorp Vault](docs/security/external-secrets-vault-lab.md)
- [Troubleshooting checklist](docs/troubleshooting/debugging-checklist.md)
- [Production-readiness checklist](docs/production/readiness-checklist.md)
- [Interview revision cards](docs/interview/revision-cards.md)
- [Glossary](GLOSSARY.md)
- [Source register](SOURCES.md)
- [Roadmap](ROADMAP.md)

## Project status and evidence

- [Project status and validation report](docs/PROJECT-STATUS-REPORT.md) summarizes implemented areas, recorded CI evidence, explicit exclusions, and the remaining validation needed before broader production-readiness claims.

## Hands-on learning and automated checks

- [Lab 01 — Kubernetes resource governance](docs/labs/resource-governance.md) walks through ResourceQuota, LimitRange, server-side dry run, expected quota rejection, troubleshooting, and cleanup.
- [Lab 02 — Least-privilege RBAC](docs/security/least-privilege-rbac-lab.md) checks allowed and denied ServiceAccount actions in a disposable namespace.
- [Lab 03 — Secrets and rotation](docs/security/secrets-and-rotation-lab.md) uses only dummy credentials and explains external-manager prerequisites.
- [Lab 04 — Vault + External Secrets Operator](docs/security/external-secrets-vault-lab.md) syncs a synthetic Vault KV v2 value through a path-scoped token, verifies read denial outside that path, and tests rotation without printing secret contents. It is explicitly a disposable dev-mode lab, not a production Vault recipe.
- [Lab validation matrix](docs/testing/lab-validation-matrix.md) separates actual CI evidence from untested Kubeflow/GPU/provider scenarios.
- The [run-record YAML](examples/lineage/run-record.example.yaml) and [GPU Job YAML](examples/cost/gpu-job.example.yaml) are educational templates; their placeholders require review before use.
- GitHub Actions validates relative Markdown links, code fences, YAML/Python syntax, security-sensitive example invariants, KFP compilation and local runtime, the container smoke test, and core Kubernetes labs on Kind v1.34.3 and v1.35.0. The expanded pinned-chart Vault/ESO workflow passed on [run #38078803152](https://github.com/dheerendra7/ML-Ops/actions/runs/38078803152): it verified a path-scoped Vault token, Kubernetes Secret sync, a non-root consumer Pod reading a read-only mounted file, and mounted-file rotation in a disposable Kind cluster without printing values. This is dev-mode integration evidence, not production Vault certification.
- The KFP local test checks a successful artifact-to-gate run, an intentionally rejected candidate, 17 score/threshold type and boundary cases, malformed dataset rows, and invalid training offsets. The Kind tests cover ResourceQuota, LimitRange defaults, a sample Job, RBAC allow/deny, and synthetic Secret rotation.
- The latest standalone KFP backend smoke workflow passed in [run #38120495578](https://github.com/dheerendra7/ML-Ops/actions/runs/38120495578) on the pipeline/script revision at commit [842b1d3](https://github.com/dheerendra7/ML-Ops/commit/842b1d321e00d787b3691b5f965a54b6d25fa6e7): standalone KFP 2.17.0 on Kind v1.34.3, successful candidate tasks, and rejection specifically at the quality gate. The current main code/test baseline [71dc3b4](https://github.com/dheerendra7/ML-Ops/commit/71dc3b484dc04c1d101d32dbfe8456322079ac3a) passed all five repository CI jobs in [run #38120678566](https://github.com/dheerendra7/ML-Ops/actions/runs/38120678566). See the [validation matrix](docs/testing/lab-validation-matrix.md) for scope and limitations. These checks still do **not** prove a full Kubeflow installation, production artifact-store durability, GPU execution, or production Vault authentication/TLS/high-availability settings.

## How each lesson is structured

- **5-minute snapshot:** the core idea and when it matters.
- **Mental model:** a simple explanation before terminology.
- **Technical details:** behavior, boundaries, and trade-offs.
- **Hands-on examples:** commands or YAML that you can adapt safely.
- **Failure modes:** what commonly breaks and how to investigate.
- **Recall:** short questions to test whether the concept stuck.
- **References:** official documentation first.

## Accuracy and version notes

Kubernetes and Kubeflow behavior can vary by release, installation method, and enabled components. Always check the version used by your cluster and verify examples against the official docs linked in each lesson. Examples are educational starting points; review resource values, permissions, and platform-specific requirements before applying them to a real cluster.

## Try the examples safely

The `examples/` directory contains educational YAML, Python, and container-image examples. Review each example and its version assumptions before running it; none of the samples automatically creates a Kubeflow installation. Use a disposable development cluster for Kubernetes labs, never bake credentials into images, and never paste tokens or secrets into issues or commits.

## Contributing

Corrections and improvements are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), include the relevant Kubernetes/Kubeflow version when reporting behavior, and prefer official references. For security-sensitive reports, follow [SECURITY.md](SECURITY.md).

## License

The handbook is licensed under the MIT License. Third-party trademarks and referenced documentation remain the property of their respective owners.
