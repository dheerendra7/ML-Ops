# KFP Component Types: Lightweight Python vs Container Components

## 5-minute snapshot
A component is a reusable task with declared inputs and outputs. Lightweight Python components are convenient for small Python functions whose dependencies fit the SDK's supported packaging model. Container components provide more explicit control over the image and command, useful for custom runtimes, system packages, or non-Python tools.

## Comparison

| Concern | Lightweight Python | Container component |
|---|---|---|
| Authoring | Python function and supported annotations/decorator | Explicit image, command, and arguments through the SDK/specification |
| Runtime | Packaged according to that KFP version's rules | Primarily defined by the chosen image and command |
| Dependencies | Must use the SDK's supported dependency mechanism | Build and maintain an image with required libraries and OS packages |
| Reproducibility | Pin dependencies and understand packaging behavior | Pin image content by digest where practical |
| Best fit | Small, self-contained Python tasks | Custom runtime, non-Python executable, specialized dependencies |

Exact APIs and supported parameters depend on the SDK version. Check version-matched documentation before copying code.

## Decision checklist
Choose lightweight Python when the task is small, Python-only, and dependencies are easy to manage. Choose a container component when you need explicit runtime control or dependencies awkward to express in a lightweight function.

For either type:
- Declare inputs and outputs explicitly.
- Do not rely on undeclared local files or developer-machine state.
- Pin dependencies and keep credentials out of images and source.
- Make tasks idempotent where possible and define failure behavior.
- Log enough context to debug without exposing sensitive values.

## Common mistakes
- Assuming the local Python environment exists in the task container.
- Using a mutable image tag and assuming it always identifies the same build.
- Passing secrets as ordinary parameters or printing them in logs.
- Confusing component packaging with orchestration.

## Recall
1. What dependency need makes a container component attractive?
2. Why don't laptop packages automatically exist in a task?
3. What does pinning an image digest improve?

## References
- https://www.kubeflow.org/docs/components/pipelines/user-guides/components/
- https://kubeflow-pipelines.readthedocs.io/