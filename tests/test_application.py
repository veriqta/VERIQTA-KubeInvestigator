import asyncio
import secrets
import time
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from pydantic import ValidationError
from kubeinvestigator.app import create_app, markdown
from kubeinvestigator.config import Settings
from kubeinvestigator.collector import Collector
from kubeinvestigator.policy import Policy, redact
from kubeinvestigator.schemas import ToolArgs, Report, Request, Finding
from kubeinvestigator.store import Store
from kubeinvestigator.engine import Engine


@pytest.fixture
def settings(tmp_path):
    return Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "records.db"))


@pytest.fixture
def client(settings):
    app = create_app(settings)
    with TestClient(app) as c:
        c.headers["Authorization"] = "Bearer " + settings.token.get_secret_value()
        yield c


def wait(c, identifier):
    for _ in range(100):
        r = c.get("/api/investigations/" + identifier).json()
        if r["status"] not in {"queued", "running"}:
            return r
        time.sleep(0.01)
    pytest.fail("Investigation did not finish")


def body(scenario="service", workload=""):
    return dict(
        namespace="veriqta-demo",
        scenario=scenario,
        workload=workload,
        problem="Application is unavailable",
    )


@pytest.mark.parametrize("scenario", ["crash", "image", "service"])
def test_workflow(client, scenario):
    response = client.post("/api/investigations", json=body(scenario))
    assert response.status_code == 202
    r = wait(client, response.json()["id"])
    assert r["status"] == "completed"
    assert r["mock"] and r["source"] == "fixture" and r["observations"]
    assert r["finding"]["evidence_ids"]
    for fmt in ["json", "md"]:
        export = client.get(f"/api/investigations/{r['id']}/export?format={fmt}")
        assert export.status_code == 200 and "MOCK" in export.text.upper()
    child = client.post(f"/api/investigations/{r['id']}/followup").json()
    followup = wait(client, child["id"])
    assert followup["parent_id"] == r["id"]
    assert followup["evidence"][0]["collected_at"] > r["evidence"][0]["collected_at"]
    assert "cannot verify" in followup["verification"]
    assert client.delete("/api/investigations/" + r["id"]).status_code == 200
    assert client.get("/api/investigations/" + r["id"]).status_code == 404


def test_named_service_uses_all_pods(client):
    r = wait(
        client, client.post("/api/investigations", json=body("service", "frontend")).json()["id"]
    )
    pods = r["evidence"][0]["data"]
    assert len(pods) == 3 and r["observations"]


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/config", "get"),
        ("/api/investigations", "get"),
        ("/api/investigations/guess", "get"),
        ("/api/investigations/guess/export", "get"),
        ("/api/investigations/guess/cancel", "post"),
        ("/api/investigations/guess/followup", "post"),
        ("/metrics", "get"),
        ("/api/diagnostics", "post"),
        ("/api/investigations/guess", "delete"),
    ],
)
def test_endpoints_require_auth(client, path, method):
    client.headers.pop("Authorization")
    assert getattr(client, method)(path).status_code == 401


def test_csrf_logout(settings):
    with TestClient(create_app(settings)) as c:
        assert c.post("/api/login", json={"token": "wrong"}).status_code == 401
        csrf = c.post("/api/login", json={"token": settings.token.get_secret_value()}).json()[
            "csrf"
        ]
        assert c.get("/api/config").status_code == 200
        assert c.post("/api/investigations", json=body()).status_code == 403
        c.headers["x-csrf-token"] = csrf
        assert c.post("/api/investigations", json=body()).status_code == 202
        assert c.post("/api/logout").status_code == 200
        assert c.get("/api/config").status_code == 401


def test_namespace_and_write_policy(client, settings):
    bad = body()
    bad["namespace"] = "kube-system"
    assert client.post("/api/investigations", json=bad).status_code == 403
    assert client.get("/api/workloads?namespace=kube-system").status_code == 403
    with pytest.raises(HTTPException):
        Collector(settings).collect(ToolArgs(namespace="other", resource="pods"), "E1")
    for resource in ["secrets", "exec", "nodes", "patch", "proxy", "namespaces"]:
        with pytest.raises(ValidationError):
            ToolArgs(namespace="veriqta-demo", resource=resource)
    with pytest.raises(ValueError):
        Policy(settings).tool(
            ToolArgs(namespace="veriqta-demo", resource="logs", name="pod", container="app")
        )


def test_config_validation(settings):
    with pytest.raises(ValidationError):
        Settings(token="short")
    with pytest.raises(ValidationError):
        Settings(token=settings.token, namespaces=["*"])
    with pytest.raises(ValidationError):
        Settings(token=settings.token, provider="openai")
    with pytest.raises(ValidationError):
        Request(**{**body(), "scenario": "run arbitrary commands"})


