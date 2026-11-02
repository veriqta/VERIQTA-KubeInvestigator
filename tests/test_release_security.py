import secrets
import time
from pathlib import Path
from fastapi.testclient import TestClient
from kubeinvestigator.app import create_app
from kubeinvestigator.config import Settings


def test_scope_revocation_protects_every_existing_report_action(tmp_path):
    settings = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
    with TestClient(create_app(settings)) as client:
        client.headers["Authorization"] = "Bearer " + settings.token.get_secret_value()
        created = client.post(
            "/api/investigations",
            json={
                "namespace": "veriqta-demo",
                "scenario": "service",
                "problem": "Sample selector failure",
            },
        ).json()
        identifier = created["id"]
        for _ in range(100):
            if client.get("/api/investigations/" + identifier).json()["status"] not in {
                "queued",
                "running",
            }:
                break
            time.sleep(0.01)
        settings.namespaces = ["another-authorised-namespace"]
        assert client.get("/api/investigations").json() == []
        for method, suffix in [
            ("get", ""),
            ("get", "/export"),
            ("get", "/export?format=md"),
            ("post", "/cancel"),
            ("post", "/followup"),
            ("delete", ""),
        ]:
            assert (
                getattr(client, method)("/api/investigations/" + identifier + suffix).status_code
                == 403
            )


def test_sql_path_markdown_and_proxy_identity_inputs_remain_data(tmp_path):
    settings = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
    with TestClient(create_app(settings)) as client:
        assert (
            client.get(
                "/api/config",
                headers={
                    "X-Forwarded-User": "admin",
                    "X-Auth-Request-Email": "admin@example.invalid",
                },
            ).status_code
            == 401
        )
        client.headers["Authorization"] = "Bearer " + settings.token.get_secret_value()
        for identifier in ["x' OR '1'='1", "..%2F..%2Fetc%2Fpasswd"]:
            assert client.get("/api/investigations/" + identifier).status_code == 404
        assert client.get("/static/..%2F..%2F.env").status_code == 404
        assert not Path(tmp_path / "unauthorised").exists()


def test_validation_error_does_not_echo_login_credential(tmp_path):
    settings = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
    with TestClient(create_app(settings)) as client:
        supplied = "secret-value-" * 100
        response = client.post("/api/login", json={"token": supplied})
        assert response.status_code == 422
        assert supplied not in response.text


def test_history_is_bounded_summaries_without_evidence(tmp_path):
    from kubeinvestigator.schemas import Report, Evidence

    settings = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
    with TestClient(create_app(settings)) as client:
        client.headers["Authorization"] = "Bearer " + settings.token.get_secret_value()
        for n in range(35):
            client.app.state.store.save(
                Report(
                    id=str(n),
                    namespace="veriqta-demo",
                    workload="",
                    problem="private problem",
                    scenario="service",
                    provider="mock",
                    model="fixture",
                    source="fixture",
                    mock=True,
                    status="completed",
                    evidence=[
                        Evidence(
                            id="E1", resource="veriqta-demo/pods/*", data="large evidence" * 1000
                        )
                    ],
                )
            )
        page = client.get("/api/investigations").json()
        assert len(page) == 30 and all("evidence" not in r and "problem" not in r for r in page)
        older = client.get("/api/investigations?offset=30&limit=30").json()
        assert len(older) == 5 and not {r["id"] for r in page} & {r["id"] for r in older}
        assert client.get("/api/investigations?limit=101").status_code == 422
        assert client.get("/api/investigations?offset=-1").status_code == 422
        assert client.get("/api/investigations?offset=" + str(2**100)).status_code == 422
        assert client.get("/api/investigations/" + page[0]["id"]).json()["evidence"]


def test_log_time_window_is_bounded_and_passed_to_sdk(tmp_path):
    from types import SimpleNamespace as Obj
    from kubeinvestigator.collector import Collector
    from kubeinvestigator.schemas import ToolArgs

    settings = Settings(
        token=secrets.token_urlsafe(32),
        database=str(tmp_path / "records.db"),
        logs=True,
        log_lookback_seconds=120,
    )
    collector = Collector(settings)
    calls = []

    def unused(*args, **kwargs):
        pass

    def logs(*args, **kwargs):
        calls.append(kwargs)
        return "safe log"

    collector.core = Obj(
        list_namespaced_pod=unused,
        list_namespaced_event=unused,
        list_namespaced_service=unused,
        read_namespaced_pod_log=logs,
    )
    collector.apps = Obj(list_namespaced_deployment=unused, list_namespaced_replica_set=unused)
    collector.discovery = Obj(list_namespaced_endpoint_slice=unused)
    collector.live(
        ToolArgs(
            namespace="veriqta-demo", resource="logs", name="pod", container="app", previous=True
        )
    )
    assert (
        calls[0]["since_seconds"] == 120
        and calls[0]["tail_lines"] == 40
        and calls[0]["limit_bytes"] == 4096
        and calls[0]["previous"]
    )
