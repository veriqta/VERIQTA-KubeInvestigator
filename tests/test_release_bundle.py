import hashlib
import json
import shutil
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    not shutil.which("openssl"), reason="OpenSSL is required for offline signing checks"
)
def test_signed_candidate_detects_tampering_and_unsigned_additions(tmp_path):
    key = tmp_path / "private.pem"
    public = tmp_path / "trusted.pem"
    subprocess.run(
        [
            "openssl",
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(key),
        ],
        check=True,
        capture_output=True,
    )
    public.write_bytes(subprocess.check_output(["openssl", "pkey", "-in", str(key), "-pubout"]))
    bundle = tmp_path / "candidate"
    bundle.mkdir()
    artifact = bundle / "application.whl"
    artifact.write_bytes(b"candidate artifact used only for signature integrity test")

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    (bundle / "provenance.json").write_text(
        json.dumps({"subject": [{"name": artifact.name, "digest": {"sha256": sha(artifact)}}]})
    )
    (bundle / "SHA256SUMS").write_text(
        "".join(f"{sha(path)}  {path.name}\n" for path in sorted(bundle.iterdir()))
    )
    subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sign",
            str(key),
            "-out",
            str(bundle / "SHA256SUMS.sig"),
            str(bundle / "SHA256SUMS"),
        ],
        check=True,
    )
    command = [
        sys.executable,
        "scripts/release_bundle.py",
        "--verify",
        str(bundle),
        "--trusted-public-key",
        str(public),
    ]
    assert subprocess.run(command, capture_output=True).returncode == 0
    artifact.write_bytes(b"tampered candidate")
    assert subprocess.run(command, capture_output=True).returncode != 0
    artifact.write_bytes(b"candidate artifact used only for signature integrity test")
    extra = bundle / "unreviewed.txt"
    extra.write_text("unsigned")
    assert subprocess.run(command, capture_output=True).returncode != 0
    extra.unlink()
    (bundle / "SHA256SUMS").write_text("0" * 64 + "  application.whl\n")
    assert subprocess.run(command, capture_output=True).returncode != 0