def test_redaction_and_html(client):
    data = {"text": "password=hunter2 Bearer abc.def https://example.invalid/leak", "number": 1}
    result = redact(data)
    assert (
        "hunter2" not in result["text"]
        and "abc.def" not in result["text"]
        and "https://" not in result["text"]
    )
    attack = body()
    attack["problem"] = "<script>alert(1)</script> [click](javascript:alert(1))"
    r = wait(client, client.post("/api/investigations", json=attack).json()["id"])
    report = Report.model_validate(r)
    assert "<script>" not in markdown(report)
    assert client.get("/").headers["content-security-policy"].startswith("default-src 'self'")
    js = client.get("/static/app.js").text
    assert "innerHTML" not in js and "textContent" in js


def test_retention_restart_capacity(settings):
    store = Store(settings)
    r = Report(
        id="old",
        **body(),
        provider="mock",
        model="fixture",
        source="fixture",
        mock=True,
        status="completed",
        created_at=(datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    )
    store.save(r)
    store.cleanup()
    assert store.get("old") is None
    r.id = "inflight"
    r.created_at = datetime.now(timezone.utc).isoformat()
    r.status = "running"
    store.save(r)
    store.close()
    store = Store(settings)
    assert store.get("inflight").status == "interrupted"
    settings.max_records = 1
    assert not store.capacity()
    store.delete("inflight")
    assert store.capacity()
    store.close()


def test_missing_permissions(settings):
    class Denied(Collector):
        def collect(self, *args):
            raise PermissionError("sensitive message never exposed")

    with TestClient(create_app(settings, Denied(settings))) as c:
        c.headers["Authorization"] = "Bearer " + settings.token.get_secret_value()
        r = wait(c, c.post("/api/investigations", json=body()).json()["id"])
        assert r["status"] == "insufficient evidence"
        assert all(e["error"] for e in r["evidence"])
        assert "sensitive message" not in str(r)


def test_budgets_invalid_references_and_provider_failure(settings):
    async def check():
        store = Store(settings)
        engine = Engine(settings, store, Collector(settings))

        def report():
            return Report(
                id=secrets.token_hex(4),
                **body(),
                provider="openai",
                model="test",
                source="fixture",
                mock=False,
            )

        class Invented:
            async def turn(self, r):
                return {
                    "finding": Finding(
                        diagnosis="invented",
                        assessment="supported",
                        evidence_ids=["E99"],
                        alternatives=[],
                        next_steps=[],
                    ).model_dump()
                }, {}

        engine.provider = Invented()
        r = report()
        await engine.execute(r)
        assert r.status == "failed" and r.finding is None

        class BadTool:
            async def turn(self, r):
                return {"tool": {"namespace": "kube-system", "resource": "pods"}}, {}

        engine.provider = BadTool()
        r = report()
        await engine.execute(r)
        assert r.status == "failed"

        class Unavailable:
            async def turn(self, r):
                raise TimeoutError("not returned to user")

        engine.provider = Unavailable()
        r = report()
        await engine.execute(r)
        assert r.status == "failed" and r.finding is None
        engine.provider = None
        settings.max_calls = 1
        r = report()
        await engine.execute(r)
        assert r.status == "failed" and len(r.evidence) == 1
        store.close()

    asyncio.run(check())


def test_cancellation_and_concurrency(settings):
    async def check():
        settings.concurrency = 1
        store = Store(settings)
        engine = Engine(settings, store, Collector(settings))
        gate = asyncio.Event()

        async def slow(r):
            await gate.wait()

        engine.investigate = slow
        rows = [
            Report(
                id=str(i), **body(), provider="mock", model="fixture", source="fixture", mock=True
            )
            for i in range(2)
        ]
        for r in rows:
            engine.submit(r)
        await asyncio.sleep(0.02)
        assert store.get("0").status == "running" and store.get("1").status == "queued"
        await engine.shutdown()
        assert all(store.get(str(i)).status == "cancelled" for i in range(2))
        store.close()

    asyncio.run(check())


def test_oversize_input(client):
    assert client.post("/api/login", content="x" * 10001).status_code == 413
    bad = body()
    bad["problem"] = "x" * 2001
    assert client.post("/api/investigations", json=bad).status_code == 422


def test_sensitive_key_redaction_and_private_database(settings):
    assert redact({"api_key": "very-sensitive", "nested": {"password": "private"}}) == {
        "api_key": "[REDACTED]",
        "nested": {"password": "[REDACTED]"},
    }
    store = Store(settings)
    from pathlib import Path

    assert Path(settings.database).stat().st_mode & 0o077 == 0
    store.close()


def test_config_errors_do_not_expose_credentials():
    token = secrets.token_urlsafe(32)
    with pytest.raises(ValidationError) as error:
        Settings(token=token, namespaces=["*"])
    assert token not in str(error.value)
