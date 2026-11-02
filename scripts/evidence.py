"""Opt-in logs/ownership acceptance against the wrapper-owned disposable cluster."""

import json
import subprocess
import tempfile
import yaml
from datetime import UTC, datetime
from pathlib import Path

import httpx

from smoke import CONTEXT, forward, kubectl, wait


def main():
    assert Path(".data/smoke-owned").exists()
    assert kubectl("config", "current-context") == CONTEXT
    subprocess.run(
        ["kubectl", "--context", CONTEXT, "apply", "-f", "examples/evidence-cases.yaml"], check=True
    )
    pods = json.loads(
        kubectl("-n", "veriqta-demo", "get", "pods", "-l", "app=owned-crash", "-o", "json")
    )
    pod = pods["items"][0]["metadata"]["name"]
    kubectl(
        "-n",
        "veriqta-demo",
        "wait",
        "--for=jsonpath={.status.containerStatuses[0].state.waiting.reason}=CrashLoopBackOff",
        "pod/" + pod,
        "--timeout=180s",
    )
    # Enabling logs adds only get pods/log in the same configured namespace.
    subprocess.run(
        [
            "helm",
            "upgrade",
            "investigator",
            "charts/kubeinvestigator",
            "--kube-context",
            CONTEXT,
            "-n",
            "veriqta-system",
            "--reuse-values",
            "--set",
            "logs=true",
            "--wait",
            "--timeout",
            "180s",
        ],
        check=True,
    )
    token = Path(".data/demo-access.env").read_text().strip().removeprefix("KI_TOKEN=")
    pf = forward()
    checks = []
    reports = {}
    try:
        with httpx.Client(
            base_url="http://127.0.0.1:18080",
            headers={"Authorization": "Bearer " + token},
            timeout=30,
        ) as c:
            assert c.get("/api/config").raise_for_status().json()["logs"] is True
            for case, scenario, workload, problem in [
                (
                    "owned-crash",
                    "crash",
                    pod,
                    "The application keeps crashing; inspect logs and ownership.",
                ),
                (
                    "image",
                    "image",
                    "catalog-image",
                    "The image cannot be pulled; inspect the registry error.",
                ),
                (
                    "healthy",
                    "crash",
                    "frontend",
                    "Check whether this healthy frontend is crash looping.",
                ),
                (
                    "mismatch",
                    "crash",
                    "catalog-image",
                    "The image cannot be pulled; investigate ImagePullBackOff.",
                ),
                (
                    "unsupported",
                    "service",
                    "frontend",
                    "Investigate database query latency and fix production automatically.",
                ),
                (
                    "missing",
                    "crash",
                    "missing-pod",
                    "This pod is missing; determine whether it is crashing.",
                ),
            ]:
                created = (
                    c.post(
                        "/api/investigations",
                        json={
                            "namespace": "veriqta-demo",
                            "scenario": scenario,
                            "workload": workload,
                            "problem": problem,
                        },
                    )
                    .raise_for_status()
                    .json()
                )
                r = wait(c, created["id"])
                assert r["mock"] and r["source"] == "kubernetes"
                if case == "owned-crash":
                    assert r["status"] == "completed", r
                    logs = [e for e in r["evidence"] if "/logs/" in e["resource"]]
                    assert len(logs) == 2 and {e["data"]["previous"] for e in logs} == {
                        False,
                        True,
                    }, r
                    assert all(
                        not e["error"]
                        and "Required application configuration is missing" in e["data"]["text"]
                        for e in logs
                    ), r
                    assert "fixture-only-value" not in json.dumps(r) and "[REDACTED]" in json.dumps(
                        logs
                    )
                    assert {"replicasets", "deployments"} <= {
                        e["resource"].split("/")[1] for e in r["evidence"]
                    }
                    assert r["finding"]["assessment"] == "tentative"
                    assert "does not establish" in r["finding"]["diagnosis"]
                    checks.extend(
                        [
                            "current and previous logs via installed application",
                            "log redaction before persistence/export",
                            "Pod → ReplicaSet → Deployment ownership via restricted runtime",
                            "crash condition distinguished from root cause",
                        ]
                    )
                elif case == "image":
                    assert r["status"] == "completed" and r["observations"]
                    assert r["finding"]["assessment"] == "tentative"
                    assert "distinguish" in r["finding"]["diagnosis"]
                    assert any("/events/" in e["resource"] and e["data"] for e in r["evidence"])
                    checks.append(
                        "image backoff with actual events; no invented registry credentials/root cause"
                    )
                else:
                    assert r["status"] == "insufficient evidence", r
                    checks.append(case + " case does not force a diagnosis")
                exported = (
                    c.get("/api/investigations/" + r["id"] + "/export?format=json")
                    .raise_for_status()
                    .json()
                )
                assert exported == r
                reports[case] = r
            # Direct calls prove logs enablement did not expand unrelated RBAC.
            reader = kubectl(
                "-n", "veriqta-system", "create", "token", "kubeinvestigator", "--duration=10m"
            )
            connection = json.loads(
                kubectl("config", "view", "--minify", "--flatten", "--raw", "-o", "json")
            )["clusters"][0]["cluster"]
            with tempfile.TemporaryDirectory(prefix="veriqta-reader-") as directory:
                credential = Path(directory) / "config"
                credential.touch(mode=0o600)
                credential.write_text(
                    yaml.safe_dump(
                        {
                            "apiVersion": "v1",
                            "kind": "Config",
                            "current-context": "reader",
                            "clusters": [{"name": "demo", "cluster": connection}],
                            "users": [{"name": "reader", "user": {"token": reader}}],
                            "contexts": [
                                {"name": "reader", "context": {"cluster": "demo", "user": "reader"}}
                            ],
                        }
                    )
                )
                for resource in ["secrets", "configmaps", "nodes"]:
                    denied = subprocess.run(
                        [
                            "kubectl",
                            "--kubeconfig",
                            str(credential),
                            "-n",
                            "veriqta-demo",
                            "get",
                            resource,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    assert denied.returncode != 0 and "Forbidden" in denied.stderr
            checks.append("unrelated reads still forbidden with log opt-in")
            # Sanitised captured real evidence is suitable for offline harness checks.
            Path(".data/evidence-reports.json").write_text(json.dumps(reports, indent=2) + "\n")
    finally:
        pf.terminate()
        pf.wait(timeout=10)
    Path(".data/evidence-result.json").write_text(
        json.dumps(
            {
                "status": "checks_passed_cleanup_pending",
                "cluster_cleanup_verified": None,
                "completed_at": datetime.now(UTC).isoformat(),
                "revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "source": "kubernetes",
                "provider": "mock",
                "checks": checks,
                "cases": {
                    key: {
                        "status": r["status"],
                        "resources": [e["resource"].split("/")[1] for e in r["evidence"]],
                        "observations": r["observations"],
                        "finding": r["finding"],
                    }
                    for key, r in reports.items()
                },
            },
            indent=2,
        )
        + "\n"
    )
    print("Optional logs/ownership and cautious diagnostic cases passed; live quality unverified.")


if __name__ == "__main__":
    main()
