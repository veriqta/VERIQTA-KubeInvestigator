# Development checkpoint

The first-release acceptance milestone is merged through PR #5. [Post-merge validation at c95c50a](acceptance/2026-11-02-main-validation-c95c50a.json) passed all 13 jobs: native images, Kubernetes matrix, browser/evidence/load, recovery and source/security checks.

The separately authorised [native candidate workflow](acceptance/2026-11-02-hosted-release-candidates.json) passed both amd64/arm64 jobs at the same revision, each with 92 source tests. Both downloads passed independent ZIP digest, signature/checksum/provenance, source-equivalence and metadata privacy verification. Test signatures do not establish an approved publisher identity. Archives and private build data remain excluded from Git; only sanitised evidence is retained.

Live provider calls, public visibility and package/release publication remain unexecuted. Maintenance assignment, private reporting and a trusted release identity remain gates in [current readiness](release-readiness.md). Future changes require their own relevant validation; earlier passes are revision-specific.
