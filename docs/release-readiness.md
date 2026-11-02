# First-release readiness

This is the authoritative current status. Historical checklists and dated scan/test records are retained in [the archive](archive/2026-11-02-release-readiness-before-first-release-acceptance.md). A pass applies to its recorded revision and environment, not every later change. The product remains an unreleased, single-replica, self-hosted read-only investigator for three conditions; no public package or image is advertised.

## Verified implementation and evidence

| Area | Actual evidence | Scope / limitation |
| --- | --- | --- |
| UI/API and complete browser journey | [Final browser acceptance](acceptance/2026-11-02-cluster-browser-final-mock.json): login, three submissions, real evidence, browser exports, restart/session invalidation, exact retained reports, three external corrections, newer follow-up evidence, logout and cleanup | Local arm64 kind 1.35.8, matching kubectl; MOCK interpretations. Genuine [screenshots and recording](browser-acceptance.md) |
| Diagnostic evidence | [Optional-evidence acceptance](acceptance/2026-11-02-optional-evidence-mock.json): current/previous retained logs, redaction, one observed ownership chain, actual events, healthy/ambiguous/missing/mismatched/unsupported cases, continued unrelated-read denial | Real Kubernetes evidence; no live-model diagnostic quality inferred. Missing historical logs remain explicit errors |
| Bounded operation | [Load results](acceptance/2026-11-02-bounded-load-mock.json): 56 submissions, 44 accepted/completed and 12 queue rejections, two observed running jobs, rate rejection/recovery, application CPU/memory/latency samples | Small real-cluster/mock workload, not sustained production. [Measured limits and starting resources](operating-limits.md) |
| Cluster/API enforcement and storage | [Hosted validation](acceptance/2026-11-02-hosted-validation.json): ten jobs passed at d261de7, native amd64 Kubernetes 1.35.8/1.36.4/1.37.0, restricted credentials, all three incidents, exports, restart, fresh follow-up and cleanup; real-PVC recovery | Actual native arm64 and hosted amd64 profiles. Same-schema backup/restore/config rollback, not cross-release downgrade |
| Source/security checks | Current component tests cover auth/CSRF/access, budgets/cancellation, failure handling, redaction, SQLite guard/recovery, source/runtime records and offline signature tamper detection | Latest exact test count and revision are recorded with each milestone; synthetic provider contract tests are not live evaluation |
| Runtime/dependencies | [Recorded native final-image scans](security/findings.md), patched SQLite 3.54.1 runtime/source setup and enforced startup floor | No findings detected by the recorded scan; not proof of no vulnerabilities. Later candidate scans must identify the exact final image |
| Candidate preparation | [Hosted native amd64/arm64 candidates](acceptance/2026-11-02-hosted-release-candidates.json) at c95c50a: both jobs passed 92 tests, source security gates, native runtime checks, exact-image scans and candidate signing; downloaded ZIP/signature/checksum/provenance/source checks independently passed | Ephemeral CI test identities; private expiring workflow artifacts, no package/release publication |
| Evaluation preparation | Eight-case no-call plan, private bounded harness, real-evidence structural replay, human-review labels | Live-model accuracy, account access, actual token use and costs remain unverified |

[Post-merge validation at c95c50a](acceptance/2026-11-02-main-validation-c95c50a.json) passed all 13 jobs, including native image, three-version Kubernetes, browser/evidence/load and PVC recovery gates. The separate [candidate workflow](acceptance/2026-11-02-hosted-release-candidates.json) also passed on both native architectures, each with 92 source tests. Earlier dated results remain preserved. These are tested-revision claims, not passes for later changes.

The conservative starting deployment allocation is 250m CPU/256Mi memory with 1 CPU/512Mi limits and concurrency two. Chart defaults were sufficient for the recorded small workload; this is not an SLA or an HA claim. Operator-supplied ingress/TLS, enforcing CNI and storage must be validated for the chosen deployment. Start with localhost/internal Service; broad internet exposure is not a tested profile.

## Current release-control review

The [PR #6 post-merge run](acceptance/2026-11-02-post-pr6-validation.json) passed all 13 jobs at 0a19271. The [release-control status](acceptance/2026-11-02-release-controls.json) records a fresh private-reporting API 404 (enablement remains unverified), unassigned maintenance roles, no approved production signer and no paid live-evaluation authorisation or verified private setup.

The [maintenance runbook](maintenance.md) now covers SQLite, CPython, base/OS, Python dependencies, action pins and advisory response without claiming active continuous monitoring. [Offline publisher approval](trusted-signing.md) is implemented separately from candidate signing. Its 11 fixture tests and current-candidate empty-policy rejection passed; the committed policy contains zero approved identities. This prepares verification but creates no trusted production signature. New tests and tool changes require their own final revision gates.

## First-release gates

1. **Live evaluation:** separately authorise the [proposed eight-case GPT-6 Luna plan](provider.md), configure provider credentials privately, run against reset disposable samples, review every case for incorrect diagnosis and unsupported claims, and retain exact model/revision/usage results. No paid calls have been made.
2. **Maintenance and private reporting:** record a responsible runtime reviewer and review the custom SQLite recipe. The repository remains private; private-reporting API status returned 404, so no working public private-reporting route is established. Follow the exact administrator setup in [SECURITY.md](../SECURITY.md) or provide a verified private contact. Do not disclose exploit details publicly.
3. **Distribution and signing identity:** source/candidate preparation does not make packages public. Before publication, approve an accountable signing identity and independently pin its public fingerprint/trust policy, use the prepared publisher-approval verifier, and review artifact subjects/checksums/provenance and current scans, approve publication destinations, and separately authorise public repository visibility. Local candidate signing does not establish an independently trusted publisher or SLSA level. See [release preparation](releasing.md).
4. **Final revision gates:** retain passing relevant CI for the merge revision, including the new real-cluster browser/evidence/load jobs. Earlier green runs do not establish a pass for changed code. No failed scanner or acceptance result may be hidden to merge.

The independent full-history Gitleaks run returned six source-verified upstream public Python signing-fingerprint matches, exit 1. The [review](security/findings/2026-11-02-history-secret-review.json) preserves exact locations and classification without ignores or history rewriting. This is not a discovered private credential, but an independent release reviewer must confirm that classification; it is not an automated clean-history pass.

## Supported first-release contract and future work

One cluster, explicit namespaces, one replica/worker and a trusted shared-team workspace are intentional. Individual report isolation/OIDC, multi-cluster control, autonomous remediation, distributed queues and high availability are outside this release. Code is Apache-2.0; brand rights are separate. No VERIQTA account/backend is required.

Cross-release schema downgrade, physical power/volume-loss certification, managed-cloud certification, WSL2, air-gapped operation, sustained production sizing and a full accessibility/independent security review remain unverified. They must not be advertised as supported, but are not an open-ended expansion of this first-release contract. A future incompatible schema requires its own tested migration/backup/binary pair. Existing backup/restore and same-schema rollback guidance remains applicable.

Current public-facing guides link here instead of repeating obsolete pending checklists. Historical evidence remains unchanged; captures distinguish fixture data, real Kubernetes observations and mock interpretations. No release, package publication, visibility change or production deployment is implied by development merges.
