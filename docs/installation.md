# Installation and local demonstration

## Source demonstration: no cluster or provider account

Prerequisites: Python 3.12+ **linked to SQLite 3.54.1+**, Git and internet for initial dependencies. Installing the sqlite3 command or upgrading pip does not necessarily patch the library loaded by Python. The default path uses synthetic fixture evidence and a deterministic mock provider; no model account/key is needed.

### Source interpreter setup

Use a maintained interpreter that passes the preflight. On macOS, this reproducible local route needs Homebrew and Xcode Command Line Tools (`xcrun --find clang` must succeed):

```sh
# From this checkout. Installs only into a NEW private workspace prefix.
# brew.sh provides the supported Homebrew installation if not already installed.
PATH="/opt/homebrew/bin:$PATH" bash scripts/bootstrap-source-python.sh "$PWD/.local/python-3.12.16"
make setup PYTHON="$PWD/.local/python-3.12.16/bin/python3.12" VENV=.venv-source
make preflight VENV=.venv-source
export KI_TOKEN="$(.venv-source/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
make run VENV=.venv-source
```

The bootstrap uses the official maintained CPython 3.12.16 security release, verifies its published SHA-256, builds with bundled Expat and maintained Homebrew SQLite/OpenSSL, and uses `make altinstall` into that prefix. It does not replace macOS Python/libraries, set loader overrides or disable TLS. `.local/` is ignored by Git and Docker. Choose another new prefix for a future interpreter release; preserve databases/backups, then recreate a virtual environment with the new interpreter. Version/hash updates require reviewing the [official release](https://www.python.org/downloads/release/python-31216/); an interpreter is also an ongoing dependency.

The Homebrew Python 3.12.16 bottle was attempted here: SQLite linkage was correct, but its pyexpat extension requested a symbol unavailable in this macOS 26.2 system library, preventing ensurepip. That failed setup is not a pass. The source-build route avoids that bottle ABI problem with CPython's bundled patched Expat. A Homebrew or other maintained interpreter on another host may work directly, but verify both its SQLite and normal virtual-environment/stdlib operation rather than assuming it matches this result.

For an existing compatible interpreter on Linux/macOS/WSL2:

```sh
# Replace python3.12 with the maintained interpreter you selected.
python3.12 src/kubeinvestigator/sqlite_runtime.py
make setup PYTHON=python3.12
make preflight
export KI_TOKEN="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
make run
```

Ubuntu 24.04 native amd64 hosted-VM source installation with Homebrew Python 3.12.16/SQLite 3.54.1 now passes 80 tests; see [actual hosted evidence](acceptance/2026-11-02-hosted-validation.json). WSL2 and other distribution/physical-host source setups remain unexecuted. If the distro/interpreter does not supply the required SQLite version, use a supported patched interpreter build or the separately tested container; do not patch system-library files, monkey-patch sqlite3, or bypass the guard. Distribution backports retaining older version numbers are conservatively rejected by this version floor; no silent risk exception is supported. Native Windows source execution is unsupported; use WSL2 with its own verified interpreter.

Install from an accessible source checkout. No public package or image has been published; repository visibility must permit access before public installation can be advertised. Open http://127.0.0.1:8080 and enter your generated token. Retrieve its value privately from your shell variable; do not share it in screenshots or URLs. Select a namespace and Service selector mismatch, describe a problem, and start an investigation. Expect a clearly labelled MOCK report with synthetic evidence. Run Connection checks to inspect configuration. Export JSON or Markdown; a fixture follow-up explicitly cannot verify a real correction.

To test the macOS environment: `make test check VENV=.venv-source`. For the default .venv use `make test check`. Stop with Ctrl+C. Remove local retained data only when no longer needed: `rm -rf .data`. This directory contains only application-local data and private demonstration tokens. Remove `.venv` to remove the development environment.

## Source deployment security prerequisite

`make setup` checks the selected interpreter **before** creating a virtual environment. `make preflight` prints the Python/SQLite versions loaded in that environment. `make run`, application storage initialization and backup/restore maintenance refuse affected versions with upgrade instructions before opening SQLite or creating a database. There is no environment-variable bypass. A version prerequisite is not a complete vulnerability assessment; review current advisories before deployment.

The previous bundled test interpreter loaded SQLite 3.53.1 with FTS5 enabled. It is retained only as rejection-test evidence; it is not the source interpreter selected by the new installation recipe. Container remediation did not patch it. Source linkage and final-container linkage are verified and recorded separately in [security findings](security/findings.md).

## Real Kubernetes evidence in a disposable kind cluster

Prerequisites: running Docker daemon, kind, kubectl, Helm 3.19+, Python environment from above, registry access, and at least several GiB of free memory/disk for kind and builds. The dedicated smoke passed locally on Kubernetes 1.35.8 / Linux arm64 using Colima. Target Kubernetes 1.35–1.37; the sample pins the official kind node 1.35.8 image digest. Native arm64 incident acceptance also passed 1.36.4/1.37.0; native amd64 hosted incident/recovery and source/runtime checks now pass, with [recorded evidence](acceptance/2026-11-02-hosted-validation.json). See [runtime installation and acceptance](runtime-acceptance.md) for actual tooling and exact commands. Check the current kind release supports the selected node image before running. No existing production context is accessed. The setup script creates its own dedicated cluster and refuses an existing cluster of the same name.

```sh
bash scripts/demo.sh setup
kubectl --context kind-veriqta-investigator-demo -n veriqta-system port-forward --address 127.0.0.1 svc/investigator 8080:8080
```

Use the private token in `.data/demo-access.env`. The app uses its in-cluster service account with per-namespace read-only Roles. The installer uses the disposable cluster administrator context to create RBAC, PVCs and samples; that credential is never mounted in the app. All evidence is real Kubernetes evidence; interpretations remain labelled MOCK. Waits are bounded. If setup fails, inspect `kubectl --context kind-veriqta-investigator-demo get pods -A` and image pull events, correct local prerequisites, then clean up before trying again.

```sh
bash scripts/demo.sh correct-service
# Use Run fresh follow-up in the UI.
bash scripts/demo.sh correct-image
bash scripts/demo.sh correct-crash
# Stop port-forward, then remove only the named demo cluster:
bash scripts/demo.sh cleanup
```

The scripts refuse an unrelated active context and every sample mutation pins the dedicated kind context explicitly. Smoke cleanup deletes its newly created named cluster independently of the active context. CI entrypoint `bash scripts/smoke.sh` owns setup, all three API investigations and exports, actual restricted-credential API denials, unchanged reports across restart, all three manual corrections, fresh linked follow-ups, deletion, and cleanup. It refuses a pre-existing demo cluster. Check `.data/smoke-result.json` for local results; the reviewed successful summary is also preserved in the [prior 1.35.8 acceptance record](acceptance/2026-11-01-kind-1.35.8-mock.json) and [current matrix scope](security/findings/2026-11-02-source-compatibility.json); no hosted matrix pass is preclaimed.

## Deploy against an explicitly authorised cluster

Do not run this guide on a cluster without authorisation. Prerequisites: Kubernetes target 1.35–1.37, kubectl, Helm 3.19+, an appropriate StorageClass supporting a single-writer PVC, private namespace access, and registry access. No managed cloud distribution has been validated. Installer permissions must create the release namespace, ServiceAccount, Secret, Deployment, Service, PVC, and Roles/RoleBindings in the named target namespaces. Runtime permissions are substantially narrower; see [security](security.md).

Build and push an image to **your** registry using your normal approved process. Publishing was not performed by this project. On kind, `kind load docker-image` substitutes for a registry. Replace `YOUR_REGISTRY` and `YOUR_NAMESPACE` below with your authorised names; create target namespaces separately if they do not already exist.

```sh
docker build -t YOUR_REGISTRY/kubeinvestigator:0.1.0 .
# Push only with your own publishing authorisation, then:
kubectl create namespace veriqta-system
umask 077
python3 -c 'import secrets; print("KI_TOKEN="+secrets.token_urlsafe(32))' > /tmp/investigator-access.env
kubectl -n veriqta-system create secret generic investigator-access --from-env-file=/tmp/investigator-access.env
helm lint charts/kubeinvestigator -f examples/values.yaml
helm upgrade --install investigator charts/kubeinvestigator -n veriqta-system   --set existingSecret=investigator-access   --set image.repository=YOUR_REGISTRY/kubeinvestigator   --set 'namespaces={YOUR_NAMESPACE}' --wait --timeout 180s
kubectl -n veriqta-system port-forward --address 127.0.0.1 svc/investigator 8080:8080
```

The private env file contains the access token; transfer it securely, then remove it. Run Connection checks; expect all configured resources to be accessible and no provider call. Readiness checks storage; it does not promise provider or cluster reachability. Empty history is expected. First run with `provider=mock`; this exercises real evidence without model costs. To use OpenAI, follow [provider configuration](provider.md).

Ingress is disabled. Opt-in ingress requires an existing ingress controller and TLS Secret you provision; set `ingress.enabled=true`, `className`, `host` and `tlsSecret`. Secure cookies are enabled automatically. Ensure the controller redirects HTTP to HTTPS and does not log credentials or request bodies. No certificate manager or controller is installed. Default CORS has no cross-origin allowances.

Upgrade with the same `helm upgrade --install` command and an explicitly reviewed image tag. Back up SQLite before upgrading. Roll back via `helm rollback investigator REVISION -n veriqta-system --wait` only when the previous binary supports the current schema; otherwise restore the matching backup. Use `helm history investigator -n veriqta-system` to identify REVISION. No rollback has been tested against a cluster here.

Uninstall with `helm uninstall investigator -n veriqta-system`. The PVC is intentionally retained; inspect and explicitly delete `investigator-data` when its data is no longer required. Delete `investigator-access` separately. Remove only namespaces you created solely for this deployment; never delete a shared target namespace. Roles and RoleBindings are Helm-owned and removed on uninstall.

| Symptom | Check | Remedy |
| --- | --- | --- |
| Startup rejects settings | Required KI_TOKEN, provider/source combination | Generate a 32+ character token; use fixture only with mock |
| 401 / expired session | Token rotation, expiry, restart | Sign in again; sessions expire after one hour |
| 403 namespace | KI_NAMESPACES and per-namespace RoleBinding | Configure explicit scope and installation RBAC |
| Collection unavailable | Connection checks, API reachability, read RBAC | Correct restricted credentials; do not grant cluster-admin |
| Provider failure | Quota, key, model capabilities, provider connectivity | Correct configuration and create a new investigation |
| Pending PVC | StorageClass and capacity | Select a suitable class; no default class is assumed |
| 507 storage limit | Report count, DB/WAL size, free disk | Export/delete data, offline compact or expand storage |
| Empty/incomplete report | Workload name, source, truncation | Narrow scope and verify objects exist; no health guarantee |
