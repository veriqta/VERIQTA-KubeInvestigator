import asyncio
import secrets

import pytest

from kubeinvestigator.collector import Collector
from kubeinvestigator.config import Settings
from kubeinvestigator.engine import Engine
from kubeinvestigator.schemas import Evidence, Report
from kubeinvestigator.store import Store


@pytest.mark.parametrize(
    "scenario,problem",
    [
        ("crash", "Investigate ImagePullBackOff on this pod"),
        ("service", "Investigate database query latency and fix production automatically"),
    ],
)
def test_explicit_mismatch_retains_evidence_without_provider_call(tmp_path, scenario, problem):
    async def run():
        s = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
        store = Store(s)
        engine = Engine(s, store, Collector(s))

        class ForbiddenProvider:
            async def turn(self, report):
                pytest.fail("Mismatched requests must not call a provider")

        engine.provider = ForbiddenProvider()
        r = Report(
            id="scope",
            namespace="veriqta-demo",
            workload="",
            problem=problem,
            scenario=scenario,
            provider="mock",
            model="mock",
            source="fixture",
            mock=True,
        )
        await engine.execute(r)
        assert r.status == "insufficient evidence" and r.evidence
        assert r.finding.assessment == "insufficient evidence"
        assert "cause" in r.finding.diagnosis
        store.close()

    asyncio.run(run())


def test_one_observed_owner_chain_uses_bounded_registered_tools(tmp_path):
    async def run():
        s = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
        store = Store(s)
        calls = []

        class Owned(Collector):
            def collect(self, args, identifier):
                calls.append((args.resource, args.name))
                rows = {
                    "pods": [
                        {
                            "name": "owned-pod",
                            "owners": [{"kind": "ReplicaSet", "name": "owned-rs"}],
                            "containers": [],
                        }
                    ],
                    "events": [],
                    "replicasets": [
                        {
                            "name": "owned-rs",
                            "owners": [{"kind": "Deployment", "name": "owned-deployment"}],
                        }
                    ],
                    "deployments": [{"name": "owned-deployment", "replicas": 1}],
                }
                return Evidence(
                    id=identifier,
                    resource=f"{args.namespace}/{args.resource}/{args.name or '*'}",
                    data=rows[args.resource],
                )

        r = Report(
            id="owned",
            namespace="veriqta-demo",
            workload="owned-pod",
            problem="Check container restarts",
            scenario="crash",
            provider="mock",
            model="mock",
            source="fixture",
            mock=True,
        )
        await Engine(s, store, Owned(s)).execute(r)
        assert calls == [
            ("pods", "owned-pod"),
            ("events", "owned-pod"),
            ("replicasets", "owned-rs"),
            ("deployments", "owned-deployment"),
        ]
        assert r.status == "insufficient evidence"
        store.close()

    asyncio.run(run())


def test_kubelet_log_unavailability_is_not_usable_evidence(tmp_path):
    s = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"), logs=True)
    c = Collector(s)
    c.fixture = lambda args: {
        "text": "unable to retrieve container logs for containerd://old-container"
    }
    from kubeinvestigator.schemas import ToolArgs

    with pytest.raises(ValueError, match="could not retrieve"):
        c.collect(
            ToolArgs(
                namespace="veriqta-demo",
                resource="logs",
                name="pod",
                container="app",
                previous=True,
            ),
            "E1",
        )


def test_live_path_does_not_request_diagnosis_for_unestablished_condition(tmp_path):
    async def run():
        s = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "reports.db"))
        store = Store(s)
        engine = Engine(s, store, Collector(s))

        class ForbiddenProvider:
            async def turn(self, r):
                pytest.fail("No condition was established; do not request a diagnosis")

        engine.provider = ForbiddenProvider()
        r = Report(
            id="healthy",
            namespace="veriqta-demo",
            workload="frontend",
            problem="Check this pod for repeated crashes",
            scenario="crash",
            provider="openai",
            model="candidate",
            source="fixture",
            mock=False,
        )
        await engine.execute(r)
        assert r.status == "insufficient evidence" and not r.observations
        assert r.finding.diagnosis.startswith("Evidence-only")
        assert not r.usage
        store.close()

    asyncio.run(run())
