"""Run only after scripts/demo.sh setup; uses the dedicated, restricted installation."""

import json
import traceback
from unittest.mock import patch
from datetime import datetime, timezone
import tempfile
import yaml
from kubeinvestigator.schemas import Report, ToolArgs
from kubeinvestigator.collector import Collector
from kubeinvestigator.config import Settings
import subprocess
import time
from pathlib import Path

import httpx

CONTEXT = "kind-veriqta-investigator-demo"


def kubectl(*args):
    return subprocess.check_output(["kubectl", "--context", CONTEXT, *args], text=True).strip()


def forward():
    process = subprocess.Popen(
        [
            "kubectl",
            "--context",
            CONTEXT,
            "-n",
            "veriqta-system",
            "port-forward",
            "--address",
            "127.0.0.1",
            "svc/investigator",
            "18080:8080",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            if httpx.get("http://127.0.0.1:18080/health/ready").status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    process.terminate()
    raise RuntimeError("Port-forward did not become ready")


def wait(client, identifier):
    for _ in range(100):
        response = client.get("/api/investigations/" + identifier)
        response.raise_for_status()
        report = response.json()
        if report["status"] not in {"queued", "running"}:
            return report
        time.sleep(0.5)
    raise RuntimeError("Investigation deadline exceeded")


def main():
    assert kubectl("config", "current-context") == CONTEXT
    token = Path(".data/demo-access.env").read_text().strip().removeprefix("KI_TOKEN=")
    # Generate restricted credentials from the installed application's ServiceAccount.
    # Retain only cluster connection information, never the installer identity.
    cluster = json.loads(kubectl("config", "view", "--minify", "--flatten", "--raw", "-o", "json"))[
        "clusters"
    ][0]["cluster"]
    restricted_token = kubectl(
        "-n", "veriqta-system", "create", "token", "kubeinvestigator", "--duration=10m"
    )
    with tempfile.TemporaryDirectory(prefix="veriqta-rbac-") as directory:
        credentials = Path(directory) / "config"
        credentials.touch(mode=0o600)
        credentials.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "v1",
                    "kind": "Config",
                    "current-context": "restricted",
                    "clusters": [{"name": "demo", "cluster": cluster}],
                    "users": [{"name": "reader", "user": {"token": restricted_token}}],
                    "contexts": [
                        {
                            "name": "restricted",
                            "context": {
                                "cluster": "demo",
                                "user": "reader",
                                "namespace": "veriqta-demo",
                            },
                        }
                    ],
                }
            )
        )

        def restricted(*args):
            return subprocess.run(
                ["kubectl", "--kubeconfig", str(credentials), *args],
                capture_output=True,
                text=True,
                timeout=30,
            )

        allowed = restricted("get", "pods", "-n", "veriqta-demo", "-o", "name")
        assert allowed.returncode == 0 and "frontend" in allowed.stdout, (
            "Restricted pod read failed"
        )
        for resource, namespace in [
            ("secrets", "veriqta-demo"),
            ("configmaps", "veriqta-demo"),
            ("pods", "kube-system"),
            ("nodes", "veriqta-demo"),
        ]:
            result = restricted("get", resource, "-n", namespace)
            assert result.returncode != 0 and "Forbidden" in result.stderr, (
                f"Expected actual forbidden read: {resource}"
            )
        for operation, resource in [
            ("create", "pods"),
            ("patch", "pods"),
            ("delete", "pods"),
            ("create", "pods/exec"),
            ("create", "pods/portforward"),
            ("get", "pods/log"),
            ("create", "pods/attach"),
            ("get", "pods/proxy"),
            ("get", "services/proxy"),
            ("patch", "deployments.apps"),
            ("create", "roles.rbac.authorization.k8s.io"),
            ("create", "rolebindings.rbac.authorization.k8s.io"),
            ("impersonate", "users"),
            ("list", "namespaces"),
            ("get", "customresourcedefinitions.apiextensions.k8s.io"),
        ]:
            base, _, subresource = resource.partition("/")
            args = ["auth", "can-i", operation, base, "-n", "veriqta-demo"]
            if subresource:
                args += ["--subresource", subresource]
            result = restricted(*args)
            assert result.stdout.strip() == "no", f"Unexpected permission: {operation} {resource}"
        from kubernetes import config

        original_load = config.load_kube_config
        with (
            patch("kubernetes.config.load_incluster_config", side_effect=config.ConfigException),
            patch(
                "kubernetes.config.load_kube_config",
                side_effect=lambda: original_load(config_file=str(credentials)),
            ),
        ):
            collector = Collector(
                Settings(token=token, source="kubernetes", database=".data/smoke-local-check.db")
            )
            for resource in [
                "pods",
                "events",
                "services",
                "endpointslices",
                "deployments",
                "replicasets",
            ]:
                try:
                    collector.collect(
                        ToolArgs(namespace="veriqta-demo", resource=resource),
                        "restricted-sdk-check",
                    )
                except Exception as exc:
                    frames = [
                        {
                            "file": Path(frame.filename).name,
                            "line": frame.lineno,
                            "function": frame.name,
                        }
                        for frame in traceback.extract_tb(exc.__traceback__)
                    ]
                    Path(".capture").mkdir(exist_ok=True)
                    Path(".capture/smoke-sdk-error.json").write_text(
                        json.dumps(
                            {
                                "resource": resource,
                                "exception_type": type(exc).__name__,
                                "frames": frames,
                            },
                            indent=2,
                        )
                    )
                    raise RuntimeError(
                        f"Restricted SDK collection failed for {resource}; inspect credential-free .capture/smoke-sdk-error.json"
                    ) from None
        denied_logs = restricted("logs", "frontend", "-n", "veriqta-demo", "--tail=1")
        assert denied_logs.returncode != 0 and "Forbidden" in denied_logs.stderr, (
            "Expected actual forbidden pod log read"
        )
    pf = forward()
    try:
        with httpx.Client(
            base_url="http://127.0.0.1:18080",
            headers={"Authorization": "Bearer " + token},
            timeout=30,
        ) as client:
            assert (
                client.get("/api/config", headers={"Authorization": "Bearer invalid"}).status_code
                == 401
            )
            configuration = client.get("/api/config").raise_for_status().json()
            assert configuration["source"] == "kubernetes" and configuration["mock"]
            checks = client.post("/api/diagnostics").raise_for_status().json()
            assert all(check["ok"] for check in checks["checks"]), checks
            identifiers = []
            originals = {}
            workloads = {"crash": "checkout-crash", "image": "catalog-image", "service": "frontend"}
            for scenario in ["crash", "image", "service"]:
                if scenario == "crash":
                    kubectl(
                        "-n",
                        "veriqta-demo",
                        "wait",
                        "--for=jsonpath={.status.containerStatuses[0].state.waiting.reason}=CrashLoopBackOff",
                        "pod/checkout-crash",
                        "--timeout=120s",
                    )
                response = client.post(
                    "/api/investigations",
                    json={
                        "namespace": "veriqta-demo",
                        "workload": workloads[scenario],
                        "problem": "Sample workload is unavailable",
                        "scenario": scenario,
                    },
                )
                response.raise_for_status()
                report = wait(client, response.json()["id"])
                assert (
                    report["status"] == "completed"
                    and report["source"] == "kubernetes"
                    and report["mock"]
                ), report
                Report.model_validate(report)
                assert report["observations"] and report["evidence"]
                assert not any(e["error"] or e["truncated"] for e in report["evidence"])
                required = (
                    {"pods", "events"}
                    if scenario != "service"
                    else {"pods", "services", "endpointslices"}
                )
                assert required <= {e["resource"].split("/")[1] for e in report["evidence"]}
                assert set(report["finding"]["evidence_ids"]) <= {
                    e["id"] for e in report["evidence"]
                }
                for fmt in ["json", "md"]:
                    exported = client.get(f"/api/investigations/{report['id']}/export?format={fmt}")
                    assert exported.status_code == 200 and "mock" in exported.text.lower()
                originals[report["id"]] = report
                identifiers.append(report["id"])
            assert (
                client.post(
                    "/api/investigations",
                    json={
                        "namespace": "kube-system",
                        "problem": "Unauthorised request",
                        "scenario": "crash",
                    },
                ).status_code
                == 403
            )
            pf.terminate()
            pf.wait(timeout=10)
            kubectl("-n", "veriqta-system", "rollout", "restart", "deployment/investigator")
            kubectl(
                "-n",
                "veriqta-system",
                "rollout",
                "status",
                "deployment/investigator",
                "--timeout=180s",
            )
            pf = forward()
            for identifier in identifiers:
                retained = client.get("/api/investigations/" + identifier).raise_for_status().json()
                assert retained == originals[identifier], (
                    "Report changed or evidence was lost across restart"
                )
            verifications = {}
            for scenario, identifier in zip(["crash", "image", "service"], identifiers):
                subprocess.run(
                    ["bash", "scripts/demo.sh", "correct-" + scenario], check=True, timeout=240
                )
                child = (
                    client.post("/api/investigations/" + identifier + "/followup")
                    .raise_for_status()
                    .json()
                )
                report = wait(client, child["id"])
                Report.model_validate(report)
                assert report["parent_id"] == identifier
                assert "absent in fresh evidence" in (report["verification"] or ""), report
                assert not report["observations"]
                assert all(
                    e["collected_at"] > originals[identifier]["completed_at"]
                    for e in report["evidence"]
                )
                parent = client.get("/api/investigations/" + identifier).raise_for_status().json()
                assert report["id"] in parent["followup_ids"]
                verifications[scenario] = report["verification"]
                assert client.delete("/api/investigations/" + child["id"]).status_code == 200
                assert client.get("/api/investigations/" + child["id"]).status_code == 404
            Path(".data/smoke-result.json").write_text(
                json.dumps(
                    {
                        "software": "0.1.0",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "status": "checks_passed_cleanup_pending",
                        "cluster_cleanup_verified": None,
                        "versions": {
                            "kubernetes": kubectl("version", "-o", "json"),
                            "kind": subprocess.check_output(["kind", "version"], text=True).strip(),
                            "helm": subprocess.check_output(
                                ["helm", "version", "--short"], text=True
                            ).strip(),
                            "image_id": subprocess.check_output(
                                [
                                    "docker",
                                    "image",
                                    "inspect",
                                    "kubeinvestigator:0.1.0",
                                    "--format",
                                    "{{.Id}}",
                                ],
                                text=True,
                            ).strip(),
                            "image_architecture": subprocess.check_output(
                                [
                                    "docker",
                                    "image",
                                    "inspect",
                                    "kubeinvestigator:0.1.0",
                                    "--format",
                                    "{{.Architecture}}",
                                ],
                                text=True,
                            ).strip(),
                            "docker_server": subprocess.check_output(
                                ["docker", "version", "--format", "{{.Server.Version}}"], text=True
                            ).strip(),
                        },
                        "source": "kubernetes",
                        "provider": "mock",
                        "mock": True,
                        "observation_counts": {
                            r["scenario"]: len(r["observations"]) for r in originals.values()
                        },
                        "reports": identifiers,
                        "verifications": verifications,
                        "checks": [
                            "Helm installation via demo setup",
                            "restricted credential API reads/denials",
                            "three incidents and exports",
                            "unchanged reports across restart",
                            "three external corrections and fresh follow-ups",
                            "deletion",
                        ],
                    },
                    indent=2,
                )
            )
    finally:
        pf.terminate()
        pf.wait(timeout=10)
    print("Cluster smoke passed; mock interpretations do not measure model quality.")


if __name__ == "__main__":
    main()
