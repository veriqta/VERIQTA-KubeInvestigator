# Archived status — superseded

Historical snapshot preserved for traceability. Pending statements describe that earlier checkpoint, not current support. See [current readiness](../release-readiness.md).

# Current acceptance status

The later [runtime acceptance record](../runtime-acceptance.md) supersedes all earlier tool-blocker statements below. Actual cluster acceptance passed for Kubernetes 1.35.8 / Linux arm64 with real Kubernetes evidence and a labelled mock provider. Restricted reads/denials, three incidents and exports, persistence after restart, three corrections/fresh follow-ups, deletion and owned-cluster cleanup passed. Current patched macOS suite: 80 passing tests; native arm64 1.36.4/1.37.0 and QEMU-amd64/source follow-up scopes are in [new evidence](../security/findings/2026-11-02-source-compatibility.json). The focused same-schema PVC backup/restore and Helm configuration upgrade/rollback also passed; see [the dated recovery record](../acceptance/2026-11-02-storage-recovery-mock.json). The current complete original-brief/security-addendum reconciliation is [release readiness](../release-readiness.md); it supersedes the historical checklist below. The final container scan now passes following component removal and verified SQLite remediation; patched source setup/startup checks are verified separately; package-maintenance review and remaining release gates are explicit in that report. The [corrected hosted validation](../acceptance/2026-11-02-hosted-validation.json) now verifies native amd64 source/runtime/Kubernetes and both native image architectures. Live-model quality remains unverified; the complete product/security brief is not marked accepted.

---

# Historical requirements checklist before real-cluster acceptance

The full accepted [product brief](../product-brief.md) remains the source of truth. IDs below correspond to its numbered sections. “Implemented” describes code/docs present; “local pass” describes exercised local behaviour; “partial” identifies a remaining acceptance gap. No cluster/live-model claim follows from mock tests.

| Brief | Status and implementation evidence | Validation / remaining work |
| --- | --- | --- |
| 1 Purpose / reuse | Implemented: README, standalone server, no VERIQTA backend | Local fixture app and UI pass |
| 2 Working approach | Connected verified empty veriqta remote; architecture/plan/decision log/checklist | No prior files/user changes existed; no push |
| 3 First-release scenarios | collector.py, analysis.py, engine.py; scenarios.md | Three mock API/browser workflows pass; actual cluster pending |
| 4 Journey / errors | app.py + static UI; installation.md | Login/create/progress/evidence/export/followup exercised; real correction smoke unrun |
| 5 Architecture | Modular FastAPI/Python client/provider/SQLite; report schema and PRAGMA migration | Local lifecycle/type check pass; container and PVC pending |
| 6 Bounded loop | Typed tools; queue/concurrency/duration/calls/turns/payload limits/cancel | Budget/cancel/concurrency/component tests pass; socket cancellation overrun documented |
| 7 Kubernetes tools/RBAC | Selected-field pods/logs/events/services/EndpointSlices/owners; per-namespace chart Roles | Projection/timeout/Role render checks pass; restricted actual API access smoke pending |
| 8 Team access | Random token, session expiry/logout/restart invalidation, CSRF, CORS/CSP, rate limits | Auth/protected endpoints/CSRF tests pass; TLS ingress unrun; no individual isolation claimed |
| 9 Model/data | Fixed-destination OpenAI adapter; mock path; filtering/redaction/payload bounds | HTTP transport failure/parsing tests pass; live model unverified; prose fallibility flagged |
| 10 Reports/verification | Versioned Report model; JSON/escaped Markdown; fresh child evidence | Exports/timestamps/links pass; real correction verification unrun |
| 11 Persistence/lifecycle | SQLite WAL, retention, max record/byte admission, deletion, interrupted startup | Local restart/cleanup/capacity tests pass; local SQLite backup/restore tested; PVC backup/restore unrun |
| 12 Interface | Responsive structured views, labelled inputs, text statuses, native details/buttons | Browser flow + 390px capture pass; keyboard smoke checked by capture; full accessibility audit pending |
| 13 Packaging | Dockerfile, Helm/schema, source setup, diagnostics, dedicated kind scripts | Clean source setup, package build, Helm lint/template/security checks; no Docker/kind execution |
| 14 Portability | compatibility.md target versus tested matrix | Only macOS arm64 Python validated; cluster/containers/other hosts unverified |
| 15 Samples | failures.yaml + guarded setup/correction/cleanup scripts; examples/README | Shell syntax and manifest parse; actual image/event timing pending |
| 16 Observability | Fixed metric names; structured request/investigation IDs; optional external Collector example | Metrics endpoint authenticated; exporter/backend unrun; cost unavailable |
| 17 Tests | tests/test_application.py, test_provider_collector.py | Local suite passes; cluster integration and broad adversarial coverage pending |
| 18 Acceptance/evals | smoke.sh/smoke.py; opt-in evaluate.py with six cases/review metadata | Cluster smoke and paid evaluation not run; no benchmark claimed |
| 19 CI/releases | validate.yml + no-publish prepare-release.yml; scanner/licence hooks/SBOM/checksums | Workflows authored, not run on GitHub; action/base-image pins verified; signing/provenance gate remains |
| 20 Structure | Conventional src/tests/charts/examples/scripts/docs/evals and community root files | Local doc/asset/package checks |
| 21 README | Narrative, story, genuine visuals, quickstart, boundaries, evaluation evidence | Relative links/assets checked; GitHub hosted rendering unverified |
| 22 Visual identity | Supplied mark, original light/dark project marks/hero/social art; screenshots/GIF/video/diagrams/tech strip | Captures genuine and visibly mock; social preview not uploaded |
| 23 Asset provenance | docs/assets/README; editable SVG/mmd; capture/render scripts | Local image/XML checks; owner brand licence remains separate |
| 24 Guides | docs/index + installation/security/provider/config/API/operations/compatibility | Relative links checked; cluster commands need real execution |
| 25 Community | Apache licence, CONTRIBUTING/SECURITY/conduct/templates/changelog/roadmap | Owner must enable verified private reporting; no private channel asserted |
| 26 Research | Official references and design notes in architecture.md | No borrowed product imagery/identity/code |
| 27 Milestones | plan.md, validation.md, checkpoint.md | Final real-cluster acceptance still pending |
| 28 Boundaries | Local implementation and read-only remote attachment only | No production access, paid calls, pushes, tags, settings changes or publication |
| 29 Completion | Partial: local app checks pass, cluster/live acceptance not satisfied | Do not claim the complete release is accepted |
| 30 Handoff | README, validation/checkpoint, installation/provider/releasing guides | Final response states actual outcome and remaining environment gates |

## Specific limits requiring follow-up

Default collection is conservative. Live model-selected logs/ownership tools exist but diagnostic quality is not evaluated. Structured references are validated; arbitrary prose cannot be proven factual. Selector observations require complete readable pod/service snapshots; runtime correction claims need full fresh evidence. Storage admission limits reserve bounded report growth but are not hard disk quotas. Optional OpenTelemetry is supplied as an operator-installed Collector path, not a built-in SDK exporter. Action/base-image pins are implemented. Release signing/provenance remain owner-gated preparation work. These limitations must survive future README edits.

The [follow-on audit table](../audit-results.md) supersedes earlier validation counts and details the expanded smoke coverage and current blockers.
