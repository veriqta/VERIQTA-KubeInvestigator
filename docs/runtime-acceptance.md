# Container runtime and disposable acceptance route

The newer [hosted evidence](acceptance/2026-11-02-hosted-validation.json) now verifies native amd64 source/runtime, kind 1.35.8/1.36.4/1.37.0 and PVC recovery, plus native amd64/arm64 image checks. Earlier “hosted/native amd64 unexecuted” statements below are historical. The corrected full workflow passed at d261de7; newer PR revisions require their own current status. Live-model interpretations remain unverified/mock-backed.

Latest follow-up: native arm64 Kubernetes 1.36.4/1.37.0 incident acceptance and QEMU-amd64 app execution now have [actual evidence](security/findings/2026-11-02-source-compatibility.json). Native amd64 hardware and hosted workflows remain unexecuted. Historical 1.35.8 sections below retain original versions/flags; that unchanged successful check was not repeated. The current source environment is .venv-source with explicitly patched SQLite; older .venv-audit/.venv-readiness examples are historical and now rejected for app/database startup. For amd64 checks only, the dedicated profile used Colima's supported --binfmt=true; native runs need no emulation.

## Supported route available on this Mac

Hardware virtualization reports `kern.hv_support: 1` on macOS 26.2 arm64. Through supported Homebrew bottles, this session installed Colima 0.10.3/Lima 2.2.1, Docker CLI 29.9.2, Buildx 0.38.1, kind 0.33.0, kubectl 1.37.2 and Helm 4.3.1. The test instead selects checksum-verified kubectl 1.35.8 and Helm 3.19.0 to match its Kubernetes 1.35.8 target and declared chart setup.

A dedicated `veriqta-acceptance` Colima VM using Apple's Virtualization.framework started successfully. Host volume mounts and SSH-agent forwarding are disabled; automatic Docker-context activation and SSH config modification are disabled. The Docker daemon reports Linux aarch64, server 29.5.2. A disposable `busybox:1.37.0` container executed `/bin/true` with `--network none` and exited successfully. This establishes actual container execution, not merely CLI installation. No restriction bypass or remote runtime was used.

