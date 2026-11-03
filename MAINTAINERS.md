# Maintenance responsibilities

**Maintaining organisation: VERIQTA LIMITED.** Organisational stewardship does not appoint an operational responder or signing-key custodian.

Repository administrators control maintainer appointment, release approval and private security-report handling. No response-time or commercial support commitment is provided. A named responsible reviewer for the project-maintained SQLite package and source-interpreter recipe has not yet been recorded; that assignment and recipe review are required before a public release.

The runtime maintainer is responsible for:

- Reviewing SQLite, CPython, OpenSSL, Alpine and Python dependency security advisories before every release and deployment refresh.
- Running the SQLite release/checksum check in CI and during updates; treating network failures or stale pins as failures.
- Verifying upstream source/checksums, actual Python runtime linkage and regression checks; retaining apk inventory and licence notices.
- Rebuilding and scanning final runtime images on each claimed architecture, with exact identities and scanner/database dates.
- Repeating affected application, real-cluster incident and storage tests; documenting unfixed findings without suppression or automatic risk acceptance.
- Maintaining the supported profile and migration/backup contract, and retiring the custom SQLite package when a reviewed supported vendor package supplies the fix.

The release reviewer must verify checksums/signatures against an independently trusted signing identity, review source/build provenance and scans, confirm a working private reporting route, and check that distribution claims match actual published artifacts. Local candidate keys and self-generated provenance do not establish an independently trusted publisher or a SLSA level.

The [SQLite maintenance procedure](packaging/sqlite/README.md) records provenance, checksums, linkage and the update gate. The [release guide](docs/releasing.md) records candidate preparation. Issues containing only non-sensitive maintenance questions may use the repository issue tracker; vulnerability details require the verified private route in [SECURITY.md](SECURITY.md).

The [maintenance runbook](docs/maintenance.md) defines the review cadence, component-specific pin/update procedures, evidence and vulnerability response. The [publisher approval procedure](docs/trusted-signing.md) is separate from ephemeral candidate signing; the committed trust policy has no approved identities. Neither document appoints a person or claims active continuous monitoring.
