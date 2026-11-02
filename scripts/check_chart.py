"""Validate security invariants in Helm-rendered YAML; does not contact Kubernetes."""

import sys
from pathlib import Path
import yaml

objects = [obj for obj in yaml.safe_load_all(Path(sys.argv[1]).read_text()) if obj]
allowed = {
    "": {"pods", "events", "services", "pods/log"},
    "apps": {"deployments", "replicasets"},
    "discovery.k8s.io": {"endpointslices"},
}
for obj in objects:
    kind = obj["kind"]
    assert kind not in {"ClusterRole", "ClusterRoleBinding"}, "Runtime RBAC must be namespaced"
    if kind == "Role":
        assert obj["metadata"].get("namespace"), "Role namespace must be explicit"
        for rule in obj["rules"]:
            assert set(rule["verbs"]) <= {"get", "list"} and rule["verbs"]
            for group in rule["apiGroups"]:
                assert group in allowed and set(rule["resources"]) <= allowed[group]
            if "pods/log" in rule["resources"]:
                assert rule["verbs"] == ["get"]
    if kind == "Deployment":
        assert obj["spec"]["replicas"] == 1 and obj["spec"]["strategy"]["type"] == "Recreate"
        spec = obj["spec"]["template"]["spec"]
        assert spec["securityContext"]["runAsNonRoot"]
        assert not any("hostPath" in volume for volume in spec["volumes"])
        for container in spec["containers"]:
            for env in container.get("env", []):
                if env["name"] in {
                    "KI_MAX_DB_BYTES",
                    "KI_MAX_RECORDS",
                    "KI_RETENTION_DAYS",
                    "KI_CONCURRENCY",
                }:
                    assert env["value"].isdigit(), (
                        "Integer configuration must not use scientific notation"
                    )
            security = container["securityContext"]
            assert security["readOnlyRootFilesystem"] and not security["allowPrivilegeEscalation"]
            assert "ALL" in security["capabilities"]["drop"]
            assert all(
                probe in container for probe in ["startupProbe", "readinessProbe", "livenessProbe"]
            )
    if kind == "Service":
        assert obj["spec"]["type"] == "ClusterIP"
    if kind == "Ingress":
        assert obj["spec"]["tls"] and all(tls["secretName"] for tls in obj["spec"]["tls"])
assert any(obj["kind"] == "Role" for obj in objects)
assert any(obj["kind"] == "PersistentVolumeClaim" for obj in objects)
print(
    "Rendered chart RBAC, storage, network exposure, health probes and container hardening invariants passed."
)