References: [Colima installation](https://colima.run/docs/installation/), [mount/context configuration](https://colima.run/docs/configuration/), [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/) and [official kind 0.33 release/node digests](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0).

## Actual acceptance attempts

The first real run built a Linux arm64 application image, created a dedicated kind Kubernetes 1.35.8 cluster, installed its networking/storage provisioner and bound the application PVC. Helm timed out because the application crashed at startup. A diagnostic rerun captured the cause: Helm quoted the large integer default as `KI_MAX_DB_BYTES="1e+08"`, rejected by the application's integer schema. The chart now casts integer environment values through `int64` before quoting. A Helm-to-Settings regression test and chart invariant check pass. Neither failed attempt is a successful cluster acceptance result. The final outcome is recorded below after actual execution.

## Exact local commands

On a normal Linux Docker machine, install a supported Docker Engine using the [official guide](https://docs.docker.com/engine/install/), start its daemon using that platform's documented method, and install Python 3.12+. Use Docker Desktop's supported WSL2 integration on Windows; run these commands inside WSL2. Do not expose a remote unauthenticated Docker socket. These alternative host setup paths have not been tested here.

On macOS with Homebrew, the route actually used was:

```sh
brew install colima docker docker-buildx kind kubernetes-cli helm
colima start veriqta-acceptance --vm-type vz --cpus 2 --memory 4 --disk 25 \
  --mount none --activate=false --ssh-config=false --binfmt=false
```

Docker CLI-only packages need Buildx; on Homebrew set `cliPluginsExtraDirs` to `/opt/homebrew/lib/docker/cli-plugins` in your dedicated Docker config. Keep that directory private and do not copy registry credentials into the project. To use the dedicated profile without switching another context:

```sh
export DOCKER_HOST="unix://$HOME/.colima/veriqta-acceptance/docker.sock"
# Optional dedicated DOCKER_CONFIG: config.json with the Buildx plugin location above.
docker info
docker buildx version
# This checks an actual container can execute, without host mounts or container network access:
docker run --rm --network none busybox:1.37.0 /bin/true
```

From this repository, on a machine with a running Docker daemon and Python 3.12+:

```sh
make setup PYTHON=python3.12
bash scripts/install-kind-tools.sh v1.35.8 "$PWD/.capture/tools/bin"
export PATH="$PWD/.capture/tools/bin:$PATH"
export KIND_EXPERIMENTAL_PROVIDER=docker
bash scripts/smoke.sh
```

This downloads official kind 0.33.0, a matching kubectl binary and Helm 3.19.0, verifies published SHA-256 checksums, and installs only in the selected local directory. The smoke rejects remote Docker endpoints before contacting a daemon and forces the Docker provider. It creates its own private temporary kubeconfig and only the dedicated `veriqta-investigator-demo` cluster. It refuses an occupied name. It installs the source-built app via Helm with real Kubernetes evidence and a clearly labelled mock provider. No provider key or paid model request is required. It checks restricted-credential reads/denials, all three sample failures, exports, unchanged persistent reports across restart, manual corrections, fresh linked verification and deletion. The trap deletes only the owned cluster and temporary credentials; `.data/smoke-result.json` records versions and cleanup status after a successful run. Raw failure diagnostics stay in ignored `.capture/` and must be reviewed before sharing.

In this prepared workspace, use `VENV=.venv-audit` for the existing verified Python environment, `DOCKER_CONFIG="$PWD/.capture/docker"`, and PATH entries for `.capture/tools/bin`, `/tmp/darwin-arm64` and `/opt/homebrew/bin`. The temporary `/tmp` Helm binary is not a permanent installation path; normal users should install Helm as above or follow the CI setup.

After testing, stop only this runtime profile: `colima stop veriqta-acceptance`. Optional deletion of its local cached images/disks is `colima delete --force veriqta-acceptance`; leave other profiles untouched. Homebrew tools remain installed unless explicitly uninstalled by the owner.

## Hosted-runner route prepared, not triggered

`.github/workflows/cluster-smoke.yml` is a manual/reusable workflow on a fresh `ubuntu-24.04` VM, not a restricted container runner. It verifies the real Docker daemon and Buildx, installs checksum-verified kind/matching kubectl/Helm and locked Python dependencies, and runs the same `bash scripts/smoke.sh`. Its matrix targets Kubernetes 1.35.8, 1.36.4 and 1.37.0 using official immutable node digests. Failures are not hidden or marked continue-on-error. Each job has a timeout, read-only repository permissions, no provider/deployment secrets, a synthetic summary artifact only and owned-cluster cleanup. The validation workflow reuses it. No `pull_request_target` or publication action is introduced.

No push or workflow dispatch has occurred. To execute this route later, the owner must explicitly authorise placing these changes on GitHub, then manually run **Disposable Kubernetes acceptance** in Actions (or authorise its separate trigger). Prepared workflow YAML is not evidence that any hosted matrix job passed.

Live-model accuracy, real provider credentials/billing, independent security review, ingress/NetworkPolicy enforcement, PVC backup/rollback and architectures not actually executed remain separate acceptance requirements. A mock-provider smoke cannot establish those results.

## Successful final execution

**Passed** on 2026-11-01 (America/Los_Angeles), exit 0. The machine-readable [acceptance record](acceptance/2026-11-01-kind-1.35.8-mock.json) contains UTC completion time, actual tool/server versions, application image ID/architecture, report identifiers, observation counts, three fresh verification outcomes and confirmed cluster cleanup. Evidence source is **Kubernetes**, provider is **mock**. A mock interpretation is not live-model diagnostic evidence.

The successful run used Kubernetes/kubectl 1.35.8, kind 0.33.0, Helm 3.19.0 and the dedicated Linux arm64 Docker runtime. It passed real restricted-credential reads and denials (including actual log denial and correct subresource authorisation reviews), independent SDK collection, all three app investigations/exports, full report equality after restart, all three external corrections/fresh follow-ups, deletion, and absence of the owned cluster after cleanup. Native Linux arm64 image build and execution are now verified for this test path; Linux amd64 and the 1.36/1.37 hosted matrix remain unexecuted.

Failures were resolved rather than skipped: decimal Helm integer serialization, correct kubectl subresource review syntax, nullable empty EndpointSlice endpoints, and repeated-exit observations during container backoff transitions. These findings have regression checks. A current Ready container with only a historical exit remains outside the repeated-failure observation.

The current local suite passes **58 tests**, lint/format/type/document checks and Helm lint. One upstream TestClient deprecation warning remains. This is a specific local acceptance result, not full validation, enterprise readiness, a live-model benchmark or an independent security review. Additional security requirements, including a dedicated log timestamp-lookback control, sustained load/failure injection, optional ingress/NetworkPolicy and release signing/provenance, remain tracked separately.


The post-acceptance local-only runtime guard has a separate regression test: remote SSH/TCP contexts are rejected without invoking Docker, while a local Unix socket proceeds to the daemon/setup checks. This guard was tested locally after the successful cluster run; the application image and investigation logic were unchanged.
