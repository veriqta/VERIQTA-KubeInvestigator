# Release preparation

There is no published image, Helm repository or tagged release. Source installation is the working path. Validation CI has contents:read and no publishing step. Pull requests do not receive provider keys, deploy credentials or privileged release contexts. No workflow uses pull_request_target or runs paid evaluations.

`Prepare release artifacts` is manual and prepares native amd64/arm64 wheel/sdist, chart, final container archive, SPDX SBOM, release notes, checksums and local build statements. Ephemeral test keys sign the candidate checksums and are never uploaded; these signatures test integrity, not an independently trusted release identity. The workflow has read-only repository permissions and no registry, release, package or deployment step. Its execution status must be recorded separately from validation.

Use the local preparation procedure below while publication is unavailable. Before publication, review version alignment, upstream notices, exact-architecture scans, source/runtime checks, acceptance, security reporting and the intended signing trust root. Immutable action/base-image references and the project's signed SQLite package are documented in their resolution/maintenance files. A package-local build signature is not publisher provenance; a release needs a separately approved signing identity and verified subjects.

## Hosted gate evidence

Validate run 41473405003 at d261de7 passed all ten jobs; native per-architecture Docker archives fix the earlier OCI input failure without weakening the vulnerability gate. Sanitised image summaries record exact config/archive lineage and scanner/database metadata. PR secret scanning has read-only commit access and no review comments; its range is not full Git history. The separately retained history audit reports six source-verified public signing fingerprints with exit 1, not an automated clean-history pass. Review that policy alongside provenance before publication. The native artifact-preparation workflow is manual, uses ephemeral test signatures and does not publish. Its actual execution is recorded separately.

## Offline candidate signatures and provenance

`scripts/release_bundle.py` prepares versioned artifacts from a clean committed `git archive`, never from ignored working data. It builds the wheel/sdist, Helm package and one native-architecture final runtime archive, independently checks loaded SQLite/runtime hardening, scans that exact archive and emits an SPDX SBOM. HIGH/CRITICAL or secret findings block signing. It records image/archive lineage, scanner/database metadata, release notes and locked requirements.

The helper generates an in-toto/SLSA-format **local build statement**, checksums all artifact subjects and that statement, then signs SHA256SUMS using OpenSSL and an explicitly supplied local key. It makes no OIDC, transparency-log, registry or publication request. No SLSA level, independent builder identity or bit-for-bit reproduction is claimed. The build type `local-candidate/v1` means: committed Git archive, system Python/Helm/Docker/Trivy tools, native runtime build and the checks described above. The manual native CI workflow uses the same helper and an ephemeral test key; its actual execution is tracked separately.

For a local verification candidate, create a new ephemeral key outside version control. This key is a test identity, not an approved publisher identity:

```sh
umask 077
mkdir -p .data
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
  -out .data/candidate-signing.pem
DOCKER_CONTEXT=YOUR_LOCAL_DOCKER_CONTEXT .venv-source/bin/python \
  scripts/release_bundle.py --prepare --signing-key .data/candidate-signing.pem
```

Replace `YOUR_LOCAL_DOCKER_CONTEXT` with a context using a local Unix socket. Docker, Helm, OpenSSL and Trivy 0.76.1 must be installed; initial source/image/scanner downloads require network access. The source environment must include locked development dependencies. A dirty checkout or occupied candidate directory is rejected. Artifacts go under `dist/0.1.0-REVISION/`; this ignored directory and the private key are not committed. Build caches contain the ephemeral SQLite package-signing key and must not be published.

Verify with a public key whose fingerprint has been established independently:

```sh
.venv-source/bin/python scripts/release_bundle.py \
  --verify dist/0.1.0-REVISION --trusted-public-key TRUSTED_PUBLIC_KEY.pem
```

Replace `REVISION` with the 12-character revision printed by preparation. A bundled public key alone is not a trust anchor. Verification checks the RSA/SHA-256 signature, every file checksum, complete file inventory and provenance subject equality; tests reject modified artifacts, checksum tampering and unsigned additions. Before a real release, use an approved independently trusted signing identity and retain its fingerprint through a separate trusted channel. Publication, keyless remote signing and public visibility still require separate approval; no package URL exists merely because this local bundle verifies.

## Recorded local candidate

The [portable 0.1.0 candidate record](acceptance/2026-11-02-portable-release-candidate.json) identifies revision 7d21ec7 and every artifact hash. Native arm64 preparation, installed-wheel import, final-archive scan, runtime checks, SBOM portability and offline signature/subject verification passed. [Final image evidence](security/findings/2026-11-02-portable-candidate-arm64.json) records Trivy 0.76.1, database timestamps, OCI/configuration identity and complete inventories; [the SPDX SBOM](security/findings/2026-11-02-portable-candidate-sbom.spdx.json) has no private host paths. No findings were detected by the recorded scan. The first local candidate was withheld after privacy review found host paths in its SBOM; the replacement was regenerated and signed, not edited after signing.

The archives, wheels, test key and build caches remain outside Git. Public records do not make any package available for public installation. The candidate is still signed only by a test identity; publication, independently trusted signing and repository visibility remain separate gates.
