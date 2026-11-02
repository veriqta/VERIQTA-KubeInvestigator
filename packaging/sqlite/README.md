# Project-maintained SQLite runtime package

The official Python 3.12 / Alpine 3.24 base pinned in Dockerfile contains sqlite-libs 3.53.4-r0. Its stable repository did not offer the upstream fix for CVE-2026-119373 during this build. Trivy's Alpine data did not flag that vulnerable version; a zero scanner count was therefore insufficient.

This recipe builds **unmodified SQLite 3.54.1** from its official autoconf archive. [source.json](source.json) records the URL and hashes: the downloaded archive was verified against the SHA3-256 on the [official download page](https://sqlite.org/download.html), then its SHA-512 was pinned in APKBUILD. [Upstream fix](https://github.com/sqlite/sqlite/commit/e1c9934f9f11a499029abb020ea715a08970da80) and [3.54.1 release notes](https://sqlite.org/releaselog/3_54_1.html) establish the fixed source. SQLite is public domain (SPDX blessing); its source headers retain that notice.

The build flags and split-library convention follow [Alpine's SQLite recipe](https://raw.githubusercontent.com/alpinelinux/aports/3.24-stable/main/sqlite/APKBUILD), originally maintained by Alpine contributors. This is a project-built package, **not an official Alpine update**. The reserved .invalid address in its required maintainer field is build attribution, not a reporting channel. No Alpine maintainer is claimed to maintain this fork.

The isolated sqlite-build stage runs Alpine's abuild, makes an ephemeral signing key, and signs the package. The runtime trusts that build's public key and installs only sqlite-libs through normal apk signature verification; no allow-untrusted flag is used. The compiler, signing private key, headers, static archive, SQLite CLI and source remain outside the runtime. The installed apk database records version 3.54.1-r0 and its shared-library dependency/provides information. FTS5 remains enabled. Do not publish builder caches: they contain the ephemeral local signing key. This package signature verifies local build transport, not release provenance or upstream publisher identity.

The project now owns monitoring and updating this component until a reviewed supported-base update provides a suitable fixed library. Prefer returning to the official stable package when that is verified; do not silently drop this override. Each update must verify upstream archive checksums, retain the licence, rebuild, rescan the final runtime, run scripts/check_runtime.py, the application suite and disposable cluster incident/recovery acceptance. The script exercises the upstream negative-rowid FTS5 prefix regression in three detail modes, JSON functions, WAL startup/restart and TLS trust stores. It does not replace the full upstream SQLite test suite; that suite is not included in this autoconf archive and was not run.

Run from a source checkout:

```sh
docker build --target runtime -t kubeinvestigator:0.1.0 .
docker run --rm -i --read-only --network none --cap-drop ALL \
  --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  kubeinvestigator:0.1.0 python - < scripts/check_runtime.py
bash scripts/smoke.sh
KI_ACCEPTANCE_SUITE=recovery bash scripts/smoke.sh
```

Use only an authorised local Docker daemon; scripts/smoke.sh owns and cleans up its disposable kind cluster. These commands are separate from any live-model evaluation. Stable package repositories and ephemeral package-signing keys make byte-for-byte reproduction across dates unclaimed; exact tested images, package/library hashes and scanner database metadata are retained in the dated security evidence.

## Detection, ownership and update gate

Before every release, dependency update and deployment refresh, the assigned maintainer must:

1. Run `.venv-source/bin/python scripts/check_sqlite_update.py`. It compares the pinned version, official autoconf URL and published SHA3-256 with SQLite's official product feed. A new release, changed checksum, malformed feed or network error fails the check; it never silently adopts a download. The Validate workflow runs the same check; recorded hosted source validation passed at d261de7. No standing monitoring service or scheduled alert has been configured.
2. Review [SQLite's CVE table](https://sqlite.org/cves.html), upstream release/change notes and relevant vendor advisories (including Alpine/Debian trackers). Refresh Trivy's database and scan the exact final runtime, without ignores. A current release pin or a scan with no findings detected cannot establish absence of vulnerabilities; the earlier Alpine SQLite coverage gap demonstrates why the independent review is required.
3. If a relevant issue lacks a fix, retain it as a release blocker pending remediation or a separately authorised, documented decision. Do not automatically accept low exposure, turn off FTS5 or suppress package matches.
4. For a fix, obtain the official stable archive and independently verify the published SHA3-256, derive SHA-512/SHA-256, then update source.json and APKBUILD together. Retain licence/provenance and document the upstream fix. Review the conservative minimum in `src/kubeinvestigator/sqlite_runtime.py`; raise it for newly affected versions. There is no user-configurable bypass. Pin/recipe/floor consistency is tested.
5. Build for each claimed CPU platform. Verify the actual Python-loaded SQLite version, shared-library path/hash and FTS5 regression using scripts/check_runtime.py. Retain apk inventory: only the signed shared-library subpackage is installed. Scan the exact archived final image with recorded index/manifest/config digests, scanner version and DB date; do not substitute a builder scan.
6. Run relevant application/storage/security tests and incident acceptance after a runtime/library change; repeat PVC recovery when storage semantics or SQLite changes. Preserve old evidence and add new dated records. For unchanged library/runtime behaviour, use targeted checks and newly untested environments instead of repeating prior successful runs without a reason.

The maintenance owner has not been appointed or independently reviewed this recipe yet; that remains an owner release action. The ephemeral APK key is not a long-term release-signing identity, and no published provenance/signature is claimed. Prefer the vendor stable package once its fixed version, linkage, scanner coverage and regressions are verified; remove this override only through the same review/test process.

## Source interpreter boundary

The source installation uses a different linkage: the tested macOS CPython build links directly to maintained Homebrew SQLite 3.54.1. The bundled older interpreter was not patched and is now rejected before database access. The tested local CPython bootstrap pins the official 3.12.16 security source checksum, uses bundled Expat 2.9.0 and Homebrew OpenSSL, and installs into a private prefix using altinstall. Track CPython security releases and Homebrew SQLite/OpenSSL updates separately; review and update that bootstrap's version/hash and recreate its virtual environment when needed. Its full upstream CPython test suite was not run; application, stdlib/TLS, linkage and installation checks are recorded.
