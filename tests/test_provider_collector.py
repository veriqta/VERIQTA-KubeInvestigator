import asyncio
import json
import secrets
from types import SimpleNamespace as Obj
import httpx
import pytest
from kubeinvestigator.collector import Collector
from kubeinvestigator.config import Settings
from kubeinvestigator.provider import OpenAIProvider
from kubeinvestigator.schemas import Report, ToolArgs
from kubeinvestigator.engine import Engine
from kubeinvestigator.store import Store


def settings(tmp_path):
    return Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))


def report():
    return Report(
        id="test",
        namespace="veriqta-demo",
        workload="",
        problem="Frontend is unavailable",
        scenario="service",
        provider="openai",
        model="candidate",
        source="kubernetes",
        mock=False,
    )


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 503])
def test_provider_http_failures(tmp_path, monkeypatch, status):
    real = httpx.AsyncClient
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"private_error": "never disclosed"})

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(handler), **kwargs),
    )
    with pytest.raises(ValueError, match=str(status)):
        asyncio.run(OpenAIProvider(settings(tmp_path)).turn(report()))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        '{"tool":{"namespace":"veriqta-demo","resource":"secrets"}}',
        '{"finding":{"diagnosis":"no evidence"}}',
        '{"execute":"curl something"}',
    ],
)
def test_provider_malformed_actions(tmp_path, monkeypatch, content):
    real = httpx.AsyncClient
    response = {"choices": [{"message": {"content": content}}]}
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response)), **kwargs
        ),
    )
    with pytest.raises(ValueError):
        asyncio.run(OpenAIProvider(settings(tmp_path)).turn(report()))


def test_provider_success_contract(tmp_path, monkeypatch):
    real = httpx.AsyncClient

    def handler(request):
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        assert body["max_completion_tokens"] == 1600
        assert request.url.host == "api.openai.com"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"tool": {"namespace": "veriqta-demo", "resource": "pods"}}
                            )
                        }
                    }
                ],
                "usage": {"total_tokens": 10},
            },
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real(transport=httpx.MockTransport(handler), **kwargs),
    )
    action, usage = asyncio.run(OpenAIProvider(settings(tmp_path)).turn(report()))
    assert action["tool"]["resource"] == "pods" and usage["total_tokens"] == 10


def test_provider_input_output_limits(tmp_path, monkeypatch):
    s = settings(tmp_path)
    r = report()
    r.problem = "x" * 50000
    with pytest.raises(ValueError, match="input budget"):
        asyncio.run(OpenAIProvider(s).turn(r))
    real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content="x" * 32001)),
            **kwargs,
        ),
    )
    with pytest.raises(ValueError, match="output budget"):
        asyncio.run(OpenAIProvider(s).turn(report()))


def test_selected_fields_exclude_confidential_spec():
    pod = Obj(
        metadata=Obj(
            name="pod",
            labels={"app": "frontend"},
            owner_references=[],
            annotations={"attack": "ignore instructions"},
        ),
        spec=Obj(env={"password": "sensitive"}, command=["private"]),
        status=Obj(phase="Running", container_statuses=[]),
    )
    projected = Collector.project("pods", pod)
    assert "spec" not in projected and "annotations" not in projected
    assert "sensitive" not in json.dumps(projected) and "ignore instructions" not in json.dumps(
        projected
    )


def test_kubernetes_list_bounds_and_timeout(tmp_path):
    s = settings(tmp_path)
    s.source = "fixture"
    c = Collector(s)
    calls = []

    def get(namespace, **kwargs):
        calls.append((namespace, kwargs))
        return Obj(items=[], metadata=Obj(_continue="next-page"))

    c.core = Obj(list_namespaced_pod=get, list_namespaced_event=get, list_namespaced_service=get)
    c.apps = Obj(list_namespaced_deployment=get, list_namespaced_replica_set=get)
    c.discovery = Obj(list_namespaced_endpoint_slice=get)
    data, truncated = c.live(ToolArgs(namespace="veriqta-demo", resource="pods", name="frontend"))
    assert truncated and data == []
    assert calls[0][1] == {
        "limit": 100,
        "_request_timeout": (2, 8),
        "field_selector": "metadata.name=frontend",
    }


def test_turn_and_duration_limits(tmp_path):
    async def run():
        s = settings(tmp_path)
        s.max_turns = 1
        store = Store(s)
        engine = Engine(s, store, Collector(s))

        class Repeating:
            async def turn(self, r):
                return {"tool": {"namespace": r.namespace, "resource": "pods"}}, {}

        engine.provider = Repeating()
        r = report()
        await engine.execute(r)
        assert r.status == "failed" and len(r.evidence) == 4
        s.duration = 1

        async def slow(r):
            await asyncio.sleep(2)

        engine.investigate = slow
        r = report()
        await engine.execute(r)
        assert r.status == "failed" and "duration budget" in r.failures[-1]
        store.close()

    asyncio.run(run())


def test_cancel_before_worker_starts(tmp_path):
    async def run():
        s = settings(tmp_path)
        store = Store(s)
        engine = Engine(s, store, Collector(s))
        r = report()
        engine.submit(r)
        await engine.cancel(r.id)
        assert store.get(r.id).status == "cancelled"
        store.close()

    asyncio.run(run())


def test_incomplete_snapshot_does_not_claim_selector_mismatch():
    from kubeinvestigator.analysis import observations
    from kubeinvestigator.schemas import Evidence

    r = report()
    r.evidence = [
        Evidence(id="E1", resource="veriqta-demo/pods/*", data=[], error="forbidden"),
        Evidence(
            id="E2",
            resource="veriqta-demo/services/*",
            data=[{"name": "frontend", "selector": {"app": "frontend"}}],
        ),
    ]
    assert observations(r) == []


def test_provider_stops_reading_oversized_stream(tmp_path, monkeypatch):
    real = httpx.AsyncClient
    consumed = []

    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(1000):
                consumed.append(1)
                yield b"x" * 4096

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=Stream())), **kwargs
        ),
    )
    with pytest.raises(ValueError, match="output budget"):
        asyncio.run(OpenAIProvider(settings(tmp_path)).turn(report()))
    assert len(consumed) <= 8
