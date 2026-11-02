import json
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def keys(tmp_path_factory):
    if not shutil.which("openssl"):
        pytest.skip("OpenSSL required for actual cryptographic verification")
    directory = tmp_path_factory.mktemp("publisher-fixture")
    result = {}
    for name in ["candidate", "publisher"]:
        private = directory / (name + ".pem")
        public = directory / (name + "-public.pem")
        subprocess.run(
            [
                "openssl",
                "genpkey",
                "-algorithm",
                "RSA",
                "-pkeyopt",
                "rsa_keygen_bits:3072",
                "-out",
                str(private),
            ],
            check=True,
            capture_output=True,
        )
        private.chmod(0o600)
        public.write_bytes(
            subprocess.check_output(["openssl", "pkey", "-in", str(private), "-pubout"])
        )
        result[name] = (private, public)
    return result


@pytest.fixture
def prepared(tmp_path, monkeypatch, keys):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    import trusted_release as release

    bundle = tmp_path / "candidate"
    bundle.mkdir()
    (bundle / "candidate-public.pem").write_bytes(keys["candidate"][1].read_bytes())
    archive = bundle / "kubeinvestigator-0.1.0.tar"
    archive.write_bytes(b"unit fixture only; not a runtime image")
    image = {
        "architecture": "arm64",
        "runtime_check": {"status": "passed"},
        "secret_finding_count": 0,
        "vulnerabilities": [],
        "archive_sha256": release.digest(archive),
    }
    (bundle / "image-security.json").write_text(json.dumps(image))
    revision = "a" * 40
    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "subject": [
            {"name": p.name, "digest": {"sha256": release.digest(p)}} for p in bundle.iterdir()
        ],
        "predicate": {
            "buildDefinition": {
                "externalParameters": {
                    "version": "0.1.0",
                    "revision": revision,
                    "architecture": "arm64",
                },
                "resolvedDependencies": [
                    {"uri": "git+" + release.REPOSITORY, "digest": {"gitCommit": revision}}
                ],
            }
        },
    }
    (bundle / "provenance.json").write_text(json.dumps(provenance))
    (bundle / "SHA256SUMS").write_text(
        "".join(f"{release.digest(p)}  {p.name}\n" for p in sorted(bundle.iterdir()))
    )
    subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(keys["candidate"][0]),
            "-out",
            str(bundle / "SHA256SUMS.sig"),
            str(bundle / "SHA256SUMS"),
        ],
        check=True,
    )
    signer = {
        "spki_sha256": release.fingerprint(keys["publisher"][1]),
        "status": "active",
        "role": "release-publisher",
        "review_reference": "fixture only; no production approval",
        "valid_from": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        "valid_until": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {"schema_version": 1, "repository": release.REPOSITORY, "approved_signers": [signer]}
        )
    )
    args = [
        bundle,
        tmp_path / "approval",
        keys["publisher"][1],
        policy,
        release.digest(policy),
        revision,
        "0.1.0",
        "arm64",
    ]
    return release, args, keys


def test_publisher_fixture_sign_verify_and_tamper_rejection(prepared):
    release, args, keys = prepared
    result = release.process(*args, private_key=keys["publisher"][0])
    assert result["status"] == "passed"
    assert release.process(*args)["signer_spki_sha256"] == result["signer_spki_sha256"]
    approval = args[1] / "RELEASE-APPROVAL.json"
    approval.write_text(approval.read_text().replace("0.1.0", "0.2.0"))
    with pytest.raises(subprocess.CalledProcessError):
        release.process(*args)


@pytest.mark.parametrize(
    "failure",
    [
        "policy-hash",
        "revoked",
        "expired",
        "candidate-key",
        "revision",
        "architecture",
        "wrong-private-key",
        "manifest",
        "nested-output",
    ],
)
def test_publisher_refuses_wrong_trust_or_candidate(prepared, failure):
    release, args, keys = prepared
    if failure == "policy-hash":
        args[4] = "0" * 64
    elif failure in {"revoked", "expired", "candidate-key"}:
        policy = json.loads(args[3].read_text())
        signer = policy["approved_signers"][0]
        if failure == "revoked":
            signer["status"] = "revoked"
        elif failure == "expired":
            signer["valid_until"] = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        else:
            signer["spki_sha256"] = release.fingerprint(keys["candidate"][1])
            args[2] = keys["candidate"][1]
        args[3].write_text(json.dumps(policy))
        args[4] = release.digest(args[3])
    elif failure == "revision":
        args[5] = "b" * 40
    elif failure == "architecture":
        args[7] = "amd64"
    elif failure == "nested-output":
        args[1] = args[0] / "approval"
    elif failure == "manifest":
        (args[0] / "SHA256SUMS").write_text("tampered")
    private = keys["candidate"][0] if failure == "wrong-private-key" else keys["publisher"][0]
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        release.process(*args, private_key=private)
    assert not args[1].exists()


def test_committed_empty_policy_never_trusts_fixture_identity(prepared):
    release, args, keys = prepared
    args[3] = Path("packaging/release/trust.json")
    args[4] = release.digest(args[3])
    with pytest.raises(ValueError, match="No unique approved"):
        release.process(*args, private_key=keys["publisher"][0])
    assert not args[1].exists()


def test_public_key_swap_cannot_substitute_candidate_signer(prepared, monkeypatch):
    release, args, keys = prepared
    release.process(*args, private_key=keys["publisher"][0])
    # Forge the same approval body with the untrusted candidate private key.
    subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(keys["candidate"][0]),
            "-out",
            str(args[1] / "RELEASE-APPROVAL.sig"),
            str(args[1] / "RELEASE-APPROVAL.json"),
        ],
        check=True,
    )
    copy = args[1].parent / "supplied-public.pem"
    copy.write_bytes(keys["publisher"][1].read_bytes())
    args[2] = copy
    original = release.approved

    def swap_after_policy(*values):
        fp = original(*values)
        copy.write_bytes(keys["candidate"][1].read_bytes())
        return fp

    monkeypatch.setattr(release, "approved", swap_after_policy)
    with pytest.raises(subprocess.CalledProcessError):
        release.process(*args)
