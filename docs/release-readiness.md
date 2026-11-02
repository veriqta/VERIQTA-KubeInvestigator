# Release readiness — 2026-11-02

## Current hosted CI milestone

**The corrected validation workflow passed all ten jobs at revision d261de7**, [run 41473405003](https://github.com/veriqta/VERIQTA-KubeInvestigator/actions/runs/41473405003). [Durable evidence](acceptance/2026-11-02-hosted-validation.json) records the exact revision, job outcomes, downloaded synthetic acceptance summaries and native image reports. This supersedes the older “hosted unexecuted” state retained in historical snapshots.

- Ubuntu 24.04 native amd64 source setup: Python 3.12.16/SQLite 3.54.1, **80 tests**, lint/format/types/docs, dependency audit and licence check passed.
- Native amd64 Kubernetes **1.35.8, 1.36.4 and 1.37.0** full incident acceptance and schema-1 PVC recovery/config rollback passed, with cleanup.
- Both native amd64 and arm64 final runtime jobs passed architecture, SQLite/FTS5/TLS checks and exact Docker-archive HIGH/CRITICAL gates. Their recorded Trivy 0.76.1 scans have **no findings detected by the recorded scan**; no claim of no vulnerabilities follows.
- PR secret scanning now reads commit metadata with job-only read access and has comments disabled. The hosted pass covered **one PR commit**, not the complete repository history. An independent Gitleaks 8.30.1 full-history audit returned six matches, all verified upstream **public signing fingerprints** in retained image metadata. [Review record](security/findings/2026-11-02-history-secret-review.json) preserves exit 1, exact locations and classification. No suppressions, ignores or history rewrite were introduced; do not label that automated full-history scan clean.

The earlier failures were a denied PR-commits API call and an unreadable multi-architecture OCI archive. Neither was a completed vulnerability analysis. Per-architecture Docker archives and explicit image-lineage checks fix the scanner input without weakening the gate. Main pushes and PRs remain validated; development push/PR duplication is removed. No runtime dependency or application behaviour was changed by this CI milestone.


## Earlier local baseline and requirement reconciliation

**The source-installation SQLite gate is resolved for the documented tested profile.** A fresh private CPython 3.12.16 build uses SQLite 3.54.1, bundled Expat 2.9.0 and maintained OpenSSL. Setup/preflight/startup/maintenance reject affected interpreters before database access. Container remediation did not patch the old bundled interpreter; it remains rejected. Current scans have **no findings detected by the recorded scan**, not proof of no vulnerabilities. Source and compatibility evidence is [recorded separately](security/findings/2026-11-02-source-compatibility.json), with earlier evidence preserved.

Verified in the earlier local baseline: 74 macOS source tests plus real HTTP startup/API flow; native arm64 Kubernetes 1.36.4/1.37.0 full incident acceptance/cleanup; amd64 execution under QEMU with 61 installed-image tests; native arm64 Linux source setup in a development container with 73 passed/one Helm-only skip and corrected-fixture static/docs passes. Native hosted amd64 and Ubuntu source execution are now verified above; WSL2, physical-host installation, other distributions and live-model accuracy remain unverified. The earlier successful 1.35.8 incident/recovery checks were not repeated unchanged.

Development validation does not constitute a release, production-readiness certification or independent security assessment. No release/package publication, paid model evaluation, production access or external application deployment formed part of these checks.

Real Kubernetes collection and enforcement have been tested. **Mock-backed interpretations do not establish live-model diagnostic accuracy.**

## Reconciliation against both briefs

The [original brief](product-brief.md) and [security addendum](security/specification.md) remain authoritative. The table maps all numbered sections to implementation/evidence and remaining gates. “Verified” describes only the stated environment and test scope.

| Requirements | Implemented / verified evidence | Remaining gate |
| --- | --- | --- |
| Product/reuse, journey, structure, community — original 1–4, 20–21, 25–28, 30; security 19–20 | Standalone self-hosted app, focused README/guides/templates, Apache code/separate brand rights, recorded research, no proprietary backend or unrelated features | Owner review, private security/conduct reporting route; source committed/pushed to the private repository; no release/package published |
| Architecture/limits — original 5–6; security 5, 8, 13–14 | Modular FastAPI/client/provider/SQLite; typed tools; namespace/resource/call/turn/time/payload/concurrency/cancellation enforcement; bounded summary history and SQL aggregate metrics | Sustained/distributed load and all physical failure modes unverified; provider estimates are not billing caps |
| Kubernetes evidence/RBAC/samples — original 7, 15, 18; security 3–5, 17 | [Repeated final-runtime 1.35.8 incident smoke](acceptance/2026-11-02-alpine-sqlite-incident-mock.json): restricted-credential reads/denials, three incidents/exports, restart persistence, corrections/fresh follow-ups and cleanup | The recorded local arm64 and hosted amd64 matrix is verified; opt-in log/owner collection and cluster-backed browser flow not comprehensively exercised |
| Authentication/report access — original 8; security 2, 7, 12–13 | Sessions/CSRF/expiry/logout, bearer API, rate limits, namespace revocation checked for detail/export/delete/cancel/follow-up; identity headers ignored; error values omitted; correlated security events | Shared trusted-team access intentionally has no individual isolation/OIDC; real ingress/TLS and external audit-log retention unverified |
| Data/model/report safety — original 9–10; security 4–7, 18 | Selected-field allowlist, redaction, safe text rendering/Markdown, strict actions/references, verified TLS/fixed provider URL/no redirects; log lookback/lines/bytes bounded | Semantic prose and unknown/encoded secrets remain fallible; live model/account/cost/accuracy not evaluated |
| Storage/lifecycle — original 11; security 9, 14 | Exclusive writer/maintenance lease; transactional 0→1 migration; malformed/newer schema rejection; integrity-checked offline backup; atomic restore with preserved old snapshot; rollback on SQLite errors; safe HTTP 507; SQL history paging | Real host disk/power loss, unreliable filesystems and future schema downgrade/binary pairs remain unsupported/unverified |
| Recovery/upgrade/rollback — original 13, 24, 29; security 14–16 | [Repeated final-runtime cluster recovery](acceptance/2026-11-02-alpine-sqlite-recovery-mock.json): config upgrade 7→8, Helm rollback, exact report equality, offline PVC backup/restore, fresh child and cleanup | This is same binary/schema 1. No nonexistent older release or future schema downgrade is claimed tested |
| Container/dependencies/CI/release — original 13, 19; security 10–11, 16 | Native Linux arm64 Alpine/Python 3.12.16 execution; signed project-built SQLite 3.54.1 package; non-root/capability/read-only hardening; immutable actions/base; no runtime pip/compiler; exact-image scans/SBOM/checksums; actionlint passes; hosted runtime/matrix/recovery jobs prepared | No findings detected by the recorded current arm64/amd64 scans; SQLite independently verified at 3.54.1. Project-maintained SQLite package needs ongoing review; native hosted jobs now pass; full-history scan nonzero public-fingerprint review, signing/provenance and external review remain separate |
| Compatibility — original 14; security 19 | Patched macOS arm64 source; native arm64 kind 1.35.8 baseline plus 1.36.4/1.37.0; QEMU amd64 app execution; Helm 3.19.0; Linux-container source setup explicitly recorded | Both native architectures and amd64 Kubernetes matrix verified; physical-host/WSL2/other distro and managed-cloud profiles remain unverified |
| UI/docs/identity/assets — original 12, 22–24; security 1, 15, 18 | Refreshed genuine mock/fixture PNGs/video/GIF; capture source/hash manifest; original/editable diagrams and marks; attribution; locked optional authoring tools; threat model and recovery/config/API guides | Exact hosted GitHub rendering, full accessibility review, brand/legal approval and owner social-preview setup remain separate |
| Observability — original 16; security 12 | Fixed operational counters, timestamps/request/investigation IDs, action-level security records without raw evidence/credentials; optional collector example | External collector/export, durable/tamper-proof audit storage and measured production sizing unverified |
| Tests/evaluation/final acceptance — original 17–18, 27, 29; security 16 | Clean patched-installer source setup; 80-test patched macOS and hosted Ubuntu source suites, 61 installed-image tests under amd64 emulation, 73 Linux-container source passes/one explicit Helm skip, loaded-SQLite/FTS5/TLS checks; static/Helm/browser/scanner checks; incident and recovery smoke repeated for runtime change | Full brief is not accepted while security/compatibility/live evaluation/release gates remain |

## Findings and mitigations

[Scan findings](security/findings.md) reconciles each of the nine CVEs, its binary packages/versions, fixed-version availability, inherited source layers, exposure and remediation. The previous Debian image had 45 HIGH/185 total OS findings. The new pinned official Python/Alpine runtime omits the affected admin/ACL/systemd/Perl components and updates ncurses. SQLite needed an independently verified fix: the first Alpine candidate scanned clean but loaded vulnerable 3.53.4. The final runtime installs a signed project-built 3.54.1 package from checksum-verified official upstream source, preserving FTS5 and apk inventory. Compiler, source, packaging tools and signing private key stay outside runtime. The project now owns this package's update/review lifecycle until a suitable vendor update replaces it.

The [earlier exact remediation-runtime evidence](security/findings/2026-11-02-final-runtime.json) records the local OCI index, runtime manifest/configuration digests, archive hash, Trivy 0.76.1 and database update/download timestamps. That recorded scan: **38 OS packages, 39 Python packages, no findings detected by the recorded scan (0 returned vulnerability/secret records); HIGH/CRITICAL gate exit 0**, with no suppression. The incident and recovery runs have identical runtime manifest/config digests; volatile BuildKit attestation metadata explains their different outer indexes. A final SPDX SBOM and full scan are linked from the findings report. This is native arm64 evidence; no other architecture or future scan result is inferred.

**Source gate resolved, with explicit scope:** the supported macOS recipe now builds upstream CPython in a private prefix and verifies its actual SQLite linkage. The old interpreter is not modified and is rejected. A Linux-container source check is additional evidence, not a bare-host installation claim. Homebrew's Python bottle failed Expat linkage on this Mac; the upstream build route is the tested installation, and the failed bottle is not counted as supported here.

**Maintenance obligation:** the project must appoint a reviewer/owner for the custom SQLite package and source-interpreter pin, review official release/advisory feeds before deployment/release, run the new checksum/release check, update pins/minimum floors together, and repeat relevant tests/scans for fixes. No continuous monitoring or independently reviewed release provenance is implemented. Hosted evidence now validates the configured source/runtime/Kubernetes profiles, not these governance obligations. See [the process](../packaging/sqlite/README.md#detection-ownership-and-update-gate).

Local functional defects addressed in the local baseline include missing offline maintenance, accidental multi-worker access, non-atomic migration setup, failure rollback, credential reflection in validation errors, unbounded history/evidence polling and missing log timestamp lookback. Physical full-volume terminal-state persistence may still fail; the API reports storage failures and restart marks retained unfinished jobs interrupted. Schema downgrade requires a matching backup/binary rather than an untested image rollback.

## Commands and execution boundaries

Current source and compatibility execution is recorded in [the new evidence summary](security/findings/2026-11-02-source-compatibility.json). The old rejected interpreter is not used for source startup. Representative successful source commands:

```sh
PATH="/opt/homebrew/bin:$PATH" bash scripts/bootstrap-source-python.sh "$PWD/.local/python-3.12.16"
make setup PYTHON="$PWD/.local/python-3.12.16/bin/python3.12" VENV=.venv-source
make preflight test check VENV=.venv-source
.venv-source/bin/python scripts/check_sqlite_update.py
```

The bootstrap refuses an existing prefix; use a new prefix for a new build, and retain databases/backups. The earlier 1.35.8 incident/PVC recovery and container remediation records are retained. Only newly untested Kubernetes versions and architectures were added here; the application/runtime version guard changed, so exact updated deployment images were scanned and exercised. No unchanged 1.35.8 acceptance was repeated.

The owner-authorised pushes have executed Validate and its reusable disposable-cluster workflow. The corrected code revision's ten jobs passed as recorded above. Current PR check status remains authoritative for later documentation commits. Prepare release artifacts remains manual and has not been dispatched; it creates unsigned candidates only. No publication, deployment or signature is claimed. Future findings must remain visible and fail the unchanged security gate.

For live evaluation, first authorise paid calls, review candidate model availability, and supply your own provider key **only to the server Secret/environment** as described in [provider setup](provider.md). Use an authorised disposable sample cluster, not production, with `KI_PROVIDER=openai`, `KI_SOURCE=kubernetes`, `KI_MODEL=YOUR_APPROVED_MODEL` and server-only `KI_API_KEY`. Keep the team token private. Then, and only then:

```sh
.venv/bin/python scripts/evaluate.py --acknowledge-paid-calls --url http://127.0.0.1:8080
```

Review every case for incorrect diagnosis and unsupported claims; null review fields are not passes. Costs remain unavailable until actual provider usage/pricing is established. No paid model call was made here.

## Remaining release blockers and next action

| Gate | Next concrete action |
| --- | --- |
| Full-history automated secret-scan status | Retain the nonzero full-history report and independently review the six public-fingerprint classifications; agree an explicit public-data handling policy before claiming an automated clean-history gate. No ignore/baseline was silently added. |
| SQLite/CPython maintenance ownership and release trust | Assign a maintainer; review source/checksum/linkage and licence obligations; approve the documented update gate. Configure and verify signing/provenance before describing artifacts as trusted signed releases. |
| Live-provider quality/account/cost unverified | Separately authorise a bounded paid evaluation and provide server-only credentials; review every diagnosis/unsupported claim. No paid call was made here. |
| Production-facing controls and unclaimed environments | Exercise authorised staging ingress/TLS/CNI and physical storage recovery/load as relevant before making those claims; managed clouds and bare-host Linux/WSL2 require their own execution. No production access is needed or authorised. |
| Owner governance/external review | Verify private vulnerability/conduct channels, brand rights and independent review before public release. No publication/settings change is performed here. |
