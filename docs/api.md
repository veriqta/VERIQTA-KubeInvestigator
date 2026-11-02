# API and report schema

All `/api` endpoints except POST `/api/login` require an expiring browser cookie or `Authorization: Bearer TEAM_TOKEN`. Cookie writes also require `X-CSRF-Token` returned at login. Keep credentials out of URLs, shell history, logs and screenshots. All reports share the trusted-team authorisation model. Health endpoints and static login assets are public. `/metrics` is authenticated. Unknown namespaces return 403, missing/expired reports 404, invalid schemas 422, busy queues 429, and full storage 507.

| Method | Path | Behaviour |
| --- | --- | --- |
| POST | /api/login | Exchange `{token}` for HttpOnly session and CSRF response |
| POST | /api/logout | Invalidate current browser session |
| GET | /api/config | Public-safe version, namespace scope, provider/source mode |
| GET | /api/workloads?namespace=NAME | Authorised pod name suggestions; list is bounded |
| POST | /api/diagnostics | Check each required resource in configured namespaces; no paid calls |
| POST | /api/investigations | Submit typed request, return queued report with HTTP 202 |
| GET | /api/investigations | Shared team history within current configured namespace scope |
| GET | /api/investigations/ID | Persistent report and progress |
| POST | /api/investigations/ID/cancel | Cancel queued/running work, wait for active client call to finish |
| POST | /api/investigations/ID/followup | Collect fresh evidence with original scope/problem and parent link |
| GET | /api/investigations/ID/export?format=json | Download versioned JSON (or format=md) |
| DELETE | /api/investigations/ID | Delete a terminal record; cancel first if active |

Example using a private environment token and a server running on localhost:

```sh
.venv/bin/python - <<'PYCODE'
import os, httpx
with httpx.Client(base_url='http://127.0.0.1:8080', headers={'Authorization':'Bearer '+os.environ['KI_TOKEN']}) as c:
    response = c.post('/api/investigations', json={
        'namespace':'veriqta-demo', 'workload':'frontend',
        'scenario':'service', 'problem':'The Service has no endpoints'
    })
    response.raise_for_status()
    print(response.json()['id'])
PYCODE
```

Scenario is crash, image or service; problem length 8–2000; resource name is optional (for service, a Service name; for others, a Pod name). Selector checks retain all namespace pods even with a named Service. Unexpected fields and write-tool requests are rejected.

Report schema 1.0 is defined in [schemas.py](../src/kubeinvestigator/schemas.py); [report.schema.json](report.schema.json) is generated from the actual model. UTC timestamps, software version, provider/model, evidence source/mock flags, namespace, problem, lifecycle, deterministic observations, finding, evidence IDs/resources/collection time, alternatives, manual next steps, failures/truncation, limitations, token usage, nullable estimated cost, duration, parent and follow-up links are included. Provider package version is not relevant to the direct HTTP adapter; model aliases may not expose an exact backend revision. Evidence IDs and structured resource_refs are validated. Model prose remains fallible.

Valid states: queued → running → completed / insufficient evidence / failed / cancelled. A queued job may be cancelled; queued/running records recovered after an unclean restart become interrupted. Completed means the workflow finished, not that the workload is healthy. Follow-up snapshots are linked, never reused. Service absence, missing pods or incomplete evidence cannot establish correction.

History is now a bounded `HistoryItem[]` response: `GET /api/investigations?limit=30&offset=0`, with limit 1–100 and offset 0–10000. It includes identifiers, scope, scenario, status, creation time and mode; problem statements, evidence and model findings are omitted. Fetch `/api/investigations/ID` for the full report. The UI provides Older/Newer navigation and uses the detail route for the selected report. This is an unreleased API change; clients must not assume history rows contain complete reports. Validation errors omit submitted values/context so malformed login inputs do not reflect credentials.
