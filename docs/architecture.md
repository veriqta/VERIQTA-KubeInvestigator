# Architecture and decisions

One FastAPI process serves a static browser interface and a typed API. An in-process bounded queue runs at most two investigations by default. Blocking official Kubernetes client calls run in threads, with socket timeouts and zero client retries. Cancellation waits for an in-flight socket call before releasing its investigation slot. The wall-clock deadline may therefore overrun by one socket timeout; it never enables another tool call after cancellation.

SQLite stores report schema 1.0, redacted evidence and lifecycle state. `PRAGMA user_version=1` is the initial transactional schema migration. Newer database versions are rejected. On startup, queued/running records become interrupted. Graceful shutdown cancels work. Neither path automatically resumes paid work. A linked follow-up collects a new snapshot.

The registered `collect` tool validates `ToolArgs`: explicit namespace, seven resource types, bounded resource/container names, and a previous-log flag. It has no write, shell, network-probe, proxy or arbitrary destination argument. Core v1, apps/v1 and discovery.k8s.io/v1 are used without legacy fallback. Snapshots are at most 100 objects per call; continuation is flagged. Each retained evidence item is at most 16,000 characters. Logs are opt-in and limited to 40 lines / 4096 bytes. Crash investigations collect current and previous logs for one observed crashing container when enabled. Named pod investigations filter events by involvedObject.name. At most eight tools, six provider turns and 90 seconds per running investigation are allowed by default. Provider inputs are limited to 48,000 characters and outputs to 1600 completion tokens and 32,000 response bytes, enforced while reading the HTTP response. Characters conservatively bound input size; they are not a token estimate.

Deterministic observations compare statuses and selectors. A replaceable provider adapter returns validated actions or a finding; mock output is separately labelled. Evidence IDs and structured resource references must belong to collected evidence. Free-text statements remain interpretations and may contain errors. Missing/inaccessible evidence and truncation are visible. Verification uses fresh deterministic observations, refuses a clearance claim on missing/empty/truncated snapshots, and never guarantees application health.

## Decision log

| Decision | Reason | Consequence |
| --- | --- | --- |
| Single process, SQLite WAL, one replica | Reproducible self-hosted installation without queue/database services | No HA; no multi-worker deployment; local filesystem with SQLite locking required |
| Static HTML/CSS/JS | A structured evidence workflow needs no frontend build system | Small deployment and direct text rendering; no arbitrary HTML/Markdown rendering |
| Shared team token exchanged for expiring cookie | Usable authenticated first release without identity infrastructure | Every authenticated member can read/delete every report; no per-user isolation or audit identity |
| No provider retries | Avoid repeated costs and hidden repeated work | Transient failure requires a new explicit investigation |
| Logs off by default | Reduce accidental disclosure | Crash causes may remain uncertain without opt-in logs |
| Fixture source distinct from mock provider | Separate synthetic evidence from deterministic interpretation | Cluster smoke uses real Kubernetes evidence with mock interpretations |
| No automatic correction | Keep runtime permissions read-only | Engineer changes workloads outside the app |

## Reference review (2026-11-01)

[K8sGPT getting started](https://docs.k8sgpt.ai/getting-started/getting-started/) separates cluster prerequisites, provider authentication and analysis. This project likewise exposes external model access near installation.
[HolmesGPT](https://holmesgpt.dev/latest/) documents installation and tool configuration; this project keeps tool access explicitly registered and enforced in code.
[OpenTelemetry Demo](https://opentelemetry.io/docs/demo/) presents installation and reproducible scenarios separately; this project provides disposable failure examples and correction steps.
[FastAPI deployment](https://fastapi.tiangolo.com/deployment/) informs the single-process deployment profile.
[Official Python client](https://github.com/kubernetes-client/python) supplies supported API clients.
[Kubernetes releases](https://kubernetes.io/releases/) listed maintained branches 1.35–1.37 at research time; these are the target range, not claimed tested clusters.
[Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) and [JSON mode](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat) define the live adapter contract. No upstream product identity, prose or code has been copied.
