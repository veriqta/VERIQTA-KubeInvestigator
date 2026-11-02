"""Offline publisher approval, separate from candidate/test signatures. Never publishes."""

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from release_bundle import digest, verify as verify_candidate

REPOSITORY = "https://github.com/veriqta/VERIQTA-KubeInvestigator"


def command(*args, input=None):
    return subprocess.check_output(
        [str(a) for a in args], input=input, stderr=subprocess.DEVNULL, timeout=30
    )


def fingerprint(public_key):
    der = command("openssl", "pkey", "-pubin", "-in", public_key, "-outform", "DER")
    return hashlib.sha256(der).hexdigest()


def approved(policy_path, policy_sha256, public_key):
    policy_bytes = policy_path.read_bytes()
    if (
        not re.fullmatch("[a-f0-9]{64}", policy_sha256)
        or hashlib.sha256(policy_bytes).hexdigest() != policy_sha256
    ):
        raise ValueError("Trust policy differs from the independently approved hash")
    policy = json.loads(policy_bytes)
    if policy.get("schema_version") != 1 or policy.get("repository") != REPOSITORY:
        raise ValueError("Unsupported trust policy or repository")
    fp = fingerprint(public_key)
    matches = [row for row in policy["approved_signers"] if row.get("spki_sha256") == fp]
    if len(matches) != 1:
        raise ValueError(
            "No unique approved publisher identity; candidate keys are not a trust root"
        )
    signer = matches[0]
    if (
        signer.get("status") != "active"
        or signer.get("role") != "release-publisher"
        or not signer.get("review_reference")
    ):
        raise ValueError("Publisher identity is revoked, unapproved or missing review evidence")
    current = datetime.now(UTC)
    start = datetime.fromisoformat(signer["valid_from"])
    end = datetime.fromisoformat(signer["valid_until"])
    if not start.tzinfo or not end.tzinfo or not start <= current < end:
        raise ValueError("Publisher identity is outside its approved validity interval")
    text = command("openssl", "rsa", "-pubin", "-in", public_key, "-text", "-noout").decode()
    bits = re.search(r"(?:Public-Key|RSA Public-Key): \((\d+) bit\)", text)
    if not bits or int(bits[1]) < 3072:
        raise ValueError("Publisher approval requires an RSA key of at least 3072 bits")
    return fp


def candidate(bundle, revision, version, architecture, publisher_fingerprint):
    if not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", version
    ) or architecture not in {"amd64", "arm64"}:
        raise ValueError("Invalid expected release version or architecture")
    if not re.fullmatch("[a-f0-9]{40}", revision):
        raise ValueError("Expected a full source revision")
    if fingerprint(bundle / "candidate-public.pem") == publisher_fingerprint:
        raise ValueError("A temporary candidate signing identity cannot approve a release")
    verify_candidate(bundle, bundle / "candidate-public.pem")
    provenance = json.loads((bundle / "provenance.json").read_text())
    if (
        provenance.get("_type") != "https://in-toto.io/Statement/v1"
        or provenance.get("predicateType") != "https://slsa.dev/provenance/v1"
    ):
        raise ValueError("Unsupported candidate provenance format")
    definition = provenance["predicate"]["buildDefinition"]
    if definition["externalParameters"] != {
        "version": version,
        "revision": revision,
        "architecture": architecture,
    }:
        raise ValueError("Candidate provenance does not match the expected release")
    if {"uri": "git+" + REPOSITORY, "digest": {"gitCommit": revision}} not in definition[
        "resolvedDependencies"
    ]:
        raise ValueError("Candidate source dependency does not match the expected revision")
    image = json.loads((bundle / "image-security.json").read_text())
    if (
        image["architecture"] != architecture
        or image["runtime_check"]["status"] != "passed"
        or image["secret_finding_count"]
        or any(v["Severity"] in {"HIGH", "CRITICAL"} for v in image["vulnerabilities"])
    ):
        raise ValueError("Candidate architecture/runtime/security gate failed")
    if image["archive_sha256"] != digest(bundle / f"kubeinvestigator-{version}.tar"):
        raise ValueError("Candidate image archive differs from the recorded scan")
    return {
        "schema_version": 1,
        "purpose": "publisher-approval",
        "repository": REPOSITORY,
        "revision": revision,
        "version": version,
        "architecture": architecture,
        "signer_spki_sha256": publisher_fingerprint,
        "candidate_manifest_sha256": digest(bundle / "SHA256SUMS"),
        "candidate_provenance_sha256": digest(bundle / "provenance.json"),
    }


