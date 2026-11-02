import asyncio
import secrets
import sqlite3
from types import SimpleNamespace as Obj

from fastapi.testclient import TestClient
from kubeinvestigator.app import create_app, markdown
from kubeinvestigator.collector import Collector
from kubeinvestigator.config import Settings
from kubeinvestigator.engine import Engine
from kubeinvestigator.schemas import Report, ToolArgs
from kubeinvestigator.store import Store
import pytest


def settings(tmp_path, **kwargs):
    return Settings(
        token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"), **kwargs
    )


def report(**kwargs):
    return Report(
        id="audit",
        namespace="veriqta-demo",
        workload="checkout-crash",
        problem="The container repeatedly exits",
        scenario="crash",
        provider="mock",
        model="fixture",
        source="fixture",
        mock=True,
        **kwargs,
    )


def test_opt_in_crash_logs_and_relevant_events(tmp_path):
    async def run():
        s = settings(tmp_path, logs=True)

        class Recording(Collector):
            calls = []

            def collect(self, args, identifier):
                self.calls.append(args)
                return super().collect(args, identifier)

        collector = Recording(s)
        store = Store(s)
        engine = Engine(s, store, collector)
        r = report()
        await engine.execute(r)
        assert r.status == "completed"
        assert collector.calls[1].resource == "events" and collector.calls[1].name == r.workload
        assert [(a.resource, a.previous) for a in collector.calls[-2:]] == [
            ("logs", False),
            ("logs", True),
        ]
        assert len(r.evidence) == 4
        assert r.evidence[1].data == []  # The fixture's unrelated catalog event is excluded.
        exported = markdown(r)
        for value in ["checkout", "Duration seconds:", "Evidence IDs:", "Evidence source:"]:
            assert value in exported
        store.close()

    asyncio.run(run())


def test_nested_endpointslice_truncation(tmp_path):
    c = Collector(settings(tmp_path))

    def get(*args, **kwargs):
        return Obj(
            items=[
                Obj(
                    metadata=Obj(name="slice", labels={}),
                    endpoints=[Obj(conditions=Obj(ready=True), target_ref=None)] * 101,
                )
            ],
            metadata=Obj(_continue=None),
        )

    c.core = Obj(list_namespaced_pod=get, list_namespaced_event=get, list_namespaced_service=get)
    c.apps = Obj(list_namespaced_deployment=get, list_namespaced_replica_set=get)
    c.discovery = Obj(list_namespaced_endpoint_slice=get)
    data, truncated = c.live(ToolArgs(namespace="veriqta-demo", resource="endpointslices"))
    assert truncated and len(data[0]["endpoints"]) == 100


def test_backup_restore_and_future_schema_rejection(tmp_path):
    s = settings(tmp_path)
    store = Store(s)
    r = report(status="completed")
    store.save(r)
    backup_path = tmp_path / "backup.db"
    with sqlite3.connect(backup_path) as backup:
        store.db.backup(backup)
    store.delete(r.id)
    store.close()
    s.database = str(backup_path)
    restored = Store(s)
    assert restored.get(r.id).model_dump() == r.model_dump()
    restored.db.execute("PRAGMA user_version=2")
    restored.close()
    with pytest.raises(RuntimeError, match="newer"):
        Store(s)


def test_session_expiry_restart_and_login_rate_limit(tmp_path):
    s = settings(tmp_path)
    s.session_seconds = -1  # Test clock boundary without sleeping or changing the system clock.
    with TestClient(create_app(s)) as client:
        client.post("/api/login", json={"token": s.token.get_secret_value()})
        assert client.get("/api/config").status_code == 401
    s.session_seconds = 3600
    with TestClient(create_app(s)) as client:
        client.post("/api/login", json={"token": s.token.get_secret_value()})
        cookie = client.cookies.get("ki_session")
        assert client.get("/api/config").status_code == 200
    with TestClient(create_app(s)) as client:
        client.cookies.set("ki_session", cookie)
        assert client.get("/api/config").status_code == 401
        for _ in range(10):
            assert client.post("/api/login", json={"token": "incorrect"}).status_code == 401
        assert client.post("/api/login", json={"token": "incorrect"}).status_code == 429


def test_retention_preserves_active_and_byte_cap_refuses_admission(tmp_path):
    s = settings(tmp_path)
    store = Store(s)
    r = report(status="running", created_at="2000-01-01T00:00:00+00:00")
    store.save(r)
    store.cleanup()
    assert store.get(r.id) is not None
    s.max_db_bytes = 1
    assert not store.capacity()
    store.close()


def test_smoke_script_prerequisite_failure():
    import subprocess

    result = subprocess.run(
        ["/bin/bash", "scripts/smoke.sh"],
        env={"PATH": "/nonexistent"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "missing required tools: docker kind kubectl helm" in result.stderr


def test_non_ascii_invalid_credential_is_rejected_without_server_error(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as client:
        assert client.post("/api/login", json={"token": "incorrect-🔒"}).status_code == 401


def test_empty_real_sdk_endpointslice_is_valid_evidence():
    from kubernetes import client

    slice = client.V1EndpointSlice(
        address_type="IPv4",
        endpoints=None,
        metadata=client.V1ObjectMeta(
            name="empty", labels={"kubernetes.io/service-name": "frontend"}
        ),
    )
    projected = Collector.project("endpointslices", slice)
    assert projected == {"name": "empty", "service": "frontend", "endpoints": []}


def test_crash_transition_is_failure_but_historical_exit_on_ready_pod_is_not():
    from kubeinvestigator.analysis import observations
    from kubeinvestigator.schemas import Evidence

    r = report()
    container = {
        "name": "app",
        "ready": False,
        "restarts": 3,
        "waiting": None,
        "terminated": {"reason": "Error", "exit_code": 1},
        "last_exit": {"reason": "Error", "exit_code": 1},
    }
    r.evidence = [
        Evidence(
            id="E1",
            resource="veriqta-demo/pods/checkout-crash",
            data=[{"name": "checkout-crash", "containers": [container]}],
        )
    ]
    assert "repeatedly exited" in observations(r)[0]
    container["terminated"] = None
    container["ready"] = True
    assert observations(r) == []


def test_smoke_rejects_remote_runtime_before_contacting_it(tmp_path):
    import subprocess

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "docker-called"
    for tool in ["docker", "kind", "kubectl", "helm"]:
        executable = bin_dir / tool
        executable.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\nexit 0\n')
        executable.chmod(0o755)
    result = subprocess.run(
        ["/bin/bash", "scripts/smoke.sh"],
        env={"PATH": str(bin_dir) + ":/usr/bin:/bin", "DOCKER_HOST": "ssh://remote.invalid"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2 and "remote runtimes are not supported" in result.stderr
    assert not marker.exists()
    # A local Unix socket reaches the daemon check, then stops at missing setup.
    local = subprocess.run(
        ["/bin/bash", "scripts/smoke.sh"],
        env={
            "PATH": str(bin_dir) + ":/usr/bin:/bin",
            "DOCKER_HOST": "unix:///tmp/test-only.sock",
            "VENV": str(tmp_path / "missing-venv"),
        },
        capture_output=True,
        text=True,
    )
    assert local.returncode == 2 and "run make setup" in local.stderr
    assert marker.exists()
