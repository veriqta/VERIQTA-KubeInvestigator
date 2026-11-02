# Release readiness — 2026-11-02

**The source-installation SQLite gate is resolved for the documented tested profile.** A fresh private CPython 3.12.16 build uses SQLite 3.54.1, bundled Expat 2.9.0 and maintained OpenSSL. Setup/preflight/startup/maintenance reject affected interpreters before database access. Container remediation did not patch the old bundled interpreter; it remains rejected. Current scans have **no findings detected by the recorded scan**, not proof of no vulnerabilities. Source and compatibility evidence is [recorded separately](security/findings/2026-11-02-source-compatibility.json), with earlier evidence preserved.

Verified this pass: 74 macOS source tests plus real HTTP startup/API flow; native arm64 Kubernetes 1.36.4/1.37.0 full incident acceptance/cleanup; amd64 execution under QEMU with 61 installed-image tests; native arm64 Linux source setup in a development container with 73 passed/one Helm-only skip and corrected-fixture static/docs passes. Native amd64 hardware, bare-host Linux/WSL2, hosted workflows and live-model accuracy remain unverified. The earlier successful 1.35.8 incident/recovery checks were not repeated unchanged.

No push, publication, paid call, external workflow trigger or production-cluster access occurred. This is not a production-readiness or independent-security certification.

Real Kubernetes collection and enforcement have been tested. **Mock-backed interpretations do not establish live-model diagnostic accuracy.**

## Reconciliation against both briefs

The [original brief](product-brief.md) and [security addendum](security/specification.md) remain authoritative. The table maps all numbered sections to implementation/evidence and remaining gates. “Verified” describes only the stated environment and test scope.

| Requirements | Implemented / verified evidence | Remaining gate |
| --- | --- | --- |
| Product/reuse, journey, structure, community — original 1–4, 20–21, 25–28, 30; security 19–20 | Standalone self-hosted app, focused README/guides/templates, Apache code/separate brand rights, recorded research, no proprietary backend or unrelated features | Owner review, private security/conduct reporting route; source remains uncommitted/unpublished |
| Architecture/limits — original 5–6; security 5, 8, 13–14 | Modular FastAPI/client/provider/SQLite; typed tools; namespace/resource/call/turn/time/payload/concurrency/cancellation enforcement; bounded summary history and SQL aggregate metrics | Sustained/distributed load and all physical failure modes unverified; provider estimates are not billing caps |
| Kubernetes evidence/RBAC/samples — original 7, 15, 18; security 3–5, 17 | [Repeated final-runtime 1.35.8 incident smoke](acceptance/2026-11-02-alpine-sqlite-incident-mock.json): restricted-credential reads/denials, three incidents/exports, restart persistence, corrections/fresh follow-ups and cleanup | Other Kubernetes versions/architectures; opt-in log/owner collection and cluster-backed browser flow not comprehensively exercised |
| Authentication/report access — original 8; security 2, 7, 12–13 | Sessions/CSRF/expiry/logout, bearer API, rate limits, namespace revocation checked for detail/export/delete/cancel/follow-up; identity headers ignored; error values omitted; correlated security events | Shared trusted-team access intentionally has no individual isolation/OIDC; real ingress/TLS and external audit-log retention unverified |
| Data/model/report safety — original 9–10; security 4–7, 18 | Selected-field allowlist, redaction, safe text rendering/Markdown, strict actions/references, verified TLS/fixed provider URL/no redirects; log lookback/lines/bytes bounded | Semantic prose and unknown/encoded secrets remain fallible; live model/account/cost/accuracy not evaluated |
| Storage/lifecycle — original 11; security 9, 14 | Exclusive writer/maintenance lease; transactional 0→1 migration; malformed/newer schema rejection; integrity-checked offline backup; atomic restore with preserved old snapshot; rollback on SQLite errors; safe HTTP 507; SQL history paging | Real host disk/power loss, unreliable filesystems and future schema downgrade/binary pairs remain unsupported/unverified |
| Recovery/upgrade/rollback — original 13, 24, 29; security 14–16 | [Repeated final-runtime cluster recovery](acceptance/2026-11-02-alpine-sqlite-recovery-mock.json): config upgrade 7→8, Helm rollback, exact report equality, offline PVC backup/restore, fresh child and cleanup | This is same binary/schema 1. No nonexistent older release or future schema downgrade is claimed tested |
| Container/dependencies/CI/release — original 13, 19; security 10–11, 16 | Native Linux arm64 Alpine/Python 3.12.16 execution; signed project-built SQLite 3.54.1 package; non-root/capability/read-only hardening; immutable actions/base; no runtime pip/compiler; exact-image scans/SBOM/checksums; actionlint passes; hosted runtime/matrix/recovery jobs prepared | No findings detected by the recorded current arm64/amd64 scans; SQLite independently verified at 3.54.1. Project-maintained SQLite package needs ongoing review; hosted jobs, native amd64 hardware/Kubernetes, signing/provenance and external review remain unexecuted |
| Compatibility — original 14; security 19 | Patched macOS arm64 source; native arm64 kind 1.35.8 baseline plus 1.36.4/1.37.0; QEMU amd64 app execution; Helm 3.19.0; Linux-container source setup explicitly recorded | Native arm64 1.36.4/1.37.0 incident tests now pass; native amd64 hardware/Kubernetes, bare-host Linux/WSL2 and managed clouds remain unverified |
| UI/docs/identity/assets — original 12, 22–24; security 1, 15, 18 | Refreshed genuine mock/fixture PNGs/video/GIF; capture source/hash manifest; original/editable diagrams and marks; attribution; locked optional authoring tools; threat model and recovery/config/API guides | Exact hosted GitHub rendering, full accessibility review, brand/legal approval and owner social-preview setup remain separate |
| Observability — original 16; security 12 | Fixed operational counters, timestamps/request/investigation IDs, action-level security records without raw evidence/credentials; optional collector example | External collector/export, durable/tamper-proof audit storage and measured production sizing unverified |
| Tests/evaluation/final acceptance — original 17–18, 27, 29; security 16 | Clean patched-installer source setup; 74-test patched macOS source suite, 61 installed-image tests under amd64 emulation, 73 Linux-container source passes/one explicit Helm skip, loaded-SQLite/FTS5/TLS checks; static/Helm/browser/scanner checks; incident and recovery smoke repeated for runtime change | Full brief is not accepted while security/compatibility/live evaluation/release gates remain |

