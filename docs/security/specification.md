This security and release-readiness specification supplements the original VERIQTA-KubeInvestigator product brief.

Audit the existing implementation first. Preserve working functionality, identify gaps, and implement the missing requirements. Do not restart the project unnecessarily or mark requirements complete based only on documentation.

Security is part of the application, deployment, development pipeline, and maintenance process.

## 1. Threat model and security boundaries

Create docs/security/threat-model.md describing:

- Assets requiring protection.
- Users and administrator privileges.
- Kubernetes access.
- Browser, API, storage, model-provider, and CI boundaries.
- Trusted and untrusted inputs.
- Possible abuse paths.
- Implemented controls.
- Residual risks and unsupported deployment patterns.

Explicitly consider a compromised user account, malicious workload logs, manipulated model responses, stolen provider credentials, unauthorised report access, and compromised dependencies.

Document that read-only Kubernetes access can still expose confidential information.

Keep these boundaries explicit:

- One cluster per deployment.
- Configured namespaces only.
- No automated remediation.
- No arbitrary shell execution.
- No claim of enterprise multi-tenancy unless implemented and tested.
- No claim that prompt injection is completely solved.

## 2. Authentication and authorisation

Audit every API route, including reports, exports, deletion, cancellation, verification, configuration, and operational endpoints.

Require server-side authorisation for every sensitive operation.

Implement and test:

- Secure credential handling.
- Session expiry and logout invalidation.
- Brute-force protection and rate limiting.
- CSRF protection where applicable.
- Restrictive CORS.
- Secure cookie settings for HTTPS deployments.
- Protection against report identifier guessing.
- Consistent access rules for UI and API.
- Safe treatment of authentication failures.
- No credentials or tokens in URLs.

Use established authentication libraries rather than inventing cryptography.

If local username/password authentication exists, use an appropriate password-hashing algorithm and secure account provisioning. If using external identity, validate issuer, audience, signature, expiry, and relevant claims.

Clearly document the supported identity model. Do not treat a shared token as individual user isolation.

Do not trust identity headers supplied by arbitrary clients. Any reverse-proxy authentication mode must require explicit configuration and a documented trusted-proxy boundary.

## 3. Kubernetes permission enforcement

Audit the generated Helm permissions and the actual client operations.

Use exact resources and verbs. Avoid wildcard permissions and unnecessary cluster-scoped access.

Do not grant access to:

- Kubernetes Secrets.
- Pod exec or attach.
- Port-forward or proxy subresources.
- Node APIs.
- Workload mutation.
- Impersonation.
- RBAC modification.
- Arbitrary custom resources.

Do not read ConfigMaps or complete workload specifications unless a supported investigation explicitly requires the information and collection is appropriately minimised.

Check configured namespace restrictions on every request and tool invocation.

Installation credentials and runtime credentials must remain separate. Explain the privileges needed to install Roles and RoleBindings.

Add real-cluster negative tests proving forbidden operations fail through Kubernetes RBAC, independently of application policy.

## 4. Sensitive evidence handling

Implement an explicit allowlist of fields collected from Kubernetes resources.

Exclude unnecessary:

- Environment values.
- Command arguments.
- Annotations.
- Full manifests.
- Credentials.
- Tokens.
- Connection strings.
- Personal information.

Make container-log collection configurable and document its risks.

Apply redaction before model submission, persistence, export, and diagnostic logging, as appropriate.

Test redaction using representative secrets and multiline values. Document that pattern-based redaction cannot guarantee removal of every confidential value.

Cap log lines, bytes, time ranges, resource counts, and total evidence size.

Do not log raw provider requests or full evidence payloads by default.

## 5. Agent and model security

Treat user prompts, cluster content, tool results, and model output as untrusted.

Enforce policy outside the model:

- Registered tools only.
- Strict argument schemas.
- Namespace and resource checks.
- Per-tool and total investigation budgets.
- Bounded retries.
- Concurrency limits.
- Maximum context and output sizes.
- Cancellation.
- No model-selected arbitrary URLs, files, commands, or credentials.

A model request must not grant permissions.

Do not expose hidden credentials, private configuration, or authentication tokens in prompts.

Validate evidence references and distinguish observations from hypotheses. Unsupported claims must be flagged or rejected rather than silently accepted.

Test malicious instructions inside logs, events, labels, annotations, and error messages.

Do not treat content filtering or a system prompt as the sole security boundary.

