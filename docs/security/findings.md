# Container security findings — 2026-11-02

**The previous container remediation is preserved, and source SQLite/startup checks are now verified separately.** The recorded final-image scans have **no findings detected by the recorded scan**; this is not proof that the product has no vulnerabilities. The unchanged HIGH/CRITICAL gate exits 0. No advisory, package, severity or unfixed finding was suppressed. This is specific automated and component-level evidence, not an independent security audit or a production-readiness certification.

The [final execution/identity record](findings/2026-11-02-final-runtime.json), [complete final scan with package inventory](findings/2026-11-02-final-runtime-scan.json) and [final SPDX SBOM](findings/2026-11-02-final-runtime-sbom.spdx.json) supersede the earlier Debian scan for the current Dockerfile. Historical [185 OS findings](findings/2026-11-02-image.json) and [45 HIGH package/layer records](findings/2026-11-02-debian-high-origins.json) remain available; those images are not approved alternatives.

## Current hosted validation and history audit

[Run 41473405003](https://github.com/veriqta/VERIQTA-KubeInvestigator/actions/runs/41473405003) passed all ten jobs at revision d261de7. [Hosted evidence](../acceptance/2026-11-02-hosted-validation.json) supersedes prior unexecuted-host claims: native amd64 Ubuntu source setup passed 80 tests; native amd64 kind 1.35.8/1.36.4/1.37.0 and PVC recovery passed; native amd64/arm64 runtime/image jobs passed. Exact [amd64](findings/2026-11-02-hosted-native-amd64-image.json) and [arm64](findings/2026-11-02-hosted-native-arm64-image.json) records bind the scanned Docker archive, config/filesystem lineage, actual runner, Trivy/database timestamps and runtime checks. Both have **no findings detected by the recorded scan**, not proof of no vulnerabilities.

The previously failing image job never reached vulnerability analysis: Trivy could not initialise the multi-architecture OCI archive. The corrected job scans a one-architecture Docker archive on each matching native runner, pins Trivy 0.76.1, records complete severity counts and enforces the unchanged HIGH/CRITICAL plus secret policy. Sanitised artifacts exclude secret values and image environment contents; malformed/empty or mismatched image evidence is rejected by tested code. A collection step's exit 0 is not presented as the later gate result; hosted job conclusion supplies that evidence.

The old PR secret action failed listing commits (403). Job-scoped PR read permission and disabled comments fix that failure without write access. Its successful hosted run scanned one PR commit only. The earlier main-merge action scanned zero commits; it is not full-history evidence.

A separate full-history Gitleaks 8.30.1 check scanned five nonempty commits and returned **exit 1, six matches**. Each was checked in its original blob against the [pinned official Python source](https://raw.githubusercontent.com/docker-library/python/3d7e95597e56a415d9e4abc0f15877e005d2cb2e/3.12/alpine3.24/Dockerfile): all are the public release-signing fingerprint in image environment/build-history metadata, not a private key or API credential. [The review](findings/2026-11-02-history-secret-review.json) retains every location and the nonzero result. No ignore, suppression, history rewrite or blanket clean-history claim was added. Independent review/public-data policy remains separate from the PR-range gate; genuine credentials must never be dismissed on this basis.

## Earlier source/compatibility follow-up (retained)

[Current evidence](findings/2026-11-02-source-compatibility.json) preserves the prior records and adds exact updated arm64/amd64 image digests, archive/config linkage, scanner/DB metadata, source linkage and real execution results. These startup-guard images supersede the older deployment image for current code; the remediation-baseline identities below remain historical evidence.

The documented macOS source installation now uses an official maintained CPython 3.12.16 source build in a private workspace prefix, linked to maintained Homebrew SQLite **3.54.1** and OpenSSL, with bundled Expat **2.9.0**. The official CPython archive SHA-256 is verified. No loader overrides or system-library replacements are used. The Homebrew Python bottle attempt failed on this macOS 26.2 Expat ABI; that failed bootstrap is not a pass. The alternate upstream build, fresh locked virtual environment, 74 tests and actual localhost authenticated investigation/export/deletion all passed.

The old bundled interpreter still loads SQLite 3.53.1: container remediation did not patch it. It is now **rejected** by setup, preflight, application Store initialization and maintenance before database access. The real old-interpreter preflight returned 1; make setup returned 2 without creating the requested virtual environment. There is no bypass setting. The minimum 3.54.1 version check is conservative and does not establish safety against future CVEs.

New native arm64 incident smoke runs passed on Kubernetes **1.36.4 and 1.37.0**, including restricted reads/denials, three incidents/exports, restart persistence, corrections/fresh verification and cleanup. The earlier successful 1.35.8 incident/PVC recovery results were retained without redundant repetition. Linux amd64 was built and executed **under QEMU**, with 61 installed-image application/security/storage tests and runtime checks; native amd64 hardware and Kubernetes remain untested. Generic Linux source setup was exercised in a separate native arm64 development container: 73 tests passed, one Helm-only test skipped, static/docs checks passed after omitted verification fixtures were supplied. This does not certify bare-host Linux/WSL2 installation or the unexecuted hosted workflow.

The current native arm64 and emulated amd64 final deployment images each have **no findings detected by the recorded scan** (0 returned vulnerability records, 0 secret records; unchanged HIGH/CRITICAL gate exit 0). Complete [arm64 scan](findings/2026-11-02-source-guard-arm64-scan.json) and [amd64 scan](findings/2026-11-02-source-guard-amd64-scan.json) include their inventories. The development-only test image is separate and is not represented by these scans. This result has the coverage limits already demonstrated by the SQLite advisory gap.

[Maintenance process](../../packaging/sqlite/README.md#detection-ownership-and-update-gate) now specifies official release/checksum monitoring, manual advisory review, ownership, pin/floor consistency, actual runtime linkage, signed package transport, rebuild/rescan/regression/acceptance gates and eventual vendor-package replacement. `scripts/check_sqlite_update.py` reports the current official release/checksum match; malformed feeds, changes or network errors fail. Prepared validation runs it and selects a patched interpreter; hosted execution remains unverified. No continuous alert service is claimed. CPython bootstrap updates and Homebrew dependencies must also be maintained.

## Why nine CVEs produced 45 findings

Trivy matched binary packages to their source package advisories. These were package/advisory pairs, not 45 independent bugs or demonstrated exploit paths:

- Four util-linux CVEs × nine binary packages = **36**.
- One ncurses CVE × four packages = **4**.
- One systemd CVE × two packages = **2**.
- One each for acl, sqlite3 and perl = **3**.
- Total: **36 + 4 + 2 + 3 = 45 HIGH** findings (nine distinct CVEs).

In the table, **U** is bsdutils `1:2.41.5-0+deb13u1`; libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, mount and util-linux `2.41.5-0+deb13u1`; login `1:4.16.0-2+really2.41.5-0+deb13u1`.

**D0** is the inherited Debian rootfs layer: diff ID `sha256:685889762157cefb6370119253b3c709f70bb2622402052065c92243e3d9105f`, compressed digest `sha256:2b70e040f7d132c8d366ee0223462552686510fb372ea5a83822973c30f19e36`. **P2** is the official Python base's compile/runtime-library layer: diff ID `sha256:e3af5abbdc37fa9b5b795480004e631040ad0b537c2174d07352e25c43d1d0ed`, compressed digest `sha256:b41621e272b0b306c196fabab6f5e0132d1c13f3c929bfb63455191fa509e311`. Neither is an application-install layer. These libraries remained in the prior final runtime; this was not merely a build-stage scan.

## Per-CVE disposition

Fixed versions below distinguish upstream/other Debian branches from a supported trixie update. No fixed trixie version was listed for any of these nine during review; sid/forky packages were not mixed into the old base.

| CVE / previous matches | Previous installed packages / source layer | Available fixed version and upstream status | Application relevance and final disposition |
| --- | --- | --- | --- |
| [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642), 9 | U / D0 | Debian unstable util-linux 2.42.3-1; trixie no-dsa | Privileged mount-hook path; app does not run it. Debian util-linux binaries/libraries removed with base replacement. Alpine libuuid 2.42.3-r1 is at the corrected source series. No remaining blocker from this CVE. |
| [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408), 9 | U / D0 | Debian unstable util-linux 2.42.4-1; trixie no-dsa | Privileged util-linux nsenter --join-cgroup descriptor inheritance. That implementation is absent. Alpine retains libuuid 2.42.3-r1, containing only UUID shared libraries; mount/nsenter commands belong to BusyBox, a different implementation. No version-based claim that libuuid is 2.42.4 is made. Affected command code is absent; no risk exception/suppression is used. |
| [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409), 9 | U / D0 | Debian unstable util-linux 2.42.3-1; trixie no-dsa | Privileged X-mount.subdir path traversal; app has no mount workflow. Affected util-linux mount implementation removed; retained Alpine libuuid is 2.42.3-r1. No remaining blocker from this CVE. |
| [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410), 9 | U / D0 | Debian unstable util-linux 2.42.3-1; trixie no-dsa | Restricted bind-mount/SUID path race. Affected implementation removed; BusyBox mount is separately inventoried. Non-root/no-escalation/no host mounts retained. No remaining blocker from this CVE. |
| [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369), 1 | libacl1 2.3.2-2+b1 / D0 | acl 2.4.0; Debian unstable 2.4.0-1; stable point update pending, new ABI not individually backported | No privileged ACL endpoint exists. libacl is absent from the final package inventory. No remaining blocker from this CVE. |
| [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720), 4 | ncurses-base, ncurses-bin, libtinfo6 6.5+20250216-2 / D0; libncursesw6 same version / P2 | Upstream 6.5-20251213; Debian unstable 6.6+20251231-1; trixie no-dsa | infocmp parser overflow, not an app workflow. Final libncursesw/libpanelw/ncurses-terminfo-base are 6.6_p20260516-r0, beyond the fix; infocmp is absent. No remaining blocker from this CVE. |
| [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373), 1 | libsqlite3-0 3.46.1-7+deb13u2 / D0 | Upstream fixed in 3.54.0; Debian tracker still unfixed; reviewed Alpine stable base/repository supplied only 3.53.4-r0 | App actively uses SQLite. Replaced with project-built, signed sqlite-libs **3.54.1-r0** from verified official source. Python loads 3.54.1; FTS5 remains enabled and negative-rowid prefix regression passes in three modes. No remaining blocker for this CVE; ongoing custom-package maintenance/review is a release obligation. |
| [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742), 2 | libsystemd0 and libudev1 257.13-1~deb13u1 / D0 | Upstream 258.10 / 261.2; Debian unstable 261.2-1; trixie no-dsa | systemd-homed group privilege path; app never starts homed. systemd/udev libraries and homed are absent from the final runtime. No remaining blocker from this CVE. |
| [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538), 1 | perl-base 5.40.1-6+deb13u1 / D0 | Archive::Tar 3.10; Debian unstable Perl 5.42.3-1; trixie postponed pending upstream regression handling | Perl tar-parser allocation exhaustion; app accepts no tar uploads and executes no Perl. Perl/Archive::Tar removed from runtime with base replacement. No remaining blocker from this CVE. |

The original source-package mapping was conservative: a library package match did not prove that it contained a vulnerable CLI. Component absence in the new image is supported by installed package/file ownership, not by an ignore rule. [Runtime package ownership evidence](findings/2026-11-02-runtime-packages.txt) records the patched SQLite paths, UUID-only libuuid contents, BusyBox command ownership and absence of infocmp/Perl. Previously deferred/unfixed stable advisories remain blockers for the old Debian image; its reduced exposure was never an accepted risk exception.

## Runtime remediation and scanner coverage gap

[Dockerfile](../../Dockerfile) now uses the pinned official `python:3.12-alpine3.24` base in isolated build/runtime stages, applying supported stable apk updates. [Alpine 3.24 is maintained](https://www.alpinelinux.org/releases/) through June 2028 for main packages. No edge/testing repositories are added. Only installed app dependencies and the SQLite shared-library package enter the runtime; Debian admin tools, ACL/systemd/Perl components, runtime pip/setuptools/wheel, compiler, SQLite headers/CLI and source do not. UID 10001, dropped capabilities, no privilege escalation and chart read-only root remain in place. The runtime retains apk's inventory and CA certificates.

The first Alpine candidate scanned clean **while still loading vulnerable SQLite 3.53.4**. That advisory-coverage gap was caught by comparing the loaded version with [upstream's fix](https://github.com/sqlite/sqlite/commit/e1c9934f9f11a499029abb020ea715a08970da80), not accepted as a clean security result. The final build uses [official SQLite 3.54.1](https://sqlite.org/releaselog/3_54_1.html), verified against its [published archive SHA3-256](https://sqlite.org/download.html), with SHA-512 pinned in [APKBUILD](../../packaging/sqlite/APKBUILD). The package is locally signed; normal apk signature verification installs it and records its real version. The private signing key stays in the build stage. This is a project-maintained package, not an official Alpine update or a release provenance signature. See [maintenance and attribution](../../packaging/sqlite/README.md).

No known unresolved advisory from the reviewed nine remains in this runtime, and none was automatically risk-accepted. The custom package must be monitored, reviewed and eventually replaced by a suitable supported vendor package. Keep trusted-backup-only restoration, bounded parameterised SQL, non-root/namespace isolation and report redaction: remediation does not make arbitrary databases or Kubernetes evidence safe.

## Container-remediation baseline identity (retained)

| Field | Actual value |
| --- | --- |
| Final local OCI index digest | `sha256:2226235df3082152ac81ef3872ee76cbb38415b00ee68ed48a7f2336bc5984e9` |
| Linux arm64 runtime manifest | `sha256:e5f7ce4935fb467935af4081e7447f386c56d3c392414570aad312664db9dd74` |
| Image configuration digest / Trivy ImageID | `sha256:385372b29bb7c7e2ed6c95890fb04427c4224b23302fc3db810adad0f078c717` |
| Saved runtime archive SHA-256 | `26300d1cefc8f7bcddafdd53ff8e1aba96c686a3c42795a50b507c72e9661d28` |
| Scanner | Trivy 0.76.1 |
| Vulnerability DB version / updated | 2 / 2026-11-02 07:17:05.526948404 UTC |
| DB downloaded / next update | 2026-11-02 10:00:51.900530 UTC / 2026-11-03 07:17:05.526947983 UTC |
| Final OS/Python inventory | Alpine 3.24.3: 38 OS packages; 39 Python packages |
| Findings, all severities | **0 vulnerabilities, 0 secrets**; HIGH/CRITICAL gate exit **0** |
| Active runtime | Python 3.12.16; SQLite 3.54.1; UID 10001 |

The archive index references the runtime manifest, which references the same configuration digest reported by Trivy; all filesystem diff IDs match Docker inspection. This scan applies to the final runtime, not sqlite-build or the dependency-install stage. Build-stage dependencies were not represented as runtime findings or silently risk-accepted. No image has been published, so the digest is a local artifact identity, not a registry download promise.

Commands executed with the dedicated local Docker daemon (full raw logs/archive remain ignored under .capture):

```sh
export DOCKER_HOST="unix://$HOME/.colima/veriqta-acceptance/docker.sock"
export DOCKER_CONFIG="$PWD/.capture/docker"
export PATH="$PWD/.capture/tools/bin:/opt/homebrew/bin:$PATH"
docker build --progress=plain --iidfile .capture/runtime-build-id -t kubeinvestigator:0.1.0 .
make test check VENV=.venv-readiness
VENV=.venv-readiness bash scripts/smoke.sh
KI_ACCEPTANCE_SUITE=recovery VENV=.venv-readiness bash scripts/smoke.sh
docker image save --output .capture/final-runtime-image.tar sha256:2226235df3082152ac81ef3872ee76cbb38415b00ee68ed48a7f2336bc5984e9
trivy --cache-dir .capture/trivy-runtime-cache image --download-db-only
trivy --cache-dir .capture/trivy-runtime-cache image --skip-db-update \
  --input .capture/final-runtime-image.tar --scanners vuln,secret --list-all-pkgs \
  --format json --output .capture/final-runtime-scan.json
trivy --cache-dir .capture/trivy-runtime-cache image --skip-db-update \
  --input .capture/final-runtime-image.tar --scanners vuln,secret \
  --severity HIGH,CRITICAL --exit-code 1
trivy --cache-dir .capture/trivy-runtime-cache image --skip-db-update \
  --input .capture/final-runtime-image.tar --format spdx-json \
  --output .capture/final-runtime-sbom.spdx.json
docker run --rm -i --read-only --network none --cap-drop ALL \
  --security-opt no-new-privileges --tmpfs /tmp:rw,nosuid,nodev,size=32m \
  sha256:2226235df3082152ac81ef3872ee76cbb38415b00ee68ed48a7f2336bc5984e9 \
  python - < scripts/check_runtime.py
```

The DB was downloaded before scanning; skip-db-update locks these repeated scans to that recorded fresh snapshot, not to an unspecified stale cache. Reproduction on another date must update the DB first and record new dates/results. No ignore file, ignore-unfixed, severity reduction, external workflow or paid provider call was used.

## Verification and remaining release gates

- **68 host tests pass**, plus **57 relevant tests against the installed final runtime**, offline as UID 10001 with root and a separate test-fixture volume read-only. The first fixture harness lacked pytest's py.py compatibility module; after correcting that test-only staging, all 57 passed. No test tools were installed into the candidate image.
- [Full real-cluster incident acceptance](../acceptance/2026-11-02-alpine-sqlite-incident-mock.json) passed on Kubernetes 1.35.8/Linux arm64: Helm installation, actual scoped reads/denials, all three incidents/exports, restart persistence, corrections and fresh follow-ups, deletion and cleanup.
- [PVC recovery/rollback acceptance](../acceptance/2026-11-02-alpine-sqlite-recovery-mock.json) passed on the final OCI index: same-schema config upgrade/rollback, offline backup/restore, exact report equality, fresh child and cleanup.
- Incident/recovery exports contain the identical runtime manifest and configuration above. Their OCI indexes differ only in regenerated BuildKit attestation metadata; [identity evidence](findings/2026-11-02-final-runtime.json) records both. No cross-binary/schema downgrade or signed provenance is implied.
- Runtime checks independently verify the loaded SQLite and its regression, JSON/WAL, non-root/tool absence and TLS CA stores. Static/type/docs checks and actionlint pass. Prepared CI/release jobs now run the runtime check independently of scanner coverage; the Validate jobs have executed successfully in the recorded hosted run; the manual artifact-preparation job remains unexecuted.

Native hosted amd64 and the target Kubernetes matrix now have the newer evidence above. WSL2/other host/cloud profiles, actual ingress/TLS, physical storage failure, external security review and release signing/provenance remain unverified. Live-model diagnostic accuracy remains **unverified**: real Kubernetes evidence was tested with mock interpretations, and no paid model calls were made. The earlier bundled source-test interpreter loads SQLite 3.53.1 with FTS5 enabled and is now rejected. The separately installed source profile above loads verified 3.54.1 and passes its checks; no risk acceptance for old interpreters was granted. Container remediation clears the previous container gate for this exact native image; it does not accept the complete product/security brief or authorise publication.
