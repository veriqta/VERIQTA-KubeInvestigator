# Current checkpoint — hosted validation reliability

Implementation, branding and CI fixes have been merged through PRs #1–#3. Development continues on codex/kubeinvestigator-development. No release or package has been published.

Corrected validation at d261de7 passed all ten jobs in [run 41473405003](https://github.com/veriqta/VERIQTA-KubeInvestigator/actions/runs/41473405003): native Ubuntu amd64 source (80 tests), chart, runtime, both native image architectures, PR secret range, three Kubernetes versions and PVC recovery. The old unreadable OCI archive was replaced by one Docker archive per native architecture; HIGH/CRITICAL gates remain. The PR secret job has read-only commit access with comments disabled. Duplicate development push/PR runs were removed. Durable [hosted evidence](acceptance/2026-11-02-hosted-validation.json) preserves actual job and image identities.

Independent full-history Gitleaks 8.30.1 audit returned six public Python signing-fingerprint matches in historical image metadata, exit 1. Every match is preserved and source-verified in [the review](security/findings/2026-11-02-history-secret-review.json); no suppression or history rewrite was added. Do not describe the one-commit hosted range check as a complete history pass.

The prior source SQLite remediation, local arm64 acceptance, QEMU-amd64 checks and dated evidence remain intact. [Compatibility](compatibility.md) now distinguishes native hosted execution from emulation and untested physical-host/WSL2/cloud profiles. Current PR checks govern later documentation revisions; green code evidence does not fabricate a pass for a newer revision.

Remaining: independent history-scan/public-fingerprint policy review, maintenance ownership, private reporting, release signing/provenance, staging TLS/CNI/physical recovery/load, and separately authorised live-model evaluation. No paid model calls, release publication, external application deployment or production access formed part of this validation.
