"""Validate exact Docker-archive scan lineage and emit credential-free CI evidence."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import tarfile


def record(archive, inspection, scan, runtime, database, scanner_info, architecture):
    image = inspection[0]
    with tarfile.open(archive) as bundle:
        manifest = json.load(bundle.extractfile("manifest.json"))
        if len(manifest) != 1:
            raise ValueError("Expected one architecture/image per Docker archive")
        config_bytes = bundle.extractfile(manifest[0]["Config"]).read()
    config = json.loads(config_bytes)
    config_digest = "sha256:" + hashlib.sha256(config_bytes).hexdigest()

    def nondefault_configuration(value):
        # Docker API versions differ in whether empty/default fields are emitted.
        return {key: item for key, item in value.items() if item not in (None, "", False, [], {})}

    if nondefault_configuration(config.get("config", {})) != nondefault_configuration(
        image.get("Config", {})
    ):
        raise ValueError("Archived runtime configuration differs from the executed image")
    descriptor = image.get("Descriptor")
    if descriptor:
        # Docker's containerd store may expose an OCI manifest/index ID rather than
        # a configuration ID. Bind that exact object graph to the scanned config.
        with tarfile.open(archive) as bundle:

            def reaches_config(digest, depth=0):
                if depth > 3 or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                    raise ValueError("Invalid archived image descriptor")
                blob = bundle.extractfile("blobs/sha256/" + digest.split(":")[1]).read()
                if "sha256:" + hashlib.sha256(blob).hexdigest() != digest:
                    raise ValueError("Archived image descriptor digest mismatch")
                node = json.loads(blob)
                if "config" in node:
                    return node["config"]["digest"] == config_digest
                return any(
                    reaches_config(item["digest"], depth + 1) for item in node.get("manifests", [])
                )

            if descriptor["digest"] != image["Id"] or not reaches_config(descriptor["digest"]):
                raise ValueError("Executed image descriptor does not reach scanned runtime")
    elif image["Id"] != config_digest:
        raise ValueError("Executed image configuration identity differs from archive")
    if config_digest != scan["Metadata"]["ImageID"]:
        raise ValueError("Scanner identity does not match archived runtime configuration")
    if config["architecture"] != architecture or image["Architecture"] != architecture:
        raise ValueError("Unexpected image architecture")
    layers = config["rootfs"]["diff_ids"]
    if layers != image["RootFS"]["Layers"] or layers != scan["Metadata"]["DiffIDs"]:
        raise ValueError("Scanner and inspected runtime filesystem lineage differ")
    results = scan.get("Results", [])
    os_packages = sum(len(r.get("Packages", [])) for r in results if r["Class"] == "os-pkgs")
    python_packages = sum(
        len(r.get("Packages", [])) for r in results if r.get("Type") == "python-pkg"
    )
    if not os_packages or not python_packages:
        raise ValueError("OS/Python inventory missing; refusing an incomplete clean scan record")
    if runtime.get("status") != "passed":
        raise ValueError("Runtime check did not pass")
    version = re.search(r"^Version:\s*(\S+)", scanner_info, re.MULTILINE)
    if not version or not database.get("UpdatedAt"):
        raise ValueError("Scanner version/database timestamp missing")
    vulnerabilities = [v for r in results for v in r.get("Vulnerabilities", [])]
    secrets = sum(len(r.get("Secrets", [])) for r in results)
    with Path(archive).open("rb") as stream:
        archive_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "architecture": architecture,
        "execution": {
            "machine_architecture": platform.machine(),
            "runner_architecture": os.getenv("RUNNER_ARCH"),
            "runner_os": os.getenv("RUNNER_OS"),
        },
        "config_digest": config_digest,
        "runtime_configuration_matches": True,
        "executed_image_identity_verified": True,
        "inspected_image_id": image["Id"],
        "archive_sha256": archive_digest,
        "filesystem_diff_ids": layers,
        "scanner": {"version": version[1], "database": database},
        "inventory": {"os_packages": os_packages, "python_packages": python_packages},
        "scan_outcome": (
            "findings detected"
            if vulnerabilities or secrets
            else "no findings detected by the recorded scan"
        ),
        "vulnerability_counts": dict(Counter(v["Severity"] for v in vulnerabilities)),
        "vulnerabilities": [
            {
                key: v.get(key)
                for key in (
                    "VulnerabilityID",
                    "PkgName",
                    "InstalledVersion",
                    "FixedVersion",
                    "Severity",
                    "Status",
                    "Layer",
                )
            }
            for v in vulnerabilities
        ],
        "secret_finding_count": secrets,
        "runtime_check": {
            k: runtime[k]
            for k in (
                "status",
                "uid",
                "python",
                "sqlite",
                "sqlite_libraries",
                "checks",
                "application",
            )
            if k in runtime
        },
        "gate_policy": "HIGH/CRITICAL and secret gate runs separately after evidence; this record is not its exit status",
        "source_revision": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "limitations": "No findings detected is not proof of no vulnerabilities; no live-model accuracy is established",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "archive",
        "inspect",
        "scan",
        "runtime-check",
        "database",
        "scanner-info",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--architecture", choices=["amd64", "arm64"], required=True)
    args = parser.parse_args()
    result = record(
        args.archive,
        json.loads(args.inspect.read_text()),
        json.loads(args.scan.read_text()),
        json.loads(args.runtime_check.read_text()),
        json.loads(args.database.read_text()),
        args.scanner_info.read_text(),
        args.architecture,
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
