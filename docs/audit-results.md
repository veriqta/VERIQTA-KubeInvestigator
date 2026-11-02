# Current acceptance addendum

The environment blocker and unexecuted cluster assertions in the historical audit below are superseded by the successful [runtime acceptance](runtime-acceptance.md). The run passed Kubernetes 1.35.8 / Linux arm64 installation, real collection/denials, three failures/exports, restart persistence, three corrections/fresh follow-ups, deletion and owned-cluster cleanup. Provider output remained MOCK. Current local tests: 58 passed. No hosted matrix or paid live evaluation ran.

Remaining security and release gaps are in [security verification](security/verification-matrix.md). Other target Kubernetes versions/architectures, optional network/TLS controls, full storage/rollback exercises and live-model quality are not established by this pass.

---

## Historical audit before runtime installation

# Follow-on implementation and acceptance audit

Recorded 2026-11-01, America/Los_Angeles. This audit continues the complete [product brief](product-brief.md); it does not replace its acceptance requirements. Local implementation is stronger, but a cluster acceptance pass and live-model quality have not been established.

## Exact environment blocker

`command -v docker`, `command -v kind`, `command -v kubectl`, and `command -v helm` returned no path. An earlier isolated Helm 3.19.0 download is usable at `/tmp/darwin-arm64/helm`.

Actual command:

```sh
PATH="/tmp/darwin-arm64:$PATH" bash scripts/smoke.sh
```

Actual result: exit **2**, `BLOCKED: missing required tools: docker kind kubectl`.

No Docker daemon was contacted because its CLI is absent. No cluster was created, installed, read or corrected. This is a prerequisite failure, **not a smoke-test pass**. The script now checks all prerequisites and Docker daemon access before attempting cluster creation.

## Fixes made during this audit

- Smoke checks actual allowed/forbidden reads using a short-lived token for the application's installed ServiceAccount, in a private temporary kubeconfig that excludes installer credentials. Write/exec/port-forward permissions are checked using that restricted identity's authorisation reviews; the application still performs no workload writes.
- All three incidents have explicit target names, typed report/evidence validation, JSON/Markdown export checks, complete report comparison across application restart, external sample corrections, linked fresh follow-up timestamps, and deletion checks.
- Smoke cleanup explicitly deletes only the newly owned dedicated cluster, independently of the active kubectl context. Sample mutation commands pin that dedicated context to prevent a later context switch from redirecting them. Failed cluster inventory is no longer treated as an empty inventory.
- Pod-scoped events filter by involvedObject.name. Opt-in crash collection gathers current and previous logs for one observed crashing container. Nested EndpointSlice truncation is flagged. Oversized pod suggestions and busy preview checks retain actionable HTTP errors.
- Markdown exports now include workload, scenario, source, duration, evidence IDs and structured references. Mock image findings no longer imply that every pull failure contains a manifest-unknown message.
- Provider response size is enforced during bounded HTTP reads, not after loading an arbitrary response. Malformed/negative usage metadata is rejected. Non-ASCII invalid login credentials return 401 instead of a comparison error. Background cleanup is awaited at shutdown; newer-schema rejection closes its connection.
- CI's nonexistent Trivy action reference was corrected to a verified upstream release. All 11 action references and the official Python multi-architecture image-index digest are pinned. Release checksums include Helm .tgz artifacts. Chart hardening/RBAC invariants are executable in `scripts/check_chart.py` and CI.
- Source setup rejects Python below 3.12 with an actionable message. Documentation uses an explicit Python 3.12 setup command. A clean `.venv-audit` installation succeeded.
- Browser tests now wait for each new investigation ID, verify the downloaded report, open evidence with Enter, and check the fixture follow-up's explicit recovery limitation. Genuine screenshots/video and the derived GIF were refreshed.

## Requirements table

“Tested locally” is specific evidence, not cluster certification. “Blocked” means the tools or external authority needed for that acceptance check are unavailable. “Remaining” identifies work beyond successful local checks.

