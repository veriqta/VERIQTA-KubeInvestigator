import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi import Request as HTTPRequest
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, SecretStr

from .audit import security_event
from .collector import Collector
from .config import Settings
from .engine import Engine
from .policy import Policy, redact
from .schemas import Report, Request, HistoryItem
from .store import Store

log = logging.getLogger("kubeinvestigator")
STATIC = Path(__file__).parent / "static"


class Login(BaseModel):
    token: SecretStr = Field(max_length=1024)


def markdown(report):
    # Escape HTML and Markdown metacharacters in all untrusted content.
    def safe(value):
        import html

        text = html.escape(str(value))
        for c in "\\`*_{}[]()#+.!|>-":
            text = text.replace(c, "\\" + c)
        return text

    lines = [
        "# VERIQTA KubeInvestigator",
        "",
        "MOCK" if report.mock else "LIVE PROVIDER",
        "",
        f"ID: {report.id}",
        f"Status: {report.status}",
        f"Created: {report.created_at}",
        f"Completed: {report.completed_at}",
        f"Namespace: {safe(report.namespace)}",
        f"Workload: {safe(report.workload or 'namespace scope')}",
        f"Scenario: {safe(report.scenario)}",
        f"Evidence source: {safe(report.source)}",
        f"Duration seconds: {report.duration_seconds}",
        f"Problem: {safe(report.problem)}",
        "",
        "## Observations",
    ]
    lines += ["- " + safe(o) for o in report.observations]
    if report.finding:
        lines += [
            "",
            "## Interpretation",
            safe(report.finding.diagnosis),
            "Assessment: " + report.finding.assessment,
            "Evidence IDs: " + safe(report.finding.evidence_ids),
            "Resource references: " + safe(report.finding.resource_refs),
            "",
            "## Alternatives",
        ]
        lines += ["- " + safe(o) for o in report.finding.alternatives]
        lines += ["", "## Manual next steps"] + ["- " + safe(o) for o in report.finding.next_steps]
    lines += ["", "## Evidence"]
    for e in report.evidence:
        lines += [
            f"### {e.id}",
            safe(e.resource),
            safe(e.collected_at),
            safe(json.dumps(e.data)),
            safe(e.error or ""),
            f"Truncated: {e.truncated}",
        ]
    lines += ["", "## Limitations"] + ["- " + safe(o) for o in report.limitations + report.failures]
    lines += [
        "",
        safe(report.verification or ""),
        "Usage: " + safe(report.usage),
        "Estimated cost: unavailable",
        f"Report schema: {report.schema_version}; software: {report.software_version}; provider: {report.provider}; model: {safe(report.model)}",
        "Parent: " + safe(report.parent_id),
        "Follow-ups: " + safe(report.followup_ids),
    ]
    return "\n".join(lines)