## Findings and mitigations

[Scan findings](security/findings.md) reconciles each of the nine CVEs, its binary packages/versions, fixed-version availability, inherited source layers, exposure and remediation. The previous Debian image had 45 HIGH/185 total OS findings. The new pinned official Python/Alpine runtime omits the affected admin/ACL/systemd/Perl components and updates ncurses. SQLite needed an independently verified fix: the first Alpine candidate scanned clean but loaded vulnerable 3.53.4. The final runtime installs a signed project-built 3.54.1 package from checksum-verified official upstream source, preserving FTS5 and apk inventory. Compiler, source, packaging tools and signing private key stay outside runtime. The project now owns this package's update/review lifecycle until a suitable vendor update replaces it.

The [earlier exact remediation-runtime evidence](security/findings/2026-11-02-final-runtime.json) records the local OCI index, runtime manifest/configuration digests, archive hash, Trivy 0.76.1 and database update/download timestamps. That recorded scan: **38 OS packages, 39 Python packages, no findings detected by the recorded scan (0 returned vulnerability/secret records); HIGH/CRITICAL gate exit 0**, with no suppression. The incident and recovery runs have identical runtime manifest/config digests; volatile BuildKit attestation metadata explains their different outer indexes. A final SPDX SBOM and full scan are linked from the findings report. This is native arm64 evidence; no other architecture or future scan result is inferred.

**Source gate resolved, with explicit scope:** the supported macOS recipe now builds upstream CPython in a private prefix and verifies its actual SQLite linkage. The old interpreter is not modified and is rejected. A Linux-container source check is additional evidence, not a bare-host installation claim. Homebrew's Python bottle failed Expat linkage on this Mac; the upstream build route is the tested installation, and the failed bottle is not counted as supported here.

