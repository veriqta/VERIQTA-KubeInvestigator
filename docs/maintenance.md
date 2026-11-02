# Maintenance and vulnerability response

No named runtime maintainer, security triage owner or release reviewer has been assigned in this repository. Repository administrators must record responsible people and an independently reviewed approval process before a public release. The roles below define responsibilities; they do not appoint anyone or promise a support SLA.

| Role | Responsibilities | Current assignment |
| --- | --- | --- |
| Runtime maintainer | SQLite fork, CPython/linkage, Alpine base, OpenSSL/Expat, dependency/action pins, update PRs and exact-image evidence | Unassigned |
| Security triage owner | Monitor advisories and private reports, assess deployed exposure, coordinate fixes and communications without public exploit details | Unassigned |
| Release reviewer | Review test/scan/provenance evidence, licensing, publisher identity and distribution approval; confirm private reporting works | Unassigned |
| Repository administrator | Appoint roles, approve trust-policy changes and repository settings, establish independent signing-key custody and reporting route | Administrator-controlled; no delegation recorded |

## Monitoring contract

Before release or deployment refresh, and at least weekly once a maintainer accepts responsibility, review official SQLite CVEs/releases, CPython security releases, Alpine security/package notices, OpenSSL/Expat advisories, Python dependency advisories and GitHub Actions security/runtime notices. Weekly review is a required operating procedure proposed here; no standing monitoring service or scheduled alert is currently configured, and no completed review cadence is claimed.

Existing Validate CI runs the official SQLite release/checksum comparison and dependency/container/secret gates on configured pushes/PRs. It does not continuously monitor an installed deployment. Failed downloads or changed upstream release/checksum data fail the SQLite check rather than silently approving a stale pin. Pattern scanners and vendor databases have coverage gaps: the earlier Alpine SQLite issue required independent linkage/advisory checks despite a scan with no findings detected.

Use [SQLite's CVE table](https://sqlite.org/cves.html), [CPython security guidance](https://devguide.python.org/security/psrt/index.html), [Alpine's security database](https://security.alpinelinux.org/), upstream release notes and the documented package feeds. Keep a dated record of sources checked, affected versions/platforms, exploit prerequisites, application exposure, fixed versions, decisions and verification revision. Assign a follow-up date for unresolved issues; do not auto-accept risk, suppress findings or disable scans.

## Component update procedures

| Component | Versioned sources | Required update and validation |
| --- | --- | --- |
| SQLite | packaging/sqlite/source.json, APKBUILD, src/kubeinvestigator/sqlite_runtime.py, runtime checks | Independently verify official archive SHA3-256 and pinned hashes; review CVE/fix, update recipe/floor together, retain licence and signed apk inventory. Verify actual loaded library/version/hash and FTS5 regression on both native platforms. Repeat affected storage/incident/recovery checks and exact final-image scans. Prefer an official stable vendor package once independently verified equivalent |
| CPython/source interpreter | scripts/bootstrap-source-python.sh, scripts/setup-ci-python.sh, Dockerfile base, installation guide | Review supported security release and source checksum. Build into a new private prefix rather than replacing system Python. Verify SQLite, bundled Expat, OpenSSL and CA linkage; recreate venv from locks and test documented clean installation. Container fixes do not patch a host interpreter |
| Python/Alpine base and OS libraries | Dockerfile immutable index, .github/base-image.json | Review upstream supported branch, index and both architecture manifests. Update Dockerfile and resolution record together. Keep stable repositories, non-root/read-only hardening and package inventory. Build/execute both native architectures, verify final runtime and SQLite floor, rescan the exact archived images and repeat affected cluster/browser checks |
| Python dependencies | pyproject.toml, requirements.lock, requirements-dev.lock | Resolve on the supported interpreter, regenerate both locks using the documented pip-compile workflow, inspect dependency/licence changes, run source/provider/security tests and advisory checks. Rebuild final images; preserve older scan evidence and add new identities/timestamps |
| Authoring tools and CI actions | scripts/asset-tools locks, .github/action-pins.json, workflows | Update optional tooling separately from runtime. Verify immutable upstream action refs, least-privilege permissions and runner compatibility. Never expose provider/release secrets to PR validation. Review current Node runtime deprecation notices during pin refresh |

The [SQLite recipe](../packaging/sqlite/README.md) records provenance, checksum verification, runtime linkage and the temporary signing-key boundary. Build caches contain the ephemeral apk signing private key and must not be published. This key is unrelated to publisher approval. The [trusted signing procedure](trusted-signing.md) covers release trust separately.

## Vulnerability handling and change review

1. Receive sensitive reports only through the verified private route in [SECURITY.md](../SECURITY.md). Until that route exists, publish no exploit details or invented contact address.
2. Reproduce in a disposable environment; compare reported package versions with the actual loaded runtime and supported profiles. Record source-installation and container exposure separately.
3. Prepare a bounded fix/update PR, upstream fix reference and updated pins/checksums. Leave unfixed relevant high-impact findings as release blockers unless an explicit, reviewed exception is separately authorised; do not silently accept low apparent exposure.
4. Run only relevant local checks, plus mandatory CI. Runtime/library changes require new exact-image scans and affected real-cluster acceptance; storage changes also require recovery checks. Docs-only changes do not require manual repetition of unchanged application checks.
5. Review the resulting artefacts, SPDX inventory, scanner version/database timestamp, source revision and known limitations. A scan with no findings detected is not a claim of no vulnerabilities.
6. Release publication, visibility and production rollout each require separate approval. Document affected versions, upgrade steps and the backup/schema contract; do not advertise cross-release downgrade or disaster guarantees outside the tested profile.

Signing-key rotation/revocation, security reporting and maintainer succession must be reviewed before changing responsibilities. Record the accepted scope and review references without placing private contact details, credentials or conversation history in distributed documents. Until people and channels are appointed, these operational responsibilities remain release blockers rather than fictional completed work.
