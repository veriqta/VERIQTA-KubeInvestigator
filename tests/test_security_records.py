import json
import logging
import secrets
import time

from fastapi.testclient import TestClient
from kubeinvestigator.app import create_app
from kubeinvestigator.config import Settings
from kubeinvestigator.policy import redact


def test_multiline_secret_material_and_connection_strings_are_redacted():
    text = 'password: |\n  first-sensitive-line\n  second-sensitive-line\nnext: visible\nsecret="quoted\nprivate-value"\n-----BEGIN PRIVATE KEY-----\nprivate-key-data\n-----END PRIVATE KEY-----\npostgresql://user:credential@db/private'
    filtered = redact(text)
    for value in [
        "first-sensitive-line",
        "second-sensitive-line",
        "private-value",
        "private-key-data",
        "credential",
        "db/private",
    ]:
        assert value not in filtered
    assert "next: visible" in filtered


def test_sensitive_actions_have_correlated_secret_free_security_records(tmp_path):
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(json.loads(record.getMessage()))

    logger = logging.getLogger("kubeinvestigator")
    handler = Capture()
    logger.addHandler(handler)
    token = secrets.token_urlsafe(32)
    settings = Settings(token=token, database=str(tmp_path / "records.db"))
    try:
        with TestClient(create_app(settings)) as client:
            assert client.get("/api/config").status_code == 401
            client.headers["Authorization"] = "Bearer " + token
            assert client.get("/api/workloads?namespace=kube-system").status_code == 403
            created = client.post(
                "/api/investigations",
                json={
                    "namespace": "veriqta-demo",
                    "scenario": "service",
                    "problem": "private problem must not be logged",
                },
            ).json()
            identifier = created["id"]
            for _ in range(100):
                report = client.get("/api/investigations/" + identifier).json()
                if report["status"] not in {"queued", "running"}:
                    break
                time.sleep(0.01)
            assert client.get("/api/investigations/" + identifier + "/export").status_code == 200
            assert client.delete("/api/investigations/" + identifier).status_code == 200
        events = {record["event"] for record in records}
        assert {
            "authentication_failed",
            "access_denied",
            "investigation_created",
            "investigation_finished",
            "report_exported",
            "report_deleted",
        } <= events
        creation = next(record for record in records if record["event"] == "investigation_created")
        assert creation["request_id"] and creation["investigation_id"] == identifier
        assert all(record["timestamp"].endswith("+00:00") for record in records)
        assert token not in str(records) and "private problem" not in str(records)
    finally:
        logger.removeHandler(handler)


def test_hsts_only_for_configured_https(tmp_path):
    settings = Settings(
        token=secrets.token_urlsafe(32), database=str(tmp_path / "records.db"), secure_cookie=True
    )
    with TestClient(create_app(settings), base_url="https://testserver") as client:
        assert client.get("/health/live").headers["strict-transport-security"] == "max-age=31536000"
    with TestClient(create_app(settings), base_url="http://testserver") as client:
        assert "strict-transport-security" not in client.get("/health/live").headers


def test_insecure_kubernetes_configuration_is_rejected(tmp_path):
    from unittest.mock import patch
    from kubernetes import client
    from kubeinvestigator.collector import Collector
    import pytest

    settings = Settings(
        token=secrets.token_urlsafe(32), database=str(tmp_path / "records.db"), source="kubernetes"
    )
    for host, verify in [("https://example.invalid", False), ("http://example.invalid", True)]:
        configuration = client.Configuration(host=host)
        configuration.verify_ssl = verify
        with (
            patch("kubernetes.config.load_incluster_config"),
            patch.object(client.Configuration, "get_default_copy", return_value=configuration),
        ):
            with pytest.raises(ValueError, match="certificate verification"):
                Collector(settings)
