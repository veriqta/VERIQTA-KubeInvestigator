# Security reporting policy

This pre-release has no promised support window or response time. Do not disclose credentials, private cluster data or vulnerability exploit details in public issues.

Report vulnerabilities privately through [GitHub’s Report a vulnerability form](https://github.com/veriqta/VERIQTA-KubeInvestigator/security/advisories/new). Sign in to GitHub if prompted. Private reporting is enabled; do not put exploit details in public issues.

The [security model](docs/security.md) documents shared-team access, restricted RBAC, redaction limits and provider data transfer. Please include affected version, a minimal redacted reproduction and impact through the verified private route. Do not access or test someone else's cluster without authorisation.

## Current reporting setup

VERIQTA LIMITED is the maintaining organisation. On November 3, 2026, an authorised administrator enabled GitHub private vulnerability reporting. The status API returned `enabled: true`, and the public [Advisories page](https://github.com/veriqta/VERIQTA-KubeInvestigator/security/advisories) displayed “Report a vulnerability” linking to the private form. Repository visibility remained public and was not changed. No fabricated report was submitted; end-to-end notification delivery has not been tested.

Repository access inspection listed one administrator account, `veriqta`, and no repository teams. This identifies an eligible administrator, not an appointed security responder or proof of notification delivery. GitHub notifies administrators/security managers subject to watch/security-alert subscriptions and notification preferences; those preferences are not verified. See [GitHub’s notification instructions](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository#configuring-notifications-for-private-vulnerability-reporting).

VERIQTA LIMITED must assign a triage person or team, arrange appropriate access, and verify **Watch → Custom → Security alerts** (or All Activity) and account notification delivery settings. No individual, team or contact address is appointed by this policy. The private intake route is verified; staffed response and notification delivery remain operational setup tasks. See [maintenance responsibilities](docs/maintenance.md) and the [dated verification](docs/acceptance/2026-11-03-private-reporting.json).
