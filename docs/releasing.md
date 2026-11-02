# Release preparation

There is no published image, Helm repository or tagged release. Source installation is the working path. Validation CI has contents:read and no publishing step. Pull requests do not receive provider keys, deploy credentials or privileged release contexts. No workflow uses pull_request_target or runs paid evaluations.

`Prepare release artifacts` is manual and generates an unsigned local container archive, wheel/sdist, chart, release notes, SPDX SBOM and SHA256SUMS as a workflow artifact. It does not push, tag or publish. This workflow has not executed in GitHub. Scanner and licence failures must be reviewed and fixed, not bypassed. The Python base-image index digest and all third-party action references are pinned. Resolution records are in `.github/base-image.json` and `.github/action-pins.json`; this verifies reference existence, not action safety or container execution. Re-review pins during updates. The final runtime uses pinned official Python/Alpine with a project-built signed SQLite 3.54.1 package; review its documented maintenance obligation and exact final-image scan before release. Runtime checks independently enforce the loaded SQLite version and regression even when a vendor advisory feed lacks coverage. The Trivy reference was corrected to an existing upstream release, and checksums include the Helm .tgz package.

Local package preparation after checks:

```sh
.venv/bin/python -m build --no-isolation
helm package charts/kubeinvestigator -d dist
(cd dist && shasum -a 256 *)
```

Before owner-authorised publication: review CHANGELOG, version alignment (Python/chart/UI), current Kubernetes/model support, vulnerability/secret/licence checks, fresh-cluster acceptance, both actual container architectures, upgrade/restore exercises, private reporting and capture provenance. Generate a release SBOM and retain required upstream notices. For future publishing use a separate protected workflow, immutable image digests, OIDC attestations and keyless cosign signatures where supported. Provenance/signing are **prepared as a documented owner gate**, not implemented or claimed verified. Do not present an unsigned build as signed. No release tag or external package should be created without explicit owner instruction.

## Hosted gate evidence

Validate run 41473405003 at d261de7 passed all ten jobs; native per-architecture Docker archives fix the earlier OCI input failure without weakening the vulnerability gate. Sanitised image summaries record exact config/archive lineage and scanner/database metadata. PR secret scanning has read-only commit access and no review comments; its range is not full Git history. The separately retained history audit reports six source-verified public signing fingerprints with exit 1, not an automated clean-history pass. Review that policy alongside provenance before publication. The artifact-preparation workflow remains manual, unsigned and unpublished; no release job was dispatched by this milestone.

## Offline candidate signatures and provenance

`scripts/release_bundle.py` prepares versioned artifacts from a clean committed `git archive`, never from ignored working data. It builds the wheel/sdist, Helm package and one native-architecture final runtime archive, independently checks loaded SQLite/runtime hardening, scans that exact archive and emits an SPDX SBOM. HIGH/CRITICAL or secret findings block signing. It records image/archive lineage, scanner/database metadata, release notes and locked requirements.

The helper generates an in-toto/SLSA-format **local build statement**, checksums all artifact subjects and that statement, then signs SHA256SUMS using OpenSSL and an explicitly supplied local key. It makes no OIDC, transparency-log, registry or publication request. No SLSA level, independent builder identity or bit-for-bit reproduction is claimed. The build type `local-candidate/v1` means: committed Git archive, system Python/Helm/Docker/Trivy tools, native runtime build and the checks described above. CI's manual unsigned artifact workflow remains a separate unexecuted path.

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
