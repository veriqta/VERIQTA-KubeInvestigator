# Security reporting policy

This pre-release has no promised support window or response time. Do not disclose credentials, private cluster data or vulnerability exploit details in public issues.

Use GitHub's private vulnerability reporting only if the repository Security tab offers “Report a vulnerability”. It is currently disabled, and no private channel is claimed to exist. Owner setup task: enable private vulnerability reporting or publish a verified private contact before accepting security reports. Until then, withhold sensitive details and request a private reporting route without describing the exploit publicly.

The [security model](docs/security.md) documents shared-team access, restricted RBAC, redaction limits and provider data transfer. Please include affected version, a minimal redacted reproduction and impact through the verified private route. Do not access or test someone else's cluster without authorisation.

## Current reporting setup

VERIQTA LIMITED is the maintaining organisation. On November 3, 2026, GitHub reported the repository as public and the private-vulnerability-reporting API returned `enabled: false`. The earlier HTTP 404 observations remain historical evidence; the current response establishes that reporting is disabled. No repository setting or visibility was changed during this inspection.

Recommended setup: enable GitHub private vulnerability reporting for this repository. An owner or administrator must approve and enable **Settings → Security and quality → Advanced Security → Private vulnerability reporting → Enable**, then verify the Security/Advisories “Report a vulnerability” entry and an API response of `enabled: true`. See [GitHub’s configuration instructions](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository). This requires no visibility change. Do not submit a fabricated vulnerability to test delivery.

VERIQTA LIMITED must designate a triage person or team with the required repository access and verify its Security alerts subscriptions and notification preferences. Until enablement and responder coverage are verified, no functioning private intake is claimed. A separately approved, access-controlled reporting portal or verified private contact is an alternative; no such destination has been supplied and no contact address is invented here. See [maintenance responsibilities](docs/maintenance.md).
