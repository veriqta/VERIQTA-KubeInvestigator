"""Focused storage/config-upgrade/Helm-rollback acceptance in the owned kind cluster."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import httpx
from smoke import CONTEXT, forward, kubectl, wait


def maintenance(operation, filename=None):
    name = "storage-" + operation
    command = [
        "python",
        "-m",
        "kubeinvestigator.maintenance",
        operation,
        "--database",
        "/data/investigations.db",
    ]
    if filename:
        command += ["--file", filename]
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": name, "namespace": "veriqta-system"},
        "spec": {
            "backoffLimit": 0,
            "activeDeadlineSeconds": 90,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "automountServiceAccountToken": False,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 10001,
                        "runAsGroup": 10001,
                        "fsGroup": 10001,
                    },
                    "containers": [
                        {
                            "name": "maintenance",
                            "image": "kubeinvestigator:0.1.0",
                            "imagePullPolicy": "IfNotPresent",
                            "command": command,
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                                "capabilities": {"drop": ["ALL"]},
                                "seccompProfile": {"type": "RuntimeDefault"},
                            },
                            "volumeMounts": [{"name": "data", "mountPath": "/data"}],
                        }
                    ],
                    "volumes": [
                        {
                            "name": "data",
                            "persistentVolumeClaim": {"claimName": "investigator-data"},
                        }
                    ],
                }
            },
        },
    }
    subprocess.run(
        ["kubectl", "--context", CONTEXT, "apply", "-f", "-"],
        input=json.dumps(job),
        text=True,
        check=True,
    )
    kubectl(
        "-n", "veriqta-system", "wait", "--for=condition=complete", "job/" + name, "--timeout=100s"
    )
    kubectl("-n", "veriqta-system", "delete", "job", name, "--wait=true")


def stop_app():
    kubectl("-n", "veriqta-system", "scale", "deployment/investigator", "--replicas=0")
    kubectl(
        "-n",
        "veriqta-system",
        "wait",
        "--for=delete",
        "pod",
        "-l",
        "app.kubernetes.io/instance=investigator",
        "--timeout=120s",
    )


def start_app():
    kubectl("-n", "veriqta-system", "scale", "deployment/investigator", "--replicas=1")
    kubectl(
        "-n", "veriqta-system", "rollout", "status", "deployment/investigator", "--timeout=120s"
    )


def main():
    token = Path(".data/demo-access.env").read_text().strip().removeprefix("KI_TOKEN=")
    pf = forward()
    try:
        with httpx.Client(
            base_url="http://127.0.0.1:18080",
            headers={"Authorization": "Bearer " + token},
            timeout=30,
        ) as c:
            created = (
                c.post(
                    "/api/investigations",
                    json={
                        "namespace": "veriqta-demo",
                        "workload": "frontend",
                        "scenario": "service",
                        "problem": "Check sample selector before recovery",
                    },
                )
                .raise_for_status()
                .json()
            )
            original = wait(c, created["id"])
            assert (
                original["status"] == "completed"
                and original["source"] == "kubernetes"
                and original["mock"]
            )
            pf.terminate()
            pf.wait(timeout=10)
            # Same schema/configuration upgrade exercise; not a fabricated older binary.
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
                    "-f",
                    "examples/values.yaml",
                    "--set",
                    "retentionDays=8",
                    "--wait",
                    "--timeout",
                    "180s",
                ],
                check=True,
            )
            pf = forward()
            assert (
                c.get("/api/investigations/" + original["id"]).raise_for_status().json() == original
            )
            pf.terminate()
            pf.wait(timeout=10)
            subprocess.run(
                [
                    "helm",
                    "rollback",
                    "investigator",
                    "1",
                    "--kube-context",
                    CONTEXT,
                    "-n",
                    "veriqta-system",
                    "--wait",
                    "--timeout",
                    "180s",
                ],
                check=True,
            )
            pf = forward()
            assert (
                c.get("/api/investigations/" + original["id"]).raise_for_status().json() == original
            )
            pf.terminate()
            pf.wait(timeout=10)
            stop_app()
            maintenance("backup", "/data/recovery-backup.db")
            start_app()
            pf = forward()
            assert c.delete("/api/investigations/" + original["id"]).status_code == 200
            assert c.get("/api/investigations/" + original["id"]).status_code == 404
            pf.terminate()
            pf.wait(timeout=10)
            stop_app()
            maintenance("restore", "/data/recovery-backup.db")
            maintenance("check")
            start_app()
            pf = forward()
            restored = c.get("/api/investigations/" + original["id"]).raise_for_status().json()
            assert restored == original
            page = c.get("/api/investigations?limit=1").raise_for_status().json()
            assert len(page) == 1 and page[0]["id"] == original["id"] and "evidence" not in page[0]
            child = (
                c.post("/api/investigations/" + original["id"] + "/followup")
                .raise_for_status()
                .json()
            )
            fresh = wait(c, child["id"])
            assert (
                fresh["parent_id"] == original["id"]
                and fresh["evidence"][0]["collected_at"] > original["completed_at"]
            )
            Path(".data/recovery-result.json").write_text(
                json.dumps(
                    {
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "software": "0.1.0",
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
                        "source": "kubernetes",
                        "provider": "mock",
                        "mock": True,
                        "status": "checks_passed_cleanup_pending",
                        "cluster_cleanup_verified": None,
                        "checks": [
                            "schema-1 config upgrade preserves reports",
                            "Helm revision rollback preserves reports",
                            "offline PVC backup",
                            "authorised deletion",
                            "offline PVC restore with previous snapshot",
                            "integrity/schema validation",
                            "restored report equality",
                            "fresh investigation from restored report",
                            "bounded history summaries after restore",
                        ],
                        "kubernetes": json.loads(kubectl("version", "-o", "json"))["serverVersion"][
                            "gitVersion"
                        ],
                        "upgrade_scope": "same binary/schema 1; retention 7 -> 8 -> 7; not a cross-version schema downgrade",
                        "report": original["id"],
                    },
                    indent=2,
                )
                + "\n"
            )
    finally:
        pf.terminate()
        pf.wait(timeout=10)
    print(
        "PVC recovery and schema-compatible Helm configuration rollback passed; mock interpretations only."
    )


if __name__ == "__main__":
    main()