| Requirement | Implemented | Tested locally / supporting command | Blocked or remaining |
| --- | --- | --- | --- |
| Working UI/API and three scenarios | FastAPI, static structured UI, typed reports | `make test VENV=.venv-audit`; `scripts/capture.cjs` runs all three mock-backed forms, evidence, download and fresh follow-up | Real Kubernetes UI journey is not exercised by the cluster smoke; browser run uses fixture evidence |
| Authentication/team workspace | Expiring HttpOnly session, CSRF, logout, restart invalidation, bearer API, rate limits | Session expiry/restart, invalid Unicode credential, protected endpoints, CSRF and login limits in tests/test_audit.py and test_application.py | Real ingress/TLS, proxy rate limiting and full accessibility review remain unverified; individual report isolation is deliberately not implemented |
| Namespace authorisation | API and collector checks; fixed configured namespaces | Unauthorised API/tool requests and invalid/write tools tested | Actual Kubernetes authorisation denial requires the blocked cluster smoke |
| Runtime read-only permissions | Explicit per-namespace Role/Binding; no Secrets/nodes/write/exec | Helm renders plus `scripts/check_chart.py` check allowed resources/verbs and security contexts | Restricted actual API reads/denials and installed RoleBindings are scripted, unexecuted |
| Evidence/redaction/exports | Selected fields, relevant events, optional current/previous logs, bounded lists/logs, redaction, JSON/Markdown | Projection, redaction, nested truncation, log selection, references and export tests; browser JSON download | Actual Kubernetes event/log collection, missing-log permission and workload ownership chains need cluster coverage; arbitrary prose/secret formats can still escape semantic validation/redaction |
| Limits/failure handling | Bounded queue, concurrency, tools, turns, duration, streamed payloads, cancellation, honest provider failure | Time/turn/call/concurrency/cancel, provider error parsing and oversized-stream tests | Real socket/network timeout behaviour and full stress testing remain; cancellation may wait for one underlying socket timeout |
| Persistence/retention/restart | SQLite WAL, schema versioning, interrupted jobs, deletion, capacity limits | Local backup/restore, newer-schema rejection, expiry cleanup, active-job preservation, byte-cap and restart tests | PVC lifecycle, physical disk-full recovery and cluster backup/restore/upgrade/rollback are unexecuted |
| Helm/container/sample installation | Non-root hardened image recipe, scoped chart, sample setup/correction/cleanup | Helm 3.19.0 lint; targets 1.35/1.36/1.37 render; default and optional log/TLS templates pass hardening checks; shell syntax passes | Docker/kind/kubectl absent; no image build/execution, chart installation, sample timing or real recovery pass |
| Smoke acceptance | Strengthened scripts/smoke.sh and smoke.py cover installation, restricted credentials, three incidents/exports, full persistence, three corrections/follow-ups and deletion | Prerequisite-failure test; script syntax, Python lint and review | Entire cluster execution blocked; no successful smoke result exists |
| Deployment/upgrade/rollback/cleanup guides | docs/installation.md, operations.md; context-safe scripts | Relative links, shell syntax, source setup and local SQLite backup/restore tested | Helm upgrade/rollback, storage snapshot/restore and cluster cleanup need disposable execution |
| Observability | Authenticated metrics, fixed metric names, request/investigation IDs, optional external Collector example | API tests and source audit; no sensitive/high-cardinality metric labels added | External Collector/backend export and operational load behaviour unexecuted; costs remain unavailable |
| CI/release preparation | Immutable action/base pins, checks/scanners, chart invariants, unsigned artifacts/SBOM/checksum workflow | Official reference/digest resolution, YAML parsing, package/chart build; local checksums | GitHub jobs, container scan, full gitleaks history scan, SBOM job, signing/provenance and architecture execution remain unverified; publishing prohibited |
| README/docs/diagrams/brand | Public-facing narrative, focused guides, supplied/original marks, editable diagrams, attributed technology strip | Local link/XML checks; browser README image/navigation/theme/mobile rendering | Exact hosted GitHub rendering is unverified; brand/private-reporting/social-preview owner setup remains |
| Authentic demonstration assets | Five real UI screenshots, WebM recording, GIF made from captured frames | Refreshed capture.cjs run; synthetic names and visible MOCK/fixture limitation inspected | No live-provider or real-recovery demonstration is claimed |
| Provider diagnostic quality | Live adapter and six-case opt-in evaluation command | Synthetic HTTP contract/error tests only | No authorised paid evaluation; accuracy, live credentials/capability, actual cost and unsupported-claim rates remain explicitly unverified |
| Community/security/reuse | Apache-2.0 code, separate brand rights, contribution/conduct/security policy, no proprietary backend | Document links and source audit | Owner must establish a verified private reporting route; no channel, release or endorsement is invented |

## Gaps in the smoke test relative to the full brief

The smoke is an acceptance slice, not the whole release audit. It does **not** run the cluster-backed browser UI, force a crash while an investigation is running, wait through configured retention, induce real disk exhaustion, collect opt-in logs/ownership relationships, test ingress/TLS/NetworkPolicy, exercise Helm upgrades/rollbacks/PVC backup restoration, run both container architectures, or measure live-model quality. Several corresponding policies are covered by local component tests; those do not replace real-cluster evidence. Only one configured kind node image is selected per run; rendering three Kubernetes versions is not a three-version smoke matrix.

On a suitable local host, run `make setup PYTHON=python3.12` then `bash scripts/smoke.sh`. Fix actual failures before marking cluster criteria tested. Retain redacted results and actual tool/Kubernetes versions. Paid model evaluation remains outside this authorised work.

No push, publication, tag, external deployment, production access, GitHub setting change or paid model call was performed.