## 6. Outbound connections and SSRF

Prevent users and models from directing the server to arbitrary network destinations.

Provider endpoints must be administrator-controlled configuration. Do not expose an unrestricted provider-URL field to ordinary users.

Validate configured destinations and document proxy, private-endpoint, and custom-certificate behaviour.

Use bounded network timeouts and response sizes. Handle redirects safely.

Do not disable TLS certificate verification to make connectivity tests pass.

Do not add arbitrary URL fetching to version one.

## 7. Browser and API protection

Implement and test appropriate protections against:

- Cross-site scripting.
- Unsafe Markdown or HTML rendering.
- SQL injection.
- Path traversal.
- Command injection.
- Unauthorised object access.
- Oversized requests.
- Request flooding.
- Sensitive error disclosure.
- Unsafe file exports.

Escape untrusted content and use parameterised database operations.

Apply an appropriate Content Security Policy and relevant browser security headers.

Restrict framing where appropriate. Apply HSTS only in a correctly configured HTTPS deployment.

Protect documentation and metrics endpoints according to the deployment model.

Do not expose stack traces, credentials, provider payloads, or internal filesystem paths in public error responses.

## 8. Resource exhaustion and spending controls

Implement limits for:

- Requests per user or trusted workspace.
- Queued investigations.
- Concurrent investigations.
- Model turns.
- Tool calls.
- Investigation duration.
- Evidence volume.
- Model output.
- Report storage.
- Export size.

Prevent unbounded background tasks and retry storms.

Provide usage reporting and configurable token or request budgets. Explain that application estimates cannot guarantee the provider's final bill.

Do not claim that an approximate cost counter is a hard provider-side spending cap.

Handle provider rate limits and exhausted budgets with clear user messages.

## 9. Storage and report lifecycle

Protect investigation records, report files, database files, and backups through appropriate permissions.

Implement:

- Schema migrations.
- Configurable retention.
- Predictable cleanup.
- Safe report deletion.
- Disk-space handling.
- Backup and restore verification.
- Interrupted-job recovery.
- Authorised exports.

Document encryption responsibilities. Do not claim encryption at rest unless the application or deployment actually provides it.

Explain that deleting an active report may not remove previously created backups or external model-provider records.

Document single-replica limitations if using SQLite. Prevent unsupported replica settings from creating a misleading deployment.

Do not permit report names or identifiers to become arbitrary filesystem paths.

## 10. Container and cluster hardening

Run as a non-root user with:

- No privileged mode.
- No privilege escalation.
- Dropped Linux capabilities.
- Appropriate seccomp settings.
- Read-only root filesystem where practical.
- Explicit writable volumes.
- Resource requests and limits.
- Appropriate service-account token handling.

Do not mount the Docker socket, host filesystem, or administrator kubeconfig into the application.

Use an internal Service by default. Ingress must be opt-in.

Provide documented TLS configuration without assuming an ingress controller or certificate manager exists.

Provide NetworkPolicy examples and explain that enforcement depends on the cluster network implementation.

Document ingress and egress requirements, including DNS, Kubernetes API access, and model-provider access. Do not advertise a restrictive policy that silently allows all traffic.

## 11. Dependency and software supply-chain security

Use locked dependencies and repeatable builds.

Implement:

- Dependency scanning.
- Container scanning.
- Secret scanning.
- Licence checking.
- SBOM generation.
- Versioned release artifacts.
- Checksums.
- Build provenance and signing where supported.
- A documented dependency-update process.

Pin CI actions to immutable references where practical.

Keep GitHub Actions permissions minimal. Do not expose credentials to untrusted pull requests or use privileged workflow patterns that execute contributor code unsafely.

Do not hide unresolved high-impact findings. Record affected versions, exposure, mitigation, and remediation status.

Do not suppress scanner findings simply to make the workflow green.

## 12. Security audit records

Record security-relevant events such as:

- Authentication failures.
- Denied namespace or report access.
- Investigation creation and cancellation.
- Report export and deletion.
- Budget exhaustion.
- Security-relevant configuration failures.

Include timestamps and correlation identifiers without recording secrets or raw evidence.

Document that ordinary application logs are not tamper-proof audit storage. Provide optional forwarding guidance if stronger retention is needed.

## 13. Secure defaults and configuration validation

Fail clearly when mandatory configuration is absent or invalid.

Do not start a shared deployment with:

