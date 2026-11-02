# Configuration reference

Environment variables are read once on startup and validated. Chart values expose the deployment-relevant subset. Changing credentials requires restart. Namespace permissions must also be changed in the Roles/RoleBindings. No environment file is auto-loaded; export variables or use your process/Secret manager.

| Variable | Default | Boundary |
| --- | --- | --- |
| KI_TOKEN | required | At least 32 characters, randomly generated; server-side Secret |
| KI_NAMESPACES | veriqta-demo | Comma-separated explicit DNS namespace names; never `*` |
| KI_PROVIDER | mock | mock or openai |
| KI_SOURCE | fixture | fixture or kubernetes; chart forces kubernetes |
| KI_MODEL | gpt-4.1-mini | Candidate live model; not live-tested |
| KI_API_KEY | unset | Required only for live provider; never chart values |
| KI_DATABASE | .data/investigations.db | Container uses /data/investigations.db |
| KI_LOGS | false | Enable narrow current/previous pod logs and chart permission together |
| KI_CONCURRENCY | 2 | 1–8 running jobs; one process only |
| KI_QUEUE_LIMIT | 20 | 1–100 total accepted active/queued jobs |
| KI_DURATION | 90 | 1–300 seconds per running job; socket cleanup can overrun |
| KI_TOOL_TIMEOUT | 8 | 1–30 read seconds plus 2-second connect timeout |
| KI_MAX_CALLS | 8 | 1–16 tool calls, including failures |
| KI_MAX_TURNS | 6 | 1–12 model turns; no hidden retries |
| KI_RETENTION_DAYS | 7 | 1–90 days; terminal report cleanup |
| KI_MAX_RECORDS | 500 | 1–10000 records; refuse new work at cap |
| KI_MAX_DB_BYTES | 100000000 | Admission threshold, at least 100000 bytes |
| KI_SESSION_SECONDS | 3600 | 60–86400 seconds; in-memory sessions |
| KI_SECURE_COOKIE | false | Must be true for HTTPS shared access; Helm enables with ingress |

Fixed safety budgets are 10KB HTTP request body, 100 Kubernetes list objects, 16KB retained evidence, 40 log lines/4096 log bytes, 48K model input characters, 32KB provider response and 1600 completion tokens per turn. These are conservative defaults for small namespace scopes; larger deployments should first narrow scope rather than remove bounds. No external provider endpoint is configurable through a model action.

Additional release hardening: `KI_LOG_LOOKBACK_SECONDS` defaults to 3600 and accepts 60–86400 seconds. Current and previous log calls pass this bound alongside 40 lines/4096 bytes and socket deadlines. The Helm value is `logLookbackSeconds`. History requests default to 30 summaries and cap `limit` at 100, with non-negative `offset`; full report evidence is fetched only by the separately authorised detail/export routes. Metrics and admission counts use aggregate SQL rather than deserializing every evidence body. [Generated configuration schema](config.schema.json) is derived from `Settings`, not a separately maintained set of defaults.
