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
