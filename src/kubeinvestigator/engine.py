import asyncio
import time
from collections import Counter

from .audit import security_event
from .analysis import mock_finding, observations
from .policy import redact
from .provider import OpenAIProvider, ProviderFailure
from .schemas import Evidence, Finding, ToolArgs, now


class Engine:
    def __init__(self, settings, store, collector):
        self.s, self.store, self.collector = settings, store, collector
        self.tasks = {}
        self.sem = asyncio.Semaphore(settings.concurrency)
        self.metrics: Counter[str] = Counter()
        self.provider = OpenAIProvider(settings) if settings.provider == "openai" else None

    def submit(self, report):
        if len(self.tasks) >= self.s.queue_limit:
            raise ValueError("Investigation queue is full; retry later")
        self.store.save(report)
        task = asyncio.create_task(self.execute(report))
        self.tasks[report.id] = task
        task.add_done_callback(lambda _: self.tasks.pop(report.id, None))

    async def execute(self, r):
        started = time.monotonic()
        try:
            async with self.sem:
                r.status = "running"
                self.store.save(r)
                async with asyncio.timeout(self.s.duration):
                    await self.investigate(r)
        except asyncio.CancelledError:
            r.status = "cancelled"
        except TimeoutError:
            r.status = "failed"
            r.finding = None
            r.failures.append("Investigation duration budget exhausted")
            self.metrics["budget_exhausted"] += 1
            security_event("budget_exhausted", investigation_id=r.id)
        except ProviderFailure as exc:
            r.status = "failed"
            r.finding = None
            r.failures.append(str(exc))
        except Exception:
            r.status = "failed"
            r.finding = None
            r.failures.append(
                "Investigation failed; check configuration, storage and provider connectivity. No diagnosis was substituted."
            )
        finally:
            r.completed_at = now()
            security_event("investigation_finished", investigation_id=r.id, status=r.status)
            r.duration_seconds = round(time.monotonic() - started, 3)
            self.metrics[r.status.replace(" ", "_")] += 1
            self.metrics["duration_milliseconds"] += int(r.duration_seconds * 1000)
            try:
                self.store.save(r)
            except Exception:
                self.metrics["storage_errors"] += 1

    async def tool(self, r, args):
        if len(r.evidence) >= self.s.max_calls:
            self.metrics["budget_exhausted"] += 1
            security_event("budget_exhausted", investigation_id=r.id)
            raise ValueError("Tool-call budget exhausted")
        self.collector.policy.tool(args)
        if args.namespace != r.namespace:
            raise ValueError("Tool cannot change the investigation namespace")
        started = time.monotonic()
        eid = f"E{len(r.evidence) + 1}"
        try:
            # The underlying client also has a socket timeout. Shield prevents cancellation
            # from freeing the concurrency slot while its blocking thread is still running.
            task = asyncio.create_task(asyncio.to_thread(self.collector.collect, args, eid))
            try:
                evidence = await asyncio.shield(task)
            except asyncio.CancelledError:
                await task
                raise
        except asyncio.CancelledError:
            raise
        except Exception:
            evidence = Evidence(
                id=eid,
                resource=f"{args.namespace}/{args.resource}/{args.name or '*'}",
                data=[],
                error="Collection failed: check RBAC, object existence and Kubernetes connectivity",
            )
            self.metrics["tool_errors"] += 1
        self.metrics["tool_calls"] += 1
        self.metrics["tool_milliseconds"] += int((time.monotonic() - started) * 1000)
        r.evidence.append(evidence)
        self.store.save(r)

    async def investigate(self, r):
        resources = (
            ["pods", "events"]
            if r.scenario != "service"
            else ["pods", "services", "endpointslices"]
        )
        for resource in resources:
            await self.tool(
                r,
                ToolArgs(
                    namespace=r.namespace,
                    resource=resource,  # type: ignore[arg-type]
                    name=r.workload
                    if (
                        resource == "services"
                        or (resource in {"pods", "events"} and r.scenario != "service")
                    )
                    else "",
                ),
            )
        if r.scenario == "crash" and self.s.logs:
            for evidence in list(r.evidence):
                if evidence.resource.split("/")[1] != "pods" or not isinstance(evidence.data, list):
                    continue
                targets = [
                    (pod["name"], c["name"])
                    for pod in evidence.data
                    for c in pod.get("containers", [])
                    if (c.get("waiting") or {}).get("reason") == "CrashLoopBackOff"
                ]
                for pod, container in targets[:1]:
                    for previous in [False, True]:
                        await self.tool(
                            r,
                            ToolArgs(
                                namespace=r.namespace,
                                resource="logs",
                                name=pod,
                                container=container,
                                previous=previous,
                            ),
                        )
        r.observations = observations(r)
        if self.provider:
            for _ in range(self.s.max_turns):
                try:
                    action, usage = await self.provider.turn(r)
                except Exception:
                    self.metrics["provider_errors"] += 1
                    raise
                if isinstance(usage.get("model_revision"), str):
                    r.model = redact(usage["model_revision"])
                for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    r.usage[key] = r.usage.get(key, 0) + int(usage.get(key, 0))
                    self.metrics[key] += int(usage.get(key, 0))
                if "tool" in action:
                    await self.tool(r, ToolArgs.model_validate(action["tool"]))
                    r.observations = observations(r)
                else:
                    r.finding = Finding.model_validate(redact(action["finding"]))
                    break
            else:
                self.metrics["budget_exhausted"] += 1
                security_event("budget_exhausted", investigation_id=r.id)
                raise ProviderFailure("Model-turn budget exhausted; narrow scope or review limits")
        else:
            r.finding = mock_finding(r)
        known = {e.id for e in r.evidence if not e.error}
        if not r.finding or not set(r.finding.evidence_ids) <= known:
            raise ValueError("Model cited unknown or inaccessible evidence")
        resource_refs: set[str] = set()
        for e in r.evidence:
            if not e.error and isinstance(e.data, list):
                resource_refs.update(
                    f"{r.namespace}/{e.resource.split('/')[1]}/{obj['name']}"
                    for obj in e.data
                    if isinstance(obj, dict) and "name" in obj
                )
        if not set(r.finding.resource_refs) <= resource_refs:
            raise ValueError("Invented resource reference")
        r.limitations.append(
            "Model prose is an interpretation; only validated evidence IDs and structured resource references are authoritative."
        )
        if not known or not r.finding.evidence_ids:
            r.status = "insufficient evidence"
        else:
            r.status = (
                "insufficient evidence"
                if r.finding.assessment == "insufficient evidence"
                else "completed"
            )
        if r.parent_id:
            parent = self.store.get(r.parent_id)
            same_resources = (
                {e.resource.split("/")[1] for e in parent.evidence if not e.error}
                <= {e.resource.split("/")[1] for e in r.evidence if not e.error}
                if parent
                else False
            )
            if r.source == "fixture":
                r.verification = "Synthetic fixture evidence; cannot verify a real correction."
            elif (
                r.failures
                or any(e.error or e.truncated for e in r.evidence)
                or not same_resources
                or not any(e.resource.split("/")[1] == "pods" and e.data for e in r.evidence)
                or (
                    r.scenario == "service"
                    and not any(
                        e.resource.split("/")[1] == "services" and e.data for e in r.evidence
                    )
                )
            ):
                r.verification = "Inconclusive: evidence is missing or incomplete."
            elif not r.observations and parent and parent.observations:
                r.verification = "Previously observed condition is absent in fresh evidence. This does not guarantee application health."
            else:
                r.verification = (
                    "Condition remains observed, or no prior condition was established."
                )

    async def cancel(self, identifier):
        task = self.tasks.get(identifier)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        r = self.store.get(identifier)
        if r and r.status in {"queued", "running"}:
            r.status = "cancelled"
            r.completed_at = now()
            self.store.save(r)

    async def shutdown(self):
        await asyncio.gather(*(self.cancel(identifier) for identifier in list(self.tasks)))