def _process(
    bundle,
    approval,
    public_key,
    policy,
    policy_hash,
    revision,
    version,
    architecture,
    private_key=None,
):
    if approval.resolve().is_relative_to(bundle.resolve()):
        raise ValueError("Publisher approval must be outside the immutable candidate")
    fp = approved(policy, policy_hash, public_key)
    expected = candidate(bundle, revision, version, architecture, fp)
    expected["trust_policy_sha256"] = policy_hash
    if private_key:
        if private_key.stat().st_mode & 0o077:
            raise ValueError("Publisher private key file must have private permissions")
        derived = command("openssl", "pkey", "-in", private_key, "-pubout", "-outform", "DER")
        if hashlib.sha256(derived).hexdigest() != fp:
            raise ValueError("Private key does not match the approved publisher")
        # New directory only; preserve the candidate and previous approvals unchanged.
        approval.mkdir(parents=True, mode=0o700, exist_ok=False)
        body = approval / "RELEASE-APPROVAL.json"
        body.write_text(json.dumps(expected, indent=2) + "\n")
        command(
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            private_key,
            "-out",
            approval / "RELEASE-APPROVAL.sig",
            body,
        )
    body_bytes = (approval / "RELEASE-APPROVAL.json").read_bytes()
    command(
        "openssl",
        "dgst",
        "-sha256",
        "-verify",
        public_key,
        "-signature",
        approval / "RELEASE-APPROVAL.sig",
        input=body_bytes,
    )
    if json.loads(body_bytes) != expected:
        raise ValueError("Publisher approval is for a different candidate/revision/platform")
    return {
        "status": "passed",
        "purpose": "publisher approval under supplied trust policy",
        "signer_spki_sha256": fp,
        "policy_sha256": policy_hash,
        "revision": revision,
        "architecture": architecture,
        "scope": "Artifact endorsement only; no independent builder attestation, SLSA level or live-model accuracy is established.",
    }


def process(
    bundle,
    approval,
    public_key,
    policy,
    policy_hash,
    revision,
    version,
    architecture,
    private_key=None,
):
    # Freeze public identity bytes before policy/fingerprint and signature checks.
    # Changing the caller's key file mid-verification must not change the signer.
    public_bytes = public_key.read_bytes()
    with tempfile.TemporaryDirectory(prefix="veriqta-publisher-") as directory:
        frozen_public = Path(directory) / "public.pem"
        frozen_public.write_bytes(public_bytes)
        return _process(
            bundle,
            approval,
            frozen_public,
            policy,
            policy_hash,
            revision,
            version,
            architecture,
            private_key,
        )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sign", action="store_true")
    mode.add_argument("--verify", action="store_true")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--approval-dir", type=Path, required=True)
    p.add_argument("--public-key", type=Path, required=True)
    p.add_argument("--private-key", type=Path)
    p.add_argument("--policy", type=Path, default=Path("packaging/release/trust.json"))
    p.add_argument(
        "--policy-sha256",
        required=True,
        help="Obtain independently, never from the candidate bundle",
    )
    p.add_argument("--revision", required=True)
    p.add_argument("--version", default="0.1.0")
    p.add_argument("--architecture", choices=["amd64", "arm64"], required=True)
    a = p.parse_args()
    if a.sign and not a.private_key:
        p.error("--sign requires an approved operator-held private key")
    if a.verify and a.private_key:
        p.error("Verification must not receive a private key")
    try:
        result = process(
            a.bundle,
            a.approval_dir,
            a.public_key,
            a.policy,
            a.policy_sha256,
            a.revision,
            a.version,
            a.architecture,
            a.private_key if a.sign else None,
        )
    except (
        ValueError,
        KeyError,
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ):
        raise SystemExit(
            "Publisher approval refused: check the approved policy/key, validity, expected revision/platform and candidate integrity. No publication performed."
        ) from None
    print(json.dumps(result))


if __name__ == "__main__":
    main()
