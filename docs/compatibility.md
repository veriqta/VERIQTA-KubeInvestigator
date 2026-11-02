# Compatibility and validation claims

| Area | Target | Actually verified locally |
| --- | --- | --- |
| Python | 3.12+ with SQLite 3.54.1+ | macOS 26.2 arm64: source-built maintained CPython 3.12.16, SQLite 3.54.1, Expat 2.9.0; 74 tests and real HTTP source setup pass. Old bundled SQLite 3.53.1 is rejected, not patched in place |
| Kubernetes | 1.35–1.37 | Native Linux arm64 kind: 1.35.8 prior incident/recovery baseline; 1.36.4 and 1.37.0 complete real-evidence incident acceptance on startup-guard image; all cleanup verified |
| Helm | 3.19+ | 3.19.0 real installation on each above Kubernetes version. Other Helm versions unexecuted |
| Container | Linux amd64 and arm64 | Native arm64 execution; amd64 image built and EXECUTED under QEMU (runtime checks + 61 application/security/storage tests). Native amd64 hardware/Kubernetes remains unverified |
| Host setup | Linux, macOS, Windows through WSL2 | macOS source installation verified. Native arm64 Linux source setup tested in a disposable development container: 73 passed, 1 Helm-only skip; static/docs checks passed after fixture corrections. Bare-host Linux/WSL2/Homebrew-Linux setup unexecuted |
| Provider | OpenAI JSON-mode adapter, configurable model | Mock/HTTP transport tests only; no paid calls; live-model accuracy unverified |
| Storage | Single-writer SQLite WAL PVC, 1Gi default | Local lifecycle/WAL/retention/limits and prior 1.35.8 real-PVC restart/backup/restore/same-schema Helm config rollback passed; physical loss/future schema downgrade unverified |
| Resources | requests 100m/128Mi, limits 1 CPU/512Mi | Starting values only; no measured recommended cluster sizing |

Kubernetes maintained versions were derived from [official releases](https://kubernetes.io/releases/) on 2026-11-01. A target range is not a certification. Client 37 is selected for this modest range; the native arm64 version matrix now has actual incident acceptance; hosted/native-amd64 matrix execution remains necessary. No EKS, AKS, GKE, OpenShift, enterprise, air-gapped or GPU claim is made. No managed service is required. Exact scopes, image identities, fixture corrections and scan DB metadata are in [current evidence](security/findings/2026-11-02-source-compatibility.json). An emulated execution is not a native hardware result.

Initial setup downloads Python packages, base/application/sample images and kind nodes. Live mode requires HTTPS to api.openai.com; the app also needs its Kubernetes API and cluster DNS. Restricted-network operators can mirror reviewed wheels/images and configure image repositories and private-registry pulls via their infrastructure, but must validate digests/architectures and provider egress. An offline live-model deployment is not supported. A StorageClass, ingress controller, TLS certificates, DNS records and enforcing CNI are operator-supplied where used.
