# Threat model and supported boundaries

This is an implementation self-review, not an independent security audit. The supported profile is one application process/replica, one cluster, explicit namespaces, one shared trusted team, manual requests and manual corrections. Read-only Kubernetes access can still expose confidential workload information. No automated remediation, arbitrary shell tool, enterprise multi-tenancy or complete prompt-injection protection is claimed.

## Assets, identities and trust

Protect team access tokens, session cookies/CSRF tokens, provider keys and quota, Kubernetes service-account credentials, redacted reports and backups, application availability, source/build integrity and release artifacts. Installation administrators can create scoped Roles/Bindings, Secrets and application workloads. That installer identity must never enter the application pod. Runtime credentials can read only the named resource types in configured namespaces. Every authenticated team member can read/export/delete every report: a compromised team token compromises that entire workspace, not an isolated personal account.

The browser is an untrusted client. HTTP requests enter authenticated/authorised API routes; cookie writes also require CSRF. Opaque session tokens use Python's standard secure random generation, constant-time comparison and SHA-256 digests; no custom cipher, JWT or password-hashing algorithm is implemented. No local password account, OIDC or proxy identity mode is offered. The server ignores client-supplied identity headers. Tokens need secure provisioning, rotation and HTTPS outside localhost. Individual user authentication/isolation would require a reviewed identity integration before being advertised.

The Kubernetes API is authenticated separately from application users. Its selected data, including logs, events, labels, status messages and owner names, remains untrusted. Fields are allowlisted, redacted and bounded before storage or optional provider submission. SQLite and backups are sensitive local assets. Files use private permissions; encryption at rest is the operator's disk/PVC/backup responsibility, not an application feature. Deletion cannot remove historical backups or provider-side records. Shared/remote SQLite writers, multiple workers/replicas and untrusted shared users are unsupported.

The model boundary is a fixed HTTPS OpenAI destination, enabled explicitly by server configuration. Neither the user nor model can choose an endpoint, URL, shell command, file or credential. HTTP redirects are refused, TLS verification stays enabled, and response reading is bounded. Standard HTTPX trust in operator environment proxy/custom certificate configuration must be reviewed by the operator (`HTTPS_PROXY`, `NO_PROXY`, `SSL_CERT_FILE` and `SSL_CERT_DIR`); no UI field controls them. Provider keys are never included in model messages. Mock mode sends no provider request. Application request/turn limits constrain work but cannot guarantee a provider-side spending cap or final bill.

CI executes contributor code in disposable hosted runners, with read-only repository permissions, no provider/deployment secrets, no pull_request_target context, and no package publication. Actions and the base-image index are pinned; this narrows drift but does not prove upstream safety. Local kind uses a privileged node container as required by kind; that installer/runtime boundary does not grant privilege or host mounts to the application pod.

## Abuse paths and controls

| Threat | Implemented controls | Residual risk and operator responsibility |
| --- | --- | --- |
| Compromised team account/token | Expiring HttpOnly SameSite sessions, CSRF, logout/restart invalidation, rate limits, no URL credentials | Entire team workspace is shared; rotate token and restart. No individual attribution or report isolation |
| Stolen provider key | Server-only Secret/env, fixed destination, no request-body logging, bounded requests | Operator/cluster-admin/host compromise can expose the key; rotate/revoke at provider, inspect bills and apply provider-side limits |
| Malicious workload instructions | Selected fields, redaction, validated tool schemas, namespace/resource checks outside model, no writes/shell/URL-fetch tool | Semantic diagnoses can still be wrong. Adversarial tests cover specific controls, not all injection |
| Manipulated model response | Bounded HTTP reads, JSON/Pydantic validation, known evidence IDs/structured resource references, text-only UI rendering | Free-text claims can remain unsupported; review evidence and manual steps before acting |
| Report identifier guessing | Every detail/export/follow-up/cancel/delete route authenticates and checks current namespace policy | Authenticated team users intentionally share reports; UUIDs are not tenant isolation |
| Confidential logs/events | Logs disabled by default; field minimisation, redaction, size/line limits, retention | Unknown/encoded/multiline secrets and PII may remain. Restrict namespace scope and review exports |
| XSS/path/SQL/command injection | textContent/native DOM, escaped Markdown, CSP/frame restrictions, parameterised SQL, no file export paths or shell tools | Full independent browser/security review remains unperformed |
| Resource exhaustion/cost abuse | IP/workspace ingress limits, bounded queue/concurrency/tools/turns/duration, evidence/output/storage admission limits | Distributed clients and trusted members can still consume resources; ingress/provider quotas and filesystem reserves remain necessary |
| Compromised dependencies/builds | Version locks, immutable action/base pins, scanner/license/SBOM/checksum workflow preparation | Scanners have incomplete coverage. Signing/provenance and executed release pipeline still require validation |
| Runtime credentials overreach | Exact namespaced RBAC, no Secret/ConfigMap/node/exec/attach/proxy/write/impersonation grants; independent restricted-credential tests | Only actually executed cluster checks establish installed RBAC; installer privileges remain broader |

## Logs and release boundaries

Ordinary process logs are not tamper-proof audit storage. Forward selected structured events to an operator-controlled logging system with restricted access and retention if stronger records are needed. Do not enable raw evidence/provider-body logging. Configure trusted TLS ingress before enabling HSTS; local HTTP port-forward intentionally omits it. The optional NetworkPolicy example permits broad HTTPS egress and is not a destination allowlist or exfiltration guarantee. CNI enforcement and API/provider routing must be tested in the deployment environment.

See [verification matrix](verification-matrix.md), [application security guide](../security.md), [RBAC template](../../charts/kubeinvestigator/templates/rbac.yaml), [operations](../operations.md) and [security reporting policy](../../SECURITY.md). A private reporting route must be verified by the owner; none is invented here.
