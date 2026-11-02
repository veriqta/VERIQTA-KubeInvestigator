"""Bounded real-Kubernetes/mock-provider load measurement; disposable wrapper only."""

import asyncio
import json
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx

from smoke import CONTEXT, forward, kubectl


def resource_sample():
    node = json.loads(kubectl("get", "nodes", "-o", "json"))["items"][0]["metadata"]["name"]
    summary = json.loads(kubectl("get", "--raw", "/api/v1/nodes/" + node + "/proxy/stats/summary"))
    containers = [
        c
        for pod in summary["pods"]
        if pod["podRef"]["namespace"] == "veriqta-system"
        for c in pod.get("containers", [])
        if c["name"] == "investigator"
    ]
    assert len(containers) == 1
    c = containers[0]
    return {
        "time": c["cpu"]["time"],
        "cpu_nanocores": c["cpu"].get("usageNanoCores"),
        "cpu_core_nanoseconds": c["cpu"]["usageCoreNanoSeconds"],
        "working_set_bytes": c["memory"]["workingSetBytes"],
        "rss_bytes": c["memory"].get("rssBytes"),
    }


async def measure(token):
    samples = []
    metrics = []
    phases = []
    stop = asyncio.Event()
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:18080",
        headers={"Authorization": "Bearer " + token},
        timeout=30,
        limits=httpx.Limits(max_connections=32),
    ) as c:
        config = (await c.get("/api/config")).raise_for_status().json()
        assert config["mock"] and config["source"] == "kubernetes"

        async def monitor():
            while not stop.is_set():
                samples.append(await asyncio.to_thread(resource_sample))
                text = (await c.get("/metrics")).raise_for_status().text
                metrics.append(
                    {
                        key: float(value)
                        for key, value in (
                            line.split()
                            for line in text.splitlines()
                            if line and not line.startswith("#")
                        )
                    }
                )
                try:
                    await asyncio.wait_for(stop.wait(), timeout=1)
                except TimeoutError:
                    pass

        monitor_task = asyncio.create_task(monitor())
        try:
            for concurrency, count in [(1, 8), (2, 8), (4, 8), (32, 32)]:
                gate = asyncio.Semaphore(concurrency)

                async def submit(index):
                    async with gate:
                        started = time.monotonic()
                        response = await c.post(
                            "/api/investigations",
                            json={
                                "namespace": "veriqta-demo",
                                "workload": "frontend",
                                "scenario": "service",
                                "problem": "Bounded load: inspect Service selector evidence.",
                            },
                        )
                        assert response.status_code in {202, 429}, response.status_code
                        return {
                            "status": response.status_code,
                            "submit_seconds": round(time.monotonic() - started, 4),
                            "id": response.json()["id"] if response.status_code == 202 else None,
                            "started": started,
                        }

                rows = await asyncio.gather(*(submit(i) for i in range(count)))
                pending = {r["id"]: r for r in rows if r["id"]}
                queued = 0
                deadline = time.monotonic() + 120
                while pending:
                    reports = (
                        (await c.get("/api/investigations?limit=100")).raise_for_status().json()
                    )
                    queued = max(queued, sum(r["status"] == "queued" for r in reports))
                    for report in reports:
                        if report["id"] in pending and report["status"] not in {
                            "queued",
                            "running",
                        }:
                            row = pending.pop(report["id"])
                            row["terminal_status"] = report["status"]
                            row["observed_completion_seconds"] = round(
                                time.monotonic() - row["started"], 4
                            )
                    assert time.monotonic() < deadline, (
                        "Queue did not drain within bounded deadline"
                    )
                    if pending:
                        await asyncio.sleep(0.25)
                phases.append(
                    {
                        "client_concurrency": concurrency,
                        "requests": count,
                        "response_counts": dict(Counter(r["status"] for r in rows)),
                        "max_queued_sample": queued,
                        "submission_latency_seconds": [r["submit_seconds"] for r in rows],
                        "completion_latency_seconds": [
                            r["observed_completion_seconds"] for r in rows if r["id"]
                        ],
                        "terminal_counts": dict(
                            Counter(r["terminal_status"] for r in rows if r["id"])
                        ),
                    }
                )
                assert all(r.get("terminal_status", "completed") == "completed" for r in rows)
                await asyncio.sleep(2)
        finally:
            stop.set()
            await monitor_task
        # Exercise rate rejection only after completing all report measurements.
        flood = []
        for _ in range(185):
            response = await c.get("/health/ready")
            flood.append(response.status_code)
            if response.status_code == 429:
                break
        assert 429 in flood, "Expected documented per-client rate rejection"
        recovered = False
        deadline = time.monotonic() + 65
        while time.monotonic() < deadline:
            await asyncio.sleep(2)
            response = await c.get("/health/ready")
            if response.status_code == 200:
                recovered = True
                break
        assert recovered, "Rate limit failed to recover after its window"
    assert samples and all(s["working_set_bytes"] > 0 for s in samples)
    return {
        "configuration": config,
        "phases": phases,
        "resource_samples": samples,
        "metrics_samples": metrics,
        "rate_limit": {
            "rejected": True,
            "recovered": recovered,
            "requests_until_rejection": len(flood),
        },
        "measurement_limits": [
            "Short synthetic sample workload; not sustained production or live-provider load.",
            "Kubelet resource samples can miss brief peaks; client timings include localhost port-forward and polling delay.",
            "Installer reads kubelet statistics; application service account retains no node access.",
        ],
    }


def main():
    assert Path(".data/smoke-owned").exists()
    assert kubectl("config", "current-context") == CONTEXT
    token = Path(".data/demo-access.env").read_text().strip().removeprefix("KI_TOKEN=")
    pf = forward()
    try:
        result = asyncio.run(measure(token))
    finally:
        pf.terminate()
        pf.wait(timeout=10)
    result.update(
        status="checks_passed_cleanup_pending",
        cluster_cleanup_verified=None,
        completed_at=datetime.now(UTC).isoformat(),
        revision=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        source="kubernetes",
        provider="mock",
        kubernetes=json.loads(kubectl("version", "-o", "json"))["serverVersion"]["gitVersion"],
        image_id=subprocess.check_output(
            ["docker", "image", "inspect", "kubeinvestigator:0.1.0", "--format", "{{.Id}}"],
            text=True,
        ).strip(),
    )
    Path(".data/load-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        "Bounded load passed; measurements are profile-specific, not HA or live-provider capacity."
    )


if __name__ == "__main__":
    main()
