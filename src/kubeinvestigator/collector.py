import json
from typing import Any

from .policy import Policy, redact
from .schemas import Evidence, ToolArgs


class Collector:
    def __init__(self, settings):
        self.s = settings
        self.policy = Policy(settings)
        self.core: Any = None
        self.apps: Any = None
        self.discovery: Any = None
        if settings.source == "kubernetes":
            from kubernetes import client, config

            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
            configuration = client.Configuration.get_default_copy()
            from urllib.parse import urlsplit

            if not configuration.verify_ssl or urlsplit(configuration.host).scheme != "https":
                raise ValueError(
                    "Kubernetes connections require HTTPS with certificate verification enabled"
                )
            configuration.retries = 0
            api = client.ApiClient(configuration)
            self.core = client.CoreV1Api(api)
            self.apps = client.AppsV1Api(api)
            self.discovery = client.DiscoveryV1Api(api)

    def collect(self, args: ToolArgs, identifier):
        self.policy.tool(args)
        if self.s.source == "fixture":
            data = self.fixture(args)
            truncated = False
        else:
            data, truncated = self.live(args)
        if (
            args.resource == "logs"
            and isinstance(data, dict)
            and str(data.get("text", "")).startswith("unable to retrieve container logs for")
        ):
            raise ValueError("Kubernetes runtime could not retrieve retained container logs")
        data = redact(data)
        # Bound stored evidence, preserving a valid JSON structure.
        if len(json.dumps(data)) > 16000:
            data = {"notice": "Evidence exceeded 16000 characters; reduce workload scope"}
            truncated = True
        return Evidence(
            id=identifier,
            resource=f"{args.namespace}/{args.resource}/{args.name or '*'}",
            data=data,
            truncated=truncated,
        )

    def live(self, a):
        kwargs: dict[str, Any] = {"_request_timeout": (2, self.s.tool_timeout), "limit": 100}
        if a.name and a.resource != "logs":
            kwargs["field_selector"] = (
                "involvedObject.name=" if a.resource == "events" else "metadata.name="
            ) + a.name
        methods = {
            "pods": self.core.list_namespaced_pod,
            "events": self.core.list_namespaced_event,
            "services": self.core.list_namespaced_service,
            "endpointslices": self.discovery.list_namespaced_endpoint_slice,
            "deployments": self.apps.list_namespaced_deployment,
            "replicasets": self.apps.list_namespaced_replica_set,
        }
        if a.resource == "logs":
            return {
                "pod": a.name,
                "container": a.container,
                "previous": a.previous,
                "text": self.core.read_namespaced_pod_log(
                    a.name,
                    a.namespace,
                    container=a.container,
                    previous=a.previous,
                    since_seconds=self.s.log_lookback_seconds,
                    tail_lines=40,
                    limit_bytes=4096,
                    _request_timeout=(2, self.s.tool_timeout),
                ),
            }, True
        result = methods[a.resource](a.namespace, **kwargs)
        truncated = bool(result.metadata._continue)
        if a.resource == "endpointslices":
            truncated = truncated or any(len(obj.endpoints or []) > 100 for obj in result.items)
        if a.resource == "events":
            truncated = truncated or any(len(obj.message or "") > 1000 for obj in result.items)
        return [self.project(a.resource, obj) for obj in result.items], truncated

    @staticmethod
    def project(resource, obj):
        base = {"name": obj.metadata.name}
        if resource == "pods":
            base.update(
                labels=obj.metadata.labels or {},
                phase=obj.status.phase,
                owners=[
                    {"kind": o.kind, "name": o.name} for o in obj.metadata.owner_references or []
                ],
                containers=[],
            )
            for c in obj.status.container_statuses or []:
                state = c.state
                base["containers"].append(
                    {
                        "name": c.name,
                        "ready": c.ready,
                        "restarts": c.restart_count,
                        "waiting": {
                            "reason": state.waiting.reason,
                            "message": (state.waiting.message or "")[:1000],
                        }
                        if state.waiting
                        else None,
                        "terminated": {
                            "reason": state.terminated.reason,
                            "exit_code": state.terminated.exit_code,
                        }
                        if state.terminated
                        else None,
                        "last_exit": {
                            "reason": c.last_state.terminated.reason,
                            "exit_code": c.last_state.terminated.exit_code,
                        }
                        if c.last_state and c.last_state.terminated
                        else None,
                    }
                )
        elif resource == "events":
            base.update(
                reason=obj.reason,
                message=(obj.message or "")[:1000],
                involved={"kind": obj.involved_object.kind, "name": obj.involved_object.name},
                count=obj.count,
            )
        elif resource == "services":
            base.update(selector=obj.spec.selector or {}, type=obj.spec.type)
        elif resource == "endpointslices":
            base.update(
                service=(obj.metadata.labels or {}).get("kubernetes.io/service-name"),
                endpoints=[
                    {
                        "ready": e.conditions.ready if e.conditions else None,
                        "target": e.target_ref.name if e.target_ref else None,
                    }
                    for e in (obj.endpoints or [])[:100]
                ],
            )
        else:
            base.update(
                replicas=obj.status.replicas,
                ready_replicas=obj.status.ready_replicas,
                owners=[
                    {"kind": o.kind, "name": o.name} for o in obj.metadata.owner_references or []
                ],
            )
        return base

    @staticmethod
    def fixture(a):
        values = {
            "pods": [
                {
                    "name": "checkout-crash",
                    "labels": {"app": "checkout"},
                    "phase": "Running",
                    "containers": [
                        {
                            "name": "app",
                            "ready": False,
                            "restarts": 8,
                            "waiting": {"reason": "CrashLoopBackOff"},
                            "last_exit": {"reason": "Error", "exit_code": 1},
                        }
                    ],
                },
                {
                    "name": "catalog-image",
                    "labels": {"app": "catalog"},
                    "phase": "Pending",
                    "containers": [
                        {
                            "name": "app",
                            "ready": False,
                            "restarts": 0,
                            "waiting": {
                                "reason": "ImagePullBackOff",
                                "message": "manifest unknown",
                            },
                        }
                    ],
                },
                {
                    "name": "frontend",
                    "labels": {"app": "frontend"},
                    "phase": "Running",
                    "containers": [{"name": "app", "ready": True, "restarts": 0}],
                },
            ],
            "services": [{"name": "frontend", "selector": {"app": "frontned"}}],
            "endpointslices": [],
            "events": [
                {
                    "name": "catalog-pull",
                    "reason": "Failed",
                    "message": "Failed to pull image: manifest unknown",
                    "involved": {"kind": "Pod", "name": "catalog-image"},
                }
            ],
            "deployments": [],
            "replicasets": [],
            "logs": {
                "text": "Application exited: configuration missing (synthetic fixture)",
                "pod": a.name,
            },
        }
        value = values[a.resource]
        return (
            [
                v
                for v in value
                if not a.name
                or (v.get("involved", {}).get("name") if a.resource == "events" else v["name"])
                == a.name
            ]
            if isinstance(value, list)
            else value
        )
