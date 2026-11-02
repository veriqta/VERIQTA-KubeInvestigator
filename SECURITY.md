# Security reporting policy

This pre-release has no promised support window or response time. Do not disclose credentials, private cluster data or vulnerability exploit details in public issues.

Use GitHub's private vulnerability reporting only if the repository Security tab offers “Report a vulnerability”. Its enablement has not been verified, and no private channel is claimed to exist. Owner setup task: enable private vulnerability reporting or publish a verified private contact before accepting security reports. Until then, withhold sensitive details and request a private reporting route without describing the exploit publicly.

The [security model](docs/security.md) documents shared-team access, restricted RBAC, redaction limits and provider data transfer. Please include affected version, a minimal redacted reproduction and impact through the verified private route. Do not access or test someone else's cluster without authorisation.

On 2026-11-02 the repository was private and the private-reporting status API returned HTTP 404, so no functioning public reporting route was verified. Before public distribution, an administrator must either provide a verified private contact or, after an authorised visibility change, enable **Settings → Security and quality → Advanced Security → Private vulnerability reporting → Enable** and verify that the Security/Advisories page offers “Report a vulnerability”. GitHub documents this feature for public repositories. See [GitHub's configuration instructions](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository). Do not send exploit details to a public issue while this remains unresolved.
