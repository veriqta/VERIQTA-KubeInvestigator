# Publisher approval and release verification

The existing candidate workflow uses ephemeral RSA test keys. Its signatures prove integrity of the recorded candidate bytes, not an approved publisher, independent builder or SLSA level. No persistent publisher identity or private signing key has been configured. The committed [trust policy](../packaging/release/trust.json) deliberately has an empty approved-signers list: the publisher path fails closed until an identity is approved.

## Recommended first-release setup

Use the implemented offline publisher-approval path with a dedicated VERIQTA LIMITED release-publisher RSA key of at least 3072 bits. Keep the key on an isolated signing workstation under an explicitly appointed custodian; maintain a restricted offline recovery copy and a documented revocation/rotation procedure. This is a recommendation, not an assigned custodian or generated identity. Do not place a persistent key in GitHub Actions secrets for the current candidate workflow: that workflow intentionally retains only ephemeral test signing and `contents: read` permission.

Owner action: appoint the custodian and independent release reviewer, approve custody/backup/validity, then generate the key outside this repository using the approved procedure. Review the actual public SPKI fingerprint and add its active, time-bounded entry with a genuine review reference to `packaging/release/trust.json` through a reviewed PR. Distribute the approved public key and policy SHA-256 through an independently authenticated organisation channel. No private key or approval is needed merely to run existing candidate validation. An administrator must arrange the review/access controls; no environment, write permission or publication permission has been added to CI. Hardware-backed or keyless signing would require a separately implemented and validated integration and is not claimed by this first-release path.

## Required trust setup

A repository administrator and release reviewer must select an accountable signing identity, approve its custody/recovery/revocation process and verify its public-key fingerprint through an independent channel. No individual is assigned by this guide. A public key bundled with the candidate or copied from an unverified PR is not a trust anchor.

The initial offline implementation supports operator-held RSA keys of at least 3072 bits and OpenSSL SHA-256 signatures. It does not provision keys, call remote signing/transparency services or publish anything. Hardware/cloud key custody and keyless OIDC attestations are not implemented or tested. Use an approved isolated signing workstation and private key-file permissions; do not put persistent keys in the repository, general CI, environment dumps, command arguments as key material, screenshots or chat. Encrypted-key prompting/provider integration has not been evaluated by this CLI; no such support is claimed.

An approved policy entry must contain `spki_sha256` (SHA-256 of canonical DER SubjectPublicKeyInfo), `status=active`, `role=release-publisher`, a genuine `review_reference`, and timezone-aware `valid_from`/`valid_until`. The repository URI and schema version are checked. An administrator must record the actual review and key before adding an entry; do not copy fixture identities from tests. Obtain and pin the complete policy file's SHA-256 independently as well. Merely hashing an untrusted policy downloaded beside the artifacts establishes no trust.

To derive a public fingerprint without revealing a private key:

```sh
openssl pkey -pubin -in APPROVED-PUBLIC.pem -outform DER | openssl dgst -sha256
```

The SPKI fingerprint differs from the earlier test evidence's SHA-256 of PEM file bytes. They are labelled separately and must not be interchanged. Publisher approval refuses reuse of the candidate's temporary signing key even if it is mistakenly placed in an approved policy.

## Separate approval; immutable candidate

`scripts/trusted_release.py` first validates the pinned trust policy/key, validity and role. It verifies candidate integrity using the existing candidate signature, but does not treat that temporary signature as publisher trust. It checks the expected full source revision, version, architecture, provenance source dependency, runtime/security evidence and archive hash.

Publisher approval creates a **new** approval directory containing `RELEASE-APPROVAL.json` and its detached signature. It does not modify or re-sign the original candidate files. The approval binds the candidate SHA256SUMS digest, provenance digest, exact revision/version/platform, publisher SPKI and approved policy hash. This is an endorsement of bytes under the supplied trust policy, not an independent build attestation or approval to publish. These commands are preparation instructions; they have not been executed with an approved production identity.

After identity/policy approval, replace all uppercase placeholders explicitly:

```sh
.venv-source/bin/python scripts/trusted_release.py --sign \
  --bundle CANDIDATE_DIRECTORY --approval-dir NEW_APPROVAL_DIRECTORY \
  --public-key APPROVED-PUBLIC.pem --private-key PRIVATE_OPERATOR_KEY.pem \
  --policy APPROVED_POLICY.json --policy-sha256 INDEPENDENT_POLICY_SHA256 \
  --revision FULL_40_CHARACTER_COMMIT --version 0.1.0 --architecture arm64
```

Use the corresponding architecture for each candidate. Key material is read only from the private file, never printed or copied into approval artifacts. The supplied private key must match the approved public identity. The tool refuses existing approval directories and does not create a release tag, change settings, publish packages or deploy.

Verification requires **only the independently approved public key and policy**, never a private key:

```sh
.venv-source/bin/python scripts/trusted_release.py --verify \
  --bundle CANDIDATE_DIRECTORY --approval-dir APPROVAL_DIRECTORY \
  --public-key APPROVED-PUBLIC.pem \
  --policy APPROVED_POLICY.json --policy-sha256 INDEPENDENT_POLICY_SHA256 \
  --revision FULL_40_CHARACTER_COMMIT --version 0.1.0 --architecture arm64
```

Policy bytes and public identity are snapshotted for consistent hashing/verification; a mid-check key-file swap cannot substitute the candidate signer. The approval body is verified and parsed from the same bytes. Verification rejects unapproved/revoked/expired identities, policy-hash changes, candidate-key reuse, modified checksums or approval statements and mismatched revisions/platforms. Tests exercise real OpenSSL-compatible signatures under **isolated fixture policies**. The local CLI tested was LibreSSL 3.3.6; hosted verification results must be recorded separately. Passing those tests does not configure production trust; existing ephemeral candidates remain ineligible under the empty repository policy.

## Rotation, revocation and release review

Keep an approved public key and its independently distributed policy available for consumers; private keys need separate restricted backup and custody. Rotate through a reviewed policy change with recorded fingerprint, validity and authorisation. Mark compromised keys revoked, communicate through a verified channel and re-approve/rebuild affected artifacts as necessary. This verifier checks policy validity at verification time and has no trusted timestamp service: it refuses expired/revoked signers even for historical signatures. Do not silently relax policy to recover a green result.

Before any authorised publication, the release reviewer must also check complete platform inventories, current scans/advisories, test evidence, source/provenance, private reporting, licence notices and the supported deployment contract. Publisher approval is not proof of diagnostic accuracy or absence of vulnerabilities. See [release readiness](release-readiness.md), [maintenance responsibilities](../MAINTAINERS.md), [candidate preparation](releasing.md) and [OpenSSL's signature documentation](https://docs.openssl.org/3.0/man1/openssl-dgst/).

## Pending organisation decision

Approve the dedicated offline VERIQTA LIMITED publisher-key approach and identify the primary custodian, recovery delegate and independent reviewer. Confirm an isolated signing location, restricted offline backup, validity/rotation period and an authenticated independent channel for distributing the public fingerprint and policy hash. Only after these decisions should an organisational key be generated and its public identity reviewed into the empty trust policy. No organisational key was generated, replaced or approved during preparation. Existing ephemeral candidate keys remain test-only.