def create_app(settings=None, collector=None):
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False
    try:
        s = settings or Settings.environment()
    except ValueError:
        security_event("configuration_rejected")
        raise
    store = Store(s)
    policy = Policy(s)
    try:
        engine = Engine(s, store, collector or Collector(s))
    except Exception:
        store.close()
        security_event("configuration_rejected")
        raise
    preview_sem = asyncio.Semaphore(1)
    sessions: dict[str, tuple[float, str]] = {}
    rate: dict[str, tuple[int, float]] = {}

    async def cleanup():
        while True:
            await asyncio.sleep(60)
            try:
                store.cleanup()
            except Exception:
                engine.metrics["cleanup_errors"] += 1

    @asynccontextmanager
    async def lifespan(app):
        cleaner = asyncio.create_task(cleanup())
        try:
            yield
        finally:
            cleaner.cancel()
            await asyncio.gather(cleaner, return_exceptions=True)
            await engine.shutdown()
            store.close()

    app = FastAPI(
        title="VERIQTA KubeInvestigator",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.engine, app.state.store = engine, store

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return JSONResponse(
            {
                "detail": [
                    {"loc": error["loc"], "type": error["type"], "msg": error["msg"]}
                    for error in exc.errors()
                ]
            },
            status_code=422,
        )

    @app.middleware("http")
    async def guard(request, call_next):
        rid = str(uuid4())
        request.state.request_id = rid
        try:
            content_length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return Response("Invalid Content-Length", status_code=400)
        if content_length > 10000:
            return Response("Request too large", status_code=413)
        # Bound even chunked requests; cache the body for downstream parsing.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 10000:
                return Response("Request too large", status_code=413)
        request._body = bytes(body)
        key = request.client.host if request.client else "unknown"
        t = time.monotonic()
        for k in list(rate):
            if rate[k][1] < t:
                del rate[k]
        count, expiry = rate.get(key, (0, t + 60))
        rate[key] = (count + 1, expiry)
        login_key = "login:" + key
        login_count, login_expiry = rate.get(login_key, (0, t + 60))
        if request.url.path == "/api/login":
            rate[login_key] = (login_count + 1, login_expiry)
            if login_count >= 10:
                security_event("rate_limit_exceeded", request_id=rid, status=429)
                return Response("Sign-in rate limit exceeded", status_code=429)
        if count >= 180 or len(rate) > 10000:
            security_event("rate_limit_exceeded", request_id=rid, status=429)
            return Response("Rate limit exceeded; retry in one minute", status_code=429)
        try:
            response = await call_next(request)
        except sqlite3.Error:
            engine.metrics["storage_errors"] += 1
            security_event("storage_failure", request_id=rid, status=507)
            response = JSONResponse(
                {
                    "detail": "Storage unavailable or full; stop new work, check capacity and restore a verified backup if needed"
                },
                status_code=507,
            )
        response.headers.update(
            {
                "X-Request-ID": rid,
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            }
        )
        route = request.scope.get("route")
        template = getattr(route, "path", "")
        event = "http_request"
        if response.status_code == 401:
            event = "authentication_failed"
        elif response.status_code == 403:
            event = "access_denied"
        elif response.status_code < 300:
            event = {
                ("POST", "/api/login"): "session_created",
                ("POST", "/api/logout"): "session_invalidated",
                ("GET", "/api/investigations/{identifier}/export"): "report_exported",
                ("DELETE", "/api/investigations/{identifier}"): "report_deleted",
                ("POST", "/api/investigations/{identifier}/cancel"): "investigation_cancelled",
            }.get((request.method, template), event)
        identifier = request.path_params.get("identifier")
        if identifier:
            from uuid import UUID

            try:
                identifier = str(UUID(identifier))
            except ValueError:
                identifier = None
        security_event(
            event, request_id=rid, investigation_id=identifier, status=response.status_code
        )
        if s.secure_cookie and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    def auth(req: HTTPRequest):
        authorization = req.headers.get("authorization", "")
        if authorization.startswith("Bearer ") and hmac.compare_digest(
            authorization[7:].encode(), s.token.get_secret_value().encode()
        ):
            return "team"
        cookie = req.cookies.get("ki_session", "")
        digest = hashlib.sha256(cookie.encode()).hexdigest()
        session = sessions.get(digest)
        if not session or session[0] < time.monotonic():
            sessions.pop(digest, None)
            raise HTTPException(401, "Session expired or missing; sign in")
        if req.method not in {"GET", "HEAD"} and not hmac.compare_digest(
            req.headers.get("x-csrf-token", "").encode(), session[1].encode()
        ):
            raise HTTPException(403, "CSRF token missing or invalid")
        return "team"

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready():
        try:
            store.get("readiness")
        except Exception:
            raise HTTPException(503, "Storage unavailable")
        return {"status": "ready"}

    @app.post("/api/login")
    def login(body: Login, response: Response):
        if not hmac.compare_digest(
            body.token.get_secret_value().encode(), s.token.get_secret_value().encode()
        ):
            raise HTTPException(401, "Invalid team access token")
        t = time.monotonic()
        for k in list(sessions):
            if sessions[k][0] < t:
                del sessions[k]
        if len(sessions) >= 100:
            raise HTTPException(429, "Session limit reached")
        cookie, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        sessions[hashlib.sha256(cookie.encode()).hexdigest()] = (t + s.session_seconds, csrf)
        response.set_cookie(
            "ki_session",
            cookie,
            httponly=True,
            secure=s.secure_cookie,
            samesite="strict",
            max_age=s.session_seconds,
            path="/",
        )
        return {"csrf": csrf}

    @app.post("/api/logout", dependencies=[Depends(auth)])
    def logout(req: HTTPRequest, response: Response):
        sessions.pop(hashlib.sha256(req.cookies.get("ki_session", "").encode()).hexdigest(), None)
        response.delete_cookie("ki_session")
        return {"status": "signed out"}

    @app.get("/api/config", dependencies=[Depends(auth)])
    def config():
        return {
            "version": "0.1.0",
            "namespaces": s.namespaces,
            "provider": s.provider,
            "source": s.source,
            "mock": s.provider == "mock",
            "model": s.model if s.provider != "mock" else "deterministic-fixture-v1",
            "logs": s.logs,
            "workspace": "Trusted team: all authenticated users share every report",
        }

    async def preview(args, identifier):
        if preview_sem.locked():
            raise HTTPException(429, "A connection check is already active; retry shortly")
        async with preview_sem:
            task = asyncio.create_task(
                asyncio.to_thread(engine.collector.collect, args, identifier)
            )
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                await task
                raise

    @app.get("/api/workloads", dependencies=[Depends(auth)])
    async def workloads(namespace: str):
        from .schemas import ToolArgs

        policy.namespace(namespace)
        try:
            result = await preview(ToolArgs(namespace=namespace, resource="pods"), "preview")
            if not isinstance(result.data, list):
                raise HTTPException(
                    413,
                    "Pod evidence exceeded its size budget; narrow the configured namespace scope",
                )
            return {"pods": [p["name"] for p in result.data], "truncated": result.truncated}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                502, "Cannot list pods: check restricted credentials and connectivity"
            )

    def report_or_404(identifier):
        r = store.get(identifier)
        if r is None:
            raise HTTPException(404, "Investigation not found or expired")
        policy.namespace(r.namespace)
        return r

    def submit(body, parent=None, request_id=None):
        policy.namespace(body.namespace)
        if not store.capacity():
            raise HTTPException(
                507, "Storage limit reached; export and delete old reports or expand storage"
            )
        r = Report(
            id=str(uuid4()),
            **redact(body.model_dump()),
            provider=s.provider,
            model=s.model if s.provider != "mock" else "deterministic-fixture-v1",
            source=s.source,
            mock=s.provider == "mock",
            parent_id=parent.id if parent else None,
        )
        try:
            engine.submit(r)
        except ValueError:
            raise HTTPException(429, "Investigation queue is full")
        if parent:
            parent.followup_ids.append(r.id)
            store.save(parent)
        security_event("investigation_created", request_id=request_id, investigation_id=r.id)
        return r

    @app.post(
        "/api/investigations", status_code=202, dependencies=[Depends(auth)], response_model=Report
    )
    async def create(body: Request, req: HTTPRequest):
        return submit(body, request_id=req.state.request_id)

    @app.get("/api/investigations", dependencies=[Depends(auth)], response_model=list[HistoryItem])
    def history(
        limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0, le=10000)
    ):
        return store.history(s.namespaces, limit, offset)

    @app.get(
        "/api/investigations/{identifier}", dependencies=[Depends(auth)], response_model=Report
    )
    def detail(identifier: str):
        return report_or_404(identifier)

    @app.post(
        "/api/investigations/{identifier}/followup",
        status_code=202,
        dependencies=[Depends(auth)],
        response_model=Report,
    )
    async def followup(identifier: str, req: HTTPRequest):
        r = report_or_404(identifier)
        if r.status in {"running", "queued"}:
            raise HTTPException(409, "Wait for or cancel the original investigation")
        return submit(
            Request(
                namespace=r.namespace, workload=r.workload, problem=r.problem, scenario=r.scenario
            ),
            r,
            request_id=req.state.request_id,
        )

    @app.post("/api/investigations/{identifier}/cancel", dependencies=[Depends(auth)])
    async def cancel(identifier: str):
        report_or_404(identifier)
        await engine.cancel(identifier)
        return report_or_404(identifier)

    @app.delete("/api/investigations/{identifier}", dependencies=[Depends(auth)])
    def delete(identifier: str):
        r = report_or_404(identifier)
        if r.status in {"queued", "running"}:
            raise HTTPException(409, "Cancel the investigation before deleting")
        store.delete(identifier)
        return {"status": "deleted"}

    @app.get("/api/investigations/{identifier}/export", dependencies=[Depends(auth)])
    def export(identifier: str, format: str = "json"):
        r = report_or_404(identifier)
        if format not in {"json", "md"}:
            raise HTTPException(422, "Use json or md")
        return Response(
            r.model_dump_json(indent=2) if format == "json" else markdown(r),
            media_type="application/json" if format == "json" else "text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="investigation-{r.id}.{format}"'
            },
        )

    @app.post("/api/diagnostics", dependencies=[Depends(auth)])
    async def diagnostics():
        from .schemas import ToolArgs

        checks = []
        for namespace in s.namespaces:
            for resource in [
                "pods",
                "events",
                "services",
                "endpointslices",
                "deployments",
                "replicasets",
            ]:
                try:
                    await preview(
                        ToolArgs(namespace=namespace, resource=resource),  # type: ignore[arg-type]
                        "diagnostic",
                    )
                    checks.append({"namespace": namespace, "resource": resource, "ok": True})
                except Exception as exc:
                    category = "Kubernetes API or connection failure"
                    if type(exc).__name__ in {"ValidationError", "AttributeError", "TypeError"}:
                        category = "Kubernetes client or response compatibility failure"
                    checks.append(
                        {
                            "namespace": namespace,
                            "resource": resource,
                            "ok": False,
                            "category": category,
                            "remedy": "Check RBAC, API availability and restricted kubeconfig",
                        }
                    )
        return {
            "mock": s.provider == "mock",
            "source": s.source,
            "checks": checks,
            "provider": "Not called; live validation is opt-in",
            "storage_capacity": store.capacity(),
        }

    @app.get("/metrics", dependencies=[Depends(auth)])
    def metrics():
        values = dict(engine.metrics)
        counts = store.state_counts()
        values["queue_depth"] = counts.get("queued", 0)
        values["active"] = counts.get("running", 0)
        return Response(
            "".join(f"kubeinvestigator_{k} {v}\n" for k, v in values.items()),
            media_type="text/plain",
        )

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    return app
