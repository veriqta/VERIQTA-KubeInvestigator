"""Regression for the Helm integer environment serialization found on a real cluster."""

import json
from pathlib import Path
import secrets
import shutil
import subprocess

import pytest
import yaml
from kubeinvestigator.config import Settings


def test_helm_integer_configuration_is_accepted_by_the_application():
    helm = shutil.which("helm")
    if not helm and Path("/tmp/darwin-arm64/helm").exists():
        helm = "/tmp/darwin-arm64/helm"
    if not helm:
        pytest.skip("Helm not installed; the dedicated chart CI job checks rendered invariants")
    rendered = subprocess.check_output(
        [
            helm,
            "template",
            "investigator",
            "charts/kubeinvestigator",
            "-f",
            "examples/values.yaml",
            "--kube-version",
            "1.35.8",
        ],
        text=True,
    )
    deployment = next(
        obj for obj in yaml.safe_load_all(rendered) if obj and obj["kind"] == "Deployment"
    )
    env = {
        item["name"].removeprefix("KI_").lower(): item["value"]
        for item in deployment["spec"]["template"]["spec"]["containers"][0]["env"]
    }
    env["namespaces"] = env["namespaces"].split(",")
    env["token"] = secrets.token_urlsafe(32)
    settings = Settings.model_validate(env)
    assert settings.max_db_bytes == 100000000
    assert env["max_db_bytes"] == "100000000"
    assert "e+" not in json.dumps(env)