- Default credentials.
- An empty signing secret.
- Authentication silently disabled.
- Wildcard CORS.
- Unrestricted namespaces.
- TLS verification disabled.
- Unknown operational mode.

Clearly distinguish local demonstration, mock-provider testing, and live investigation.

Do not silently fall back from live mode to mock mode.

Generate example configuration from the real configuration schema where practical so defaults and documentation remain aligned.

## 14. Reliability requirements that still need verification

Beyond security, verify:

- Investigation cancellation stops further work.
- Graceful shutdown handles active requests.
- Restarted investigations are marked or recovered accurately.
- Queue and concurrency limits work under load.
- Repeated verification uses fresh evidence.
- Data truncation is visible.
- Kubernetes API failures do not crash the application.
- Provider outages do not create retry storms.
- Full storage produces a clear failure.
- Backup restoration preserves usable reports.
- Upgrade and rollback instructions account for database schema changes.
- Cleanup removes only project-owned resources.

Use realistic failure injection in disposable environments.

## 15. Public-facing security documentation

Provide:

- SECURITY.md.
- Threat model.
- Kubernetes permissions reference.
- Authentication guide.
- Data-flow and external-provider disclosure.
- Redaction and retention guide.
- Secure deployment checklist.
- Supported-version and vulnerability-handling policy.
- Backup and recovery instructions.

Explain who should deploy the product, what access it receives, and which decisions remain the operator's responsibility.

Do not invent security certifications, compliance status, penetration-test results, private reporting channels, or response-time guarantees.

If GitHub private vulnerability reporting needs to be enabled, identify it as an owner setup task. Do not direct users to disclose vulnerabilities publicly.

## 16. Testing evidence

Maintain a security verification matrix containing:

- Requirement.
- Threat addressed.
- Implemented control.
- Relevant files.
- Test command.
- Actual result.
- Environment.
- Remaining limitation.

Separate:

1. Static analysis.
2. Mock-based tests.
3. Real-cluster tests.
4. Browser tests.
5. Live-model evaluations.
6. External review.

Passing mock tests does not prove Kubernetes RBAC, cluster installation, live-model accuracy, or protection against every attack.

Never describe self-review and automated scanning as an independent security audit.

## 17. Historical execution-environment requirement

The initial environment lacked Docker, kind and kubectl. This blocker is resolved in the recorded acceptance evidence; the original fallback requirements below remain relevant to unsupported execution environments.

Determine whether this environment can support an actual container runtime and disposable kind cluster.

If it can, install the required tooling using supported methods and run the complete smoke test.

If it cannot, prepare a GitHub Actions workflow and exact local instructions for running the tests in a suitable environment. Do not bypass environment restrictions.

Do not keep retrying a command whose prerequisites are known to be absent.

Do not mark cluster acceptance complete until the tests actually execute successfully.

## 18. Documentation and visual honesty

Preserve the original requirements for the descriptive README, project identity, architecture diagrams, data-flow diagrams, screenshots, demo, and asset inventory.

Ensure security diagrams match the implementation.

Use genuine screenshots. Label mock-backed examples visibly.

Do not put private hostnames, credentials, authentication tokens, student information, or confidential logs in screenshots or demonstrations.

Show security boundaries in the documentation without overwhelming the main user journey.

Keep public claims aligned with the current release and actual test results.

## 19. Maintainable support and release readiness

Include:

- A compatibility matrix.
- A known-limitations list.
- A reproducible bug-report template.
- A diagnostic command that avoids collecting credentials.
- A dependency maintenance process.
- Release notes describing breaking changes.
- A documented supported deployment profile.
- Clear installation, verification, upgrade, rollback, and uninstall instructions.

Do not promise universal compatibility or uninterrupted operation.

Document which Kubernetes versions, architectures, model configurations, and operating-system setup paths were actually tested.

## 20. Implementation boundaries and final report

Continue all ordinary local implementation and testing already authorised.

Do not make paid model calls, provision paid infrastructure, access production clusters, push to GitHub, trigger external workflows, publish packages, or change repository settings without explicit repository-administrator authorisation.

Finish with:

- Changes implemented.
- Tests executed and actual results.
- Outstanding vulnerabilities or limitations.
- Requirements still blocked by the environment.
- Exact commands for the next verification step.
- Owner actions required before public release.
- A clear distinction between implemented, locally tested, cluster-tested, and live-model-tested functionality.

Do not call the project fully secure, production-ready, or fully validated merely because a checklist or automated test suite passes.