**Maintenance obligation:** the project must appoint a reviewer/owner for the custom SQLite package and source-interpreter pin, review official release/advisory feeds before deployment/release, run the new checksum/release check, update pins/minimum floors together, and repeat relevant tests/scans for fixes. No continuous monitoring or independently reviewed release provenance is implemented. See [the process](../packaging/sqlite/README.md#detection-ownership-and-update-gate).

Local functional defects addressed in this pass include missing offline maintenance, accidental multi-worker access, non-atomic migration setup, failure rollback, credential reflection in validation errors, unbounded history/evidence polling and missing log timestamp lookback. Physical full-volume terminal-state persistence may still fail; the API reports storage failures and restart marks retained unfinished jobs interrupted. Schema downgrade requires a matching backup/binary rather than an untested image rollback.

## Commands and execution boundaries

Current source and compatibility execution is recorded in [the new evidence summary](security/findings/2026-11-02-source-compatibility.json). The old rejected interpreter is not used for source startup. Representative successful source commands:

```sh
PATH="/opt/homebrew/bin:$PATH" bash scripts/bootstrap-source-python.sh "$PWD/.local/python-3.12.16"
make setup PYTHON="$PWD/.local/python-3.12.16/bin/python3.12" VENV=.venv-source
make preflight test check VENV=.venv-source
.venv-source/bin/python scripts/check_sqlite_update.py
```

The bootstrap refuses an existing prefix; use a new prefix for a new build, and retain databases/backups. The earlier 1.35.8 incident/PVC recovery and container remediation records are retained. Only newly untested Kubernetes versions and architectures were added here; the application/runtime version guard changed, so exact updated deployment images were scanned and exercised. No unchanged 1.35.8 acceptance was repeated.

After source review and **separate explicit authorisation to place changes on GitHub**, run **Disposable Kubernetes acceptance** in Actions. It executes the three-version real-cluster mock matrix plus focused recovery job on fresh Ubuntu 24.04 VMs. Run **Validate** for the static/dependency/container/secret/licence gates. Future OS/dependency findings must remain visible and block the unchanged container gate. Validate and release preparation now independently check the loaded runtime SQLite/TLS/tooling profile. No hosted workflow has run in this work. Run **Prepare release artifacts** only after gates are satisfied and owner-authorised; it creates candidate artifacts, not a public package or signed release. Signing/provenance require a reviewed trusted publishing/attestation path and appropriate owner permissions; no signature is claimed.

For live evaluation, first authorise paid calls, review candidate model availability, and supply your own provider key **only to the server Secret/environment** as described in [provider setup](provider.md). Use an authorised disposable sample cluster, not production, with `KI_PROVIDER=openai`, `KI_SOURCE=kubernetes`, `KI_MODEL=YOUR_APPROVED_MODEL` and server-only `KI_API_KEY`. Keep the team token private. Then, and only then:

```sh
.venv/bin/python scripts/evaluate.py --acknowledge-paid-calls --url http://127.0.0.1:8080
```

Review every case for incorrect diagnosis and unsupported claims; null review fields are not passes. Costs remain unavailable until actual provider usage/pricing is established. No paid model call was made here.

## Remaining release blockers and next action

| Gate | Next concrete action |
| --- | --- |
| Hosted/native amd64 and CI interpreter route unexecuted | After explicit owner authorisation, place reviewed changes on GitHub and run Validate/Disposable Kubernetes acceptance. Local QEMU results do not close native hardware testing. |
| SQLite/CPython maintenance ownership and release trust | Assign a maintainer; review source/checksum/linkage and licence obligations; approve the documented update gate. Configure and verify signing/provenance before describing artifacts as trusted signed releases. |
| Live-provider quality/account/cost unverified | Separately authorise a bounded paid evaluation and provide server-only credentials; review every diagnosis/unsupported claim. No paid call was made here. |
| Production-facing controls and unclaimed environments | Exercise authorised staging ingress/TLS/CNI and physical storage recovery/load as relevant before making those claims; managed clouds and bare-host Linux/WSL2 require their own execution. No production access is needed or authorised. |
| Owner governance/external review | Verify private vulnerability/conduct channels, brand rights and independent review before public release. No publication/settings change is performed here. |
