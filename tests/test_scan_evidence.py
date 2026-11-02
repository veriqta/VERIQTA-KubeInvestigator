import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest

spec = importlib.util.spec_from_file_location(
    "scan_evidence", Path(__file__).resolve().parents[1] / "scripts/record_image_scan.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inputs(tmp_path):
    config = json.dumps(
        {
            "architecture": "amd64",
            "rootfs": {"diff_ids": ["sha256:layer"]},
            "config": {"Env": ["CREDENTIAL=private-runtime-value"]},
        }
    ).encode()
    archive = tmp_path / "image.tar"
    with tarfile.open(archive, "w") as bundle:
        for name, data in [
            ("manifest.json", b'[{"Config":"config.json"}]'),
            ("config.json", config),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    inspection = [
        {
            "Id": "local-index",
            "Architecture": "amd64",
            "RootFS": {"Layers": ["sha256:layer"]},
            "Config": {"Env": ["private-inspection-value"]},
        }
    ]
    scan = {
        "Metadata": {
            "ImageID": "sha256:" + hashlib.sha256(config).hexdigest(),
            "DiffIDs": ["sha256:layer"],
        },
        "Results": [
            {"Class": "os-pkgs", "Type": "alpine", "Packages": [{"Name": "sqlite-libs"}]},
            {"Class": "lang-pkgs", "Type": "python-pkg", "Packages": [{"Name": "fastapi"}]},
        ],
    }
    return [
        archive,
        inspection,
        scan,
        {"status": "passed", "python": "3.12.16", "sqlite": "3.54.1"},
        {"UpdatedAt": "2026-11-02T07:17:05Z"},
        "Version: 0.76.1",
        "amd64",
    ]


def test_evidence_preserves_findings_without_leaking_credentials(tmp_path):
    args = inputs(tmp_path)
    args[2]["Results"][0]["Secrets"] = [{"Match": "private-secret-match", "Severity": "HIGH"}]
    args[2]["Results"][0]["Vulnerabilities"] = [
        {
            "VulnerabilityID": "CVE-example",
            "Severity": "MEDIUM",
            "PkgName": "sqlite-libs",
            "Description": "private-description",
        }
    ]
    args[3]["unexpected_secret"] = "private-extra-value"
    result = module.record(*args)
    assert result["scan_outcome"] == "findings detected"
    assert result["vulnerability_counts"] == {"MEDIUM": 1}
    assert result["vulnerabilities"][0]["VulnerabilityID"] == "CVE-example"
    assert result["secret_finding_count"] == 1
    assert "private-" not in json.dumps(result)
    assert "gate_exit_code" not in result  # Evidence cannot claim the later gate has run.


@pytest.mark.parametrize("failure", ["identity", "layers", "architecture", "inventory", "runtime"])
def test_evidence_rejects_mismatched_or_incomplete_scans(tmp_path, failure):
    args = inputs(tmp_path)
    if failure == "identity":
        args[2]["Metadata"]["ImageID"] = "different"
    elif failure == "layers":
        args[2]["Metadata"]["DiffIDs"] = ["different"]
    elif failure == "architecture":
        args[-1] = "arm64"
    elif failure == "inventory":
        args[2]["Results"] = []
    else:
        args[3]["status"] = "failed"
    with pytest.raises(ValueError):
        module.record(*args)
