# Development checkpoint

The first-release acceptance milestone is merged through PR #5. [Post-merge validation at c95c50a](acceptance/2026-11-02-main-validation-c95c50a.json) passed all 13 jobs: native images, Kubernetes matrix, browser/evidence/load, recovery and source/security checks.

The separately authorised [native candidate workflow](acceptance/2026-11-02-hosted-release-candidates.json) passed both amd64/arm64 jobs at the same revision, each with 92 source tests. Both downloads passed independent ZIP digest, signature/checksum/provenance, source-equivalence and metadata privacy verification. Test signatures do not establish an approved publisher identity. Archives and private build data remain excluded from Git; only sanitised evidence is retained.

Live provider calls and package/release publication remain unexecuted. Current visibility and reporting status are recorded in the authoritative readiness guide. Maintenance assignment, private reporting and a trusted release identity remain gates in [current readiness](release-readiness.md). Future changes require their own relevant validation; earlier passes are revision-specific.

The next release-control milestone records the passing post-PR #6 run at 0a19271, documents component maintenance/triage roles (still unassigned), and prepares fail-closed offline publisher approval with an empty production trust policy. Live evaluation still lacks paid-call authorisation and verified private setup. No actual publisher key or repository setting has been configured. See [the control record](acceptance/2026-11-02-release-controls.json).

The November 3 release setup records VERIQTA LIMITED as maintaining organisation and the successful post-PR #7 validation. Current owner decisions and setup actions supersede older pending-status statements; see [release readiness](release-readiness.md).
