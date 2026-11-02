"""Prepare or verify a local signed candidate; never publish or use external signing services."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from record_image_scan import record

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=None, input=None):
    return subprocess.check_output([str(a) for a in args], cwd=cwd, input=input)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(directory, trusted_public_key):
    # Trust must be established independently; a bundled key alone proves no publisher identity.
    run(
        "openssl",
        "dgst",
        "-sha256",
        "-verify",
        trusted_public_key,
        "-signature",
        directory / "SHA256SUMS.sig",
        directory / "SHA256SUMS",
    )
    if any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError("Candidate bundle must contain only regular files")
    hashes = {}
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split("  ", 1)
        if Path(name).name != name or name in hashes or len(expected) != 64:
            raise ValueError("Invalid candidate checksum entry")
        path = directory / name
        if path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError("Candidate artifact checksum mismatch")
        hashes[name] = expected
    actual = {p.name for p in directory.iterdir() if p.is_file()} - {"SHA256SUMS", "SHA256SUMS.sig"}
    if actual != set(hashes):
        raise ValueError("Unsigned or missing candidate files")
    statement = json.loads((directory / "provenance.json").read_text())
    subjects = {s["name"]: s["digest"]["sha256"] for s in statement["subject"]}
    if subjects != {name: value for name, value in hashes.items() if name != "provenance.json"}:
        raise ValueError("Provenance subjects do not match signed artifacts")
    return {
        "status": "passed",
        "files": len(hashes),
        "public_key_sha256": digest(trusted_public_key),
        "scope": "Offline checksum/signature/subject verification; local signer identity is not independently trusted and no SLSA level is claimed.",
    }


def prepare(key):
    endpoint = (
        os.environ.get("DOCKER_HOST")
        or run("docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}")
        .decode()
        .strip()
    )
    if not endpoint.startswith("unix:///"):
        raise ValueError("Candidate preparation requires a local Unix-socket Docker runtime")
    if key.stat().st_mode & 0o077:
        raise ValueError("Signing key permissions must be private (chmod 600)")
    if run("git", "status", "--porcelain", cwd=ROOT).strip():
        raise ValueError("Commit project sources before building a candidate")
    revision = run("git", "rev-parse", "HEAD", cwd=ROOT).decode().strip()
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    output = ROOT / "dist" / f"{version}-{revision[:12]}"
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="veriqta-release-") as scratch:
        scratch = Path(scratch)
        archive = scratch / "source.tar"
        archive.write_bytes(run("git", "archive", "HEAD", cwd=ROOT))
        source = scratch / "source"
        source.mkdir()
        with tarfile.open(archive) as bundle:
            bundle.extractall(source, filter="data")
        run(sys.executable, "-m", "build", "--no-isolation", "--outdir", output, cwd=source)
        run("helm", "package", "charts/kubeinvestigator", "--destination", output, cwd=source)
        image = f"kubeinvestigator:{version}-{revision[:12]}"
        run("docker", "build", "--target", "runtime", "-t", image, ".", cwd=source)
        image_archive = output / f"kubeinvestigator-{version}.tar"
        run("docker", "save", image, "-o", image_archive)
        inspection = json.loads(run("docker", "image", "inspect", image))
        runtime = json.loads(
            run(
                "docker",
                "run",
                "--rm",
                "-i",
                "--read-only",
                "--network",
                "none",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=32m",
                image,
                "python",
                "-",
                input=(source / "scripts/check_runtime.py").read_bytes(),
            )
        )
        cache = ROOT / ".capture/release-trivy"
        raw_scan = scratch / "scan.json"
        run(
            "trivy",
            "image",
            "--cache-dir",
            cache,
            "--input",
            image_archive,
            "--scanners",
            "vuln,secret",
            "--list-all-pkgs",
            "--format",
            "json",
            "--output",
            raw_scan,
        )
        scan = json.loads(raw_scan.read_text())
        version_text = run("trivy", "version").decode()
        evidence = record(
            image_archive,
            inspection,
            scan,
            runtime,
            json.loads((cache / "db/metadata.json").read_text()),
            version_text,
            inspection[0]["Architecture"],
        )
        if evidence["secret_finding_count"] or any(
            v["Severity"] in {"HIGH", "CRITICAL"}
            for item in scan.get("Results", [])
            for v in item.get("Vulnerabilities", [])
        ):
            raise ValueError(
                "Candidate blocked by HIGH/CRITICAL or secret findings; no signature generated"
            )
        (output / "image-security.json").write_text(json.dumps(evidence, indent=2) + "\n")
        run(
            "trivy",
            "image",
            "--cache-dir",
            cache,
            "--skip-db-update",
            "--input",
            image_archive.name,
            "--format",
            "spdx-json",
            "--output",
            "sbom.spdx.json",
            cwd=output,
        )
    (output / "RELEASE-NOTES.md").write_bytes((ROOT / "CHANGELOG.md").read_bytes())
    (output / "requirements.lock").write_bytes((ROOT / "requirements.lock").read_bytes())
    public = output / "candidate-public.pem"
    public.write_bytes(run("openssl", "pkey", "-in", key, "-pubout"))
    for artifact in output.iterdir():
        if artifact.suffix in {".json", ".md", ".lock", ".pem"}:
            text = artifact.read_text()
            if str(ROOT) in text or re.search(r"/(?:Users|home)/[^/\s]+|/private/var/", text):
                raise ValueError("Candidate metadata contains a private host path; signing refused")
    subjects = [
        {"name": p.name, "digest": {"sha256": digest(p)}}
        for p in sorted(output.iterdir())
        if p.is_file()
    ]
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subjects,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/veriqta/VERIQTA-KubeInvestigator/local-candidate/v1",
                "externalParameters": {
                    "version": version,
                    "revision": revision,
                    "architecture": inspection[0]["Architecture"],
                },
                "resolvedDependencies": [
                    {
                        "uri": "git+https://github.com/veriqta/VERIQTA-KubeInvestigator",
                        "digest": {"gitCommit": revision},
                    }
                ],
            },
            "runDetails": {
                "builder": {"id": "local-development-builder; not independently attested"},
                "metadata": {"finishedOn": datetime.now(UTC).isoformat()},
            },
        },
    }
    (output / "provenance.json").write_text(json.dumps(statement, indent=2) + "\n")
    (output / "SHA256SUMS").write_text(
        "".join(f"{digest(p)}  {p.name}\n" for p in sorted(output.iterdir()) if p.is_file())
    )
    run(
        "openssl",
        "dgst",
        "-sha256",
        "-sign",
        key,
        "-out",
        output / "SHA256SUMS.sig",
        output / "SHA256SUMS",
    )
    return output, verify(output, public)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--verify", type=Path)
    p.add_argument("--signing-key", type=Path)
    p.add_argument("--trusted-public-key", type=Path)
    a = p.parse_args()
    if a.prepare:
        if not a.signing_key:
            p.error("Provide a private local signing key; no remote signing is performed")
        output, result = prepare(a.signing_key.resolve())
        print(json.dumps({"candidate": output.name, "verification": result}))
    else:
        if not a.trusted_public_key:
            p.error("Provide an independently trusted public key")
        print(json.dumps(verify(a.verify, a.trusted_public_key)))


if __name__ == "__main__":
    os.umask(0o077)
    main()
