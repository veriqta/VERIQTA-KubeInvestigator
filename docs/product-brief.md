Build VERIQTA KubeInvestigator in my existing GitHub repository named VERIQTA-KubeInvestigator.

Treat this as the complete product brief. Preserve these requirements throughout implementation, and track their completion against evidence.

## 1. Product purpose

VERIQTA KubeInvestigator is an open-source, self-hosted Kubernetes incident investigation service.

It helps engineers investigate application failures by collecting authorised Kubernetes evidence, identifying likely causes, explaining uncertainty, recommending corrective steps, and checking the observed state after an engineer makes a correction.

Intended users include DevOps engineers, SREs, platform engineers, developers, engineering teams, and technical learners.

The application must be reusable independently of VERIQTA. Users run it in their own infrastructure with their own credentials. No VERIQTA account, proprietary VERIQTA backend, or private VERIQTA service is required.

Deliver functioning software, reproducible installation, trustworthy documentation, and an attractive repository that clearly explains the product.

Do not describe the public repository primarily as my portfolio. Its public presentation should focus on the people using it and the problem it solves.

## 2. Working approach

First:

- Inspect the workspace, Git remote, existing files, and applicable repository instructions.
- Confirm whether the connected repository is VERIQTA-KubeInvestigator.
- Preserve existing user changes.
- Do not modify VERIQTA Mentor or another project.
- If the intended repository is unavailable, create an isolated local project directory and report the mismatch without attaching an unrelated remote.
- Read this entire brief before implementation.
- Check current official documentation before choosing dependency versions and Kubernetes APIs.

Create:

- A concise architecture document.
- An implementation plan divided into milestones.
- A requirements checklist linking requirements to code, documentation, and validation.
- A decision log for meaningful architectural tradeoffs.

Then proceed with implementation. Do not stop after producing a plan, README, scaffolding, screenshots, or mock interface.

Make reasonable, reversible decisions autonomously. Ask only when a genuinely blocking decision cannot be resolved from the repository or this brief.

If the work spans sessions, leave an accurate progress checkpoint and the next executable task. Do not claim completion because the current session ended.

## 3. Scope for the first release

Implement complete investigation workflows for:

1. CrashLoopBackOff.
2. ImagePullBackOff.
3. Service selector mismatches.

For each scenario, document:

- What evidence is collected.
- What conclusions that evidence can support.
- Common alternative explanations.
- What the service cannot establish.
- How the user can verify a recommended correction.

CrashLoopBackOff and ImagePullBackOff are observed conditions, not sufficient explanations of an underlying cause. Reports must investigate further where evidence allows.

For example, an image pull failure may suggest an invalid image reference or registry access problem, but the application must not invent registry credentials or claim certainty without evidence.

Initial boundaries:

- One cluster per deployment.
- Explicitly configured namespaces.
- Read-only investigation.
- Manual investigation requests.
- One supported live model provider.
- A documented single-replica deployment profile.
- An authenticated team interface with documented trust assumptions.

Do not add autonomous remediation, arbitrary code execution, multi-cluster control, billing, Kubernetes operators, or unrelated integrations to version one.

Record suitable future features in the roadmap without presenting them as implemented.

## 4. User journey

A first-time user should be able to:

1. Understand the product from the top of the README.
2. See an authentic screenshot and short demonstration.
3. Check prerequisites and supported environments.
4. Choose the sample demonstration or installation against their own cluster.
5. Run configuration and connectivity checks.
6. Open the interface.
7. Select an authorised namespace and optional workload.
8. Describe a problem.
9. Follow investigation progress.
10. Read findings and supporting evidence.
11. Export a report.
12. Correct their workload independently.
13. Run a linked follow-up investigation.
14. See whether the previously observed condition has cleared.
15. Remove the application and demonstration resources using documented commands.

Handle empty states, invalid configuration, insufficient permissions, unavailable providers, and unsupported problems with clear, actionable messages.

## 5. Architecture and implementation

Use:

- Python.
- FastAPI.
- The official Kubernetes Python client.
- Typed request and response schemas.
- A lightweight web interface served with the application where practical.
- A replaceable model-provider adapter.
- A simple persistent storage layer appropriate for the declared deployment profile.

Prefer a maintainable modular application over unnecessary microservices or agent frameworks.

Separate:

- API routes and authentication.
- Authorisation and policy enforcement.
- Kubernetes tools.
- Evidence collection and redaction.
- Investigation orchestration.
- Model-provider integration.
- Report validation.
- Persistence.
- Observability.
- UI presentation.

Account for blocking Kubernetes client calls so they do not block the asynchronous API event loop.

Implement bounded work execution with explicit concurrency limits. Persist investigation state and define what happens when the application restarts mid-investigation.

For a single-replica SQLite implementation, document storage, concurrency, backup, and replica limitations. Do not imply high availability. Use migrations and version the report schema.

Do not introduce a separate database, queue, or frontend framework without a clear reason.

## 6. Investigation workflow

Implement one bounded agent investigation loop.

The agent may choose only explicitly registered tools with validated arguments. Application code must enforce:

- Namespace restrictions.
- Allowed resource types and operations.
- Maximum investigation duration.
- Maximum tool calls and model turns.
- Per-tool timeouts.
- Evidence and log size limits.
- Model input and output limits.
- Concurrency limits.
- Cancellation.

Expose appropriate investigation states, including queued, running, completed, insufficient evidence, failed, cancelled, and interrupted.

Do not repeatedly retry an action without a limit.

Keep Kubernetes observations and deterministic checks distinct from model interpretations.

When the model is unavailable, show an honest failure or explicitly labelled evidence-only result. Do not silently substitute a mock diagnosis.

## 7. Kubernetes tools and permissions

Provide narrowly scoped tools for the resources needed by the supported scenarios, including:

- Pod status and container status.
- Current and previous container logs where permitted.
- Relevant events.
- Services and selectors.
- EndpointSlices.
- Relevant workload status and ownership relationships.

Use current supported APIs. Document any compatibility fallback.

Return selected fields rather than forwarding entire resource manifests. Pod specifications, environment values, commands, annotations, and logs can contain confidential information.

The application service account must not:

- Read Kubernetes Secrets.
- Create, update, patch, or delete cluster workloads.
- Execute commands inside pods.
- Open arbitrary Kubernetes proxy or port-forward operations.
- Impersonate users.
- Access nodes or cluster-wide resources unnecessarily.
- Use wildcard resource permissions.
- Receive cluster-admin.

Generate explicit Roles and RoleBindings in configured target namespaces. Avoid cluster-wide list permissions.

Populate the namespace selector from authorised configuration rather than requiring permission to list every namespace.

Check namespace and resource authorisation on every relevant API request and tool invocation. Never rely solely on what the UI displays or what the model was instructed to do.

Distinguish installation permissions from the runtime service account permissions.

Local demonstrations should also use restricted credentials rather than relying on an administrator kubeconfig.

## 8. Authentication and team access

Support a secure, documented authentication mechanism for shared deployments.

Requirements:

- No default or hard-coded credentials.
- Credentials remain on the server.
- No provider keys embedded in frontend code.
- No credentials in URLs, committed files, screenshots, or logs.
- Secure handling of browser sessions or tokens.
- Appropriate expiry, logout, and invalidation behaviour.
- CSRF protection where cookie authentication requires it.
- Restrictive CORS defaults.
- Server-side request and resource authorisation.
- Protected report, export, cancellation, and verification endpoints.
- Appropriate rate limits.

Document whether users share a trusted team workspace or have individual report isolation. Do not claim enterprise multi-tenancy if it is not implemented.

The local access path must bind or forward to localhost. Inside Kubernetes, the application may listen on the pod interface but should use an internal Service by default.

Ingress must be opt-in, authenticated, and accompanied by TLS instructions. Do not assume the user's cluster already has an ingress controller or certificate manager.

## 9. Data handling and model integration

Support one live provider initially and document the exact tested model configuration.

Use a provider interface so future integrations can be added without rewriting orchestration.

Handle:

- Invalid credentials.
- Provider rate limits.
- Temporary failures.
- Malformed responses.
- Invalid tool calls.
- Token limits.
- Timeouts.
- Unsupported model capabilities.

Keep retries bounded and observable.

Provide a separate mock adapter for development and automated smoke tests. Mock mode must be visibly labelled in the UI, API responses, reports, and captured demonstrations.

Before data reaches a model:

- Minimise collected fields.
- Apply redaction.
- Enforce payload limits.
- Exclude unnecessary environment values, annotations, and full manifests.
- Allow operators to disable log collection.
- Document residual redaction limitations.

Treat cluster content and model output as untrusted data. Embedded instructions must not change policy, expose credentials, select arbitrary destinations, or expand tool access.

Validate evidence references in reports. Reject or flag invented resource references.

Render model output safely. Prevent script execution, unsafe HTML, and malicious links from becoming executable UI content.

Document:

- What stays inside the deployment.
- What is stored.
- What is sent to the provider.
- What may appear in observability systems.
- How to disable optional data collection.
- Retention and deletion behaviour.

No analytics, telemetry export, or external tracking by default.

Mock mode must not require a provider key or contact a model provider. Initial image and dependency downloads may still require internet access; document this accurately.

## 10. Reports and verification

Each investigation report should include:

- Investigation identifier.
- Creation and completion timestamps in UTC.
- Software, provider, and model versions where available.
- Namespace and selected workload.
- User's problem statement.
- Investigation status.
- Observations.
- Evidence identifiers, resource references, and collection timestamps.
- Likely diagnosis.
- Alternative hypotheses.
- Missing or inaccessible evidence.
- Recommended manual next steps.
- Limitations.
- Tool failures or truncated evidence.
- Usage, duration, and estimated cost where available.
- Related follow-up investigation identifiers.

Do not invent confidence percentages. Use a clear qualitative assessment tied to evidence.

Provide JSON and Markdown exports with appropriate authorisation and redaction.

A follow-up investigation must collect fresh evidence. Distinguish “the observed condition is no longer present” from a guarantee that the entire application is healthy.

Do not run arbitrary network probes or shell commands to verify recovery.

## 11. Persistence and lifecycle

Persist investigation state and reports.

Provide:

- Configurable retention.
- Predictable cleanup.
- A maximum storage strategy.
- User-triggered deletion appropriate to the access model.
- Safe schema migrations.
- Backup and restore guidance.
- Clear handling of interrupted jobs.
- Documented behaviour when storage fills.

Do not persist raw logs indefinitely. Document whether redacted evidence is retained and for how long.

Export and deletion endpoints must respect authorisation.

## 12. Interface quality

Create a polished, practical engineering interface.

Include:

- Product identity and version.
- Connection and configuration status.
- Namespace and workload selection.
- Problem submission.
- Investigation progress.
- Investigation history.
- Report detail view.
- Expandable evidence.
- Clear distinction between observations and hypotheses.
- Export and follow-up actions.
- Useful loading, empty, failure, and cancelled states.
- Clear mock-mode labelling.

Make the interface usable with keyboard navigation, readable contrast, labelled controls, and status indicators that do not rely on colour alone.

Use responsive layouts. A complex evidence view may work best on desktop, but essential content should remain usable on smaller screens.

Avoid a generic chat-only interface if structured investigation views communicate the work more clearly.

Do not add decorative charts or artificial statistics.

## 13. Installation and packaging

Provide:

- A non-root Docker image.
- A Helm chart.
- A reproducible kind-based local demonstration.
- A source-development setup.
- An example environment file without secrets.
- Helm example values and values-schema validation.
- Setup diagnostics.
- Setup and cleanup scripts.
- Versioned package and release preparation.

Use locked dependencies and a documented update strategy.

Use appropriate container hardening, including dropped capabilities, no privilege escalation, a read-only root filesystem where practical, and explicit writable storage.

Do not mount the Docker socket or host filesystem into the application.

For Kubernetes, include:

- Resource requests and limits.
- Startup, readiness, and liveness checks.
- Service account configuration.
- Scoped RBAC.
- Persistent storage configuration.
- Internal Service.
- Optional ingress.
- Configurable security context.
- Optional NetworkPolicy examples with limitations explained.

External dependencies such as ingress controllers, StorageClasses, DNS, and network-policy enforcement must be declared.

Support users supplying an existing Secret or suitable secret-management integration without committing actual credentials.

Do not put live API keys directly into example Helm values.

## 14. Portability and support claims

Aim for broad reuse through explicit compatibility.

Define and test a modest Kubernetes version range at implementation time. Derive the selected versions from current official support information.

Document separately:

- Tested Kubernetes versions.
- Tested container architectures.
- Tested operating-system setup paths.
- Model configuration.
- Helm and tooling prerequisites.
- Storage requirements.
- Minimum and measured recommended resources.
- Network and registry access requirements.

Target Linux amd64 and arm64 container images where feasible. Distinguish images that were built from images actually executed and tested.

Provide setup guidance for Linux, macOS, and Windows through WSL2 where applicable. Label untested paths honestly.

Do not claim EKS, AKS, GKE, OpenShift, air-gapped, GPU, or enterprise compatibility without appropriate validation.

Document registry mirroring and restricted-network considerations without claiming offline live-model support.

## 15. Sample workloads

Provide disposable demonstration workloads for all three supported conditions.

Use a dedicated, clearly named demonstration namespace and preferably a dedicated kind cluster.

For every example include:

- Purpose.
- Resources created.
- Expected failure.
- Expected evidence.
- Investigation request.
- Expected report characteristics.
- Manual correction.
- Follow-up verification.
- Cleanup.

Example scripts must check the active Kubernetes context and refuse accidental execution against an unrelated cluster.

Only sample setup, correction, and cleanup scripts may modify sample workloads. The investigation application remains read-only.

Use bounded waits rather than long fixed sleeps. Handle image-pull backoff and event timing reliably.

Never delete unrelated namespaces, workloads, volumes, or clusters during cleanup.

## 16. Operational observability

Provide structured logs, request identifiers, and investigation identifiers.

Measure useful operational signals such as:

- Investigation success and failure counts.
- Queue depth and concurrency.
- Investigation duration.
- Tool latency and errors.
- Provider failures.
- Token usage.
- Estimated model costs.
- Budget exhaustion.
- Storage cleanup failures.

Avoid high-cardinality labels and sensitive values in metrics.

Provide basic metrics and optional OpenTelemetry export. Optional monitoring integrations must not be required for a basic installation.

If providing a dashboard, make it functional, provision it reproducibly, and use real captured measurements.

Cost reporting must identify pricing assumptions and dates. If reliable pricing or usage is unavailable, say so rather than displaying invented precision.

## 17. Testing strategy

Implement meaningful tests at several levels.

Unit and component tests:

- Input and configuration validation.
- Namespace and resource policy.
- Evidence filtering and redaction.
- Agent step and time limits.
- Provider parsing and failure handling.
- Evidence-reference validation.
- Report generation and exports.
- Retention and deletion.
- Authentication and authorisation.

Integration tests:

- Restricted Kubernetes access.
- Actual Kubernetes resource collection.
- Persistent report lifecycle.
- Application restart behaviour.
- API and UI investigation flow.

Adversarial cases:

- Unauthorised namespace requests.
- Guessing another user's report identifier where individual isolation applies.
- Injection instructions inside logs or annotations.
- Malicious HTML and Markdown in evidence.
- Invalid model tool calls.
- Oversized logs and responses.
- Attempted write operations.
- Exfiltration requests.
- Missing permissions.
- Provider and tool timeouts.

Keep safety claims proportionate. Passing injection tests is evidence of specific controls, not proof that all prompt injection is solved.

## 18. End-to-end acceptance and evaluations

Create an automated smoke test that:

1. Creates a fresh, disposable kind cluster.
2. Builds or loads the application image.
3. Installs the Helm chart.
4. Creates restricted credentials and sample failures.
5. Runs investigations using the mock provider.
6. Checks report structure and evidence collection.
7. Confirms forbidden access is denied.
8. Restarts the application and checks retained records.
9. Performs a sample correction outside the application.
10. Runs fresh verification.
11. Cleans up only resources created by the test.

Mock tests validate wiring, enforcement, and lifecycle. They do not prove live-model diagnostic quality.

Provide a separate opt-in live evaluation command using user-supplied credentials.

Include supported incidents, healthy workloads, ambiguous failures, and unsupported problems in the live evaluation set.

Define expected evidence and acceptable outcomes. Measure incorrect diagnoses and unsupported claims as well as successful cases.

Store evaluation metadata, model configuration, prompts or prompt versions, test conditions, and appropriately redacted results.

Do not fabricate benchmarks, coverage, provider costs, or test passes.

## 19. CI and release preparation

Implement GitHub Actions workflows for relevant checks:

- Formatting, linting, and type checking.
- Unit and integration tests.
- Container build.
- Helm linting and template checks.
- Disposable-cluster smoke tests.
- Documentation and internal-link checks.
- Secret scanning.
- Dependency and container vulnerability scanning.
- Licence checks.
- Asset validation where practical.

Use least-privilege workflow permissions. Protect secrets from untrusted pull requests. Do not execute untrusted contributions in privileged release contexts.

Prepare release automation for:

- Versioned container images.
- Versioned Helm packages.
- Release notes and changelog.
- Checksums.
- Software bill of materials.
- Build provenance and signing where feasible.

Separate validation from publishing. Default development workflows must not unexpectedly publish packages.

Do not create a release tag, publish an image, or claim that a package exists before publication is authorised and succeeds.

Until releases exist, make source installation the working documented path. Do not place nonexistent release commands in the main quick start.

## 20. Repository structure

Use a clear structure with a small number of meaningful top-level directories.

A suitable starting layout is:

- Application source.
- Automated tests.
- Helm chart.
- Examples.
- Scripts.
- Documentation.
- Evaluations.
- GitHub workflows and templates.

Use conventional names such as src/, tests/, charts/, examples/, scripts/, docs/, and evals/ where appropriate.

Keep required root files easy to find:

- README.md
- LICENSE
- CONTRIBUTING.md
- SECURITY.md
- CODE_OF_CONDUCT.md
- CHANGELOG.md
- ROADMAP.md
- Dependency configuration and lockfile
- Dockerfile
- Makefile or equivalent task runner

Do not create empty directories, placeholder-only documents, duplicate guides, or unnecessary layers.

## 21. README narrative and information architecture

The README is the product's front door. A visitor should understand what it does before scrolling through implementation details.

Write professional, public-facing prose with concrete examples. Avoid inflated claims, generic AI marketing, and statements about how impressive the portfolio is.

Use this narrative order:

1. Product banner, logo, and name.
2. A precise one-sentence description.
3. Small set of genuine status badges.
4. Navigation links to quick start, demonstration, documentation, security, and contributing.
5. Authentic product screenshot or demo preview.
6. The engineering problem.
7. A concrete investigation story.
8. Implemented capabilities and explicit scope.
9. Quick start.
10. How investigation works.
11. Architecture and permission boundaries.
12. Example report.
13. Deployment options and compatibility.
14. Security, data flow, and model-provider costs.
15. Evaluation evidence and limitations.
16. Documentation index.
17. Roadmap.
18. Contributing, support, licence, and acknowledgements.

The example story should walk through:

- An unavailable application.
- Evidence gathered from its Service and selected pods.
- The observed selector mismatch.
- A recommended manual correction.
- A fresh verification after the engineer corrects it.

Use text and genuine screenshots to explain each meaningful stage. Do not claim that this workflow is unique to this project.

Keep detailed configuration and operations material in linked guides. Make the README comprehensive enough to orient users without turning it into an unstructured manual.

Put essential requirements and external model dependencies near the quick start.

Explain that open-source software can still require paid model access and infrastructure.

## 22. Visual identity and repository assets

The repository must communicate a coherent visual story beyond an SVG banner.

Create or prepare:

1. An original VERIQTA KubeInvestigator project mark.
2. A clean README hero banner.
3. Light and dark compatible logo variants.
4. A GitHub social preview image.
5. A real interface overview screenshot.
6. A real evidence-detail screenshot.
7. A real diagnosis/report screenshot.
8. A real follow-up verification screenshot.
9. A short investigation demo GIF with a static fallback.
10. A full short demo video when capture tools are available.
11. An architecture diagram.
12. An investigation lifecycle diagram.
13. A data-flow and trust-boundary diagram.
14. A small technology-logo strip using only implemented technologies.

Use existing authorised VERIQTA brand assets if present. Do not invent an official company logo or claim a provisional project palette is the established corporate identity.

If brand assets are absent, create an original project wordmark and document a provisional, restrained palette that can be updated later.

Prefer clarity, readable typography, strong spacing, and consistent visual treatment. Avoid excessive badges, giant logo walls, decorative stock imagery, or unrelated AI illustrations.

Technology logos must come from appropriate sources, respect applicable brand guidance, and have attribution or licence records. Inclusion must not imply partnership or endorsement.

Do not fabricate customer logos, adopter lists, testimonials, certifications, or CNCF affiliation.

Do not use AI-generated images to represent exact architecture, actual product screenshots, evaluation results, or live demonstrations.

Code-native SVG is suitable for original marks and precise diagrams. Use screenshots from the functioning application for product evidence.

## 23. Asset documentation and verification

Organise visual assets under docs/assets/ with meaningful subdirectories for brand, screenshots, diagrams, demos, and third-party marks where helpful.

Include:

- Editable source for diagrams and original graphics.
- GitHub-compatible rendered versions.
- Alt text and explanatory captions.
- Source attribution.
- Applicable licences.
- Screenshot capture instructions.
- Demo recording instructions.
- Optimisation guidance and reasonable file sizes.

Create an asset inventory recording:

- Filename.
- Purpose.
- Source or creator.
- Licence.
- Whether it depicts mock or live mode.
- Application version or commit used for capture.
- How to regenerate it.

Use a resettable sample dataset for captures. Remove tokens, private infrastructure names, user information, and sensitive logs.

Screenshots must show real working UI states. Mock-backed screenshots are acceptable when visibly labelled.

Do not display claimed live investigations when a mocked provider was used.

Check rendering in light and dark GitHub themes and on narrow screens. Keep important information available as text, not only inside images.

Use relative asset paths and verify links.

If recording or image tools are unavailable, complete the working application and capture scripts, then report exactly which assets remain uncaptured. Never substitute blank files or fake visuals.

## 24. User and operator documentation

Provide a documentation index and focused guides covering:

- What the product does.
- Supported scenarios and limitations.
- Local quick start.
- Helm installation.
- Authentication and shared deployment.
- Provider configuration.
- Kubernetes RBAC.
- Configuration reference with defaults.
- Architecture and investigation lifecycle.
- API usage and report schemas.
- Security model and threat boundaries.
- Data flow, redaction, retention, and deletion.
- Storage, backup, and restore.
- Monitoring and troubleshooting.
- Evaluation methodology.
- Development and contribution workflow.
- Asset regeneration.
- Upgrade, rollback, and uninstall.
- Release preparation.

Every installation guide must include:

- Prerequisites.
- Tested versions.
- Permissions required.
- Commands in execution order.
- Expected results.
- Verification.
- Common failures and remedies.
- Cleanup.

Use copyable commands. Explain placeholders consistently.

Do not assume an existing registry package, StorageClass, ingress controller, provider key, or Kubernetes cluster without stating it.

Provide a troubleshooting table linking symptoms to checks and remedies.

## 25. Open-source community and maintenance

Use Apache-2.0 licensing and preserve any required upstream notices.

Do not invent copyright holders, maintainer names, email addresses, legal claims, or support guarantees.

Include:

- Contribution instructions.
- Development setup.
- Testing expectations.
- Bug and feature-request templates.
- A pull-request template.
- A code of conduct.
- A changelog.
- A realistic roadmap.
- A security reporting policy.
- Dependency maintenance guidance.

Do not direct people to disclose vulnerabilities publicly.

If private GitHub vulnerability reporting is not enabled, report this as an owner setup task and do not pretend a private reporting channel exists.

Explain code and brand licensing separately. Commercial use of open-source code does not imply VERIQTA endorsement.

Do not add mandatory contributor agreements, external accounts, or sign-up requirements without a concrete reason.

## 26. Research and originality

Review the current public documentation and repository presentation of K8sGPT, HolmesGPT, and the OpenTelemetry Demo.

Use them to understand effective installation, examples, documentation, contribution, and presentation patterns.

Record useful references in the design notes.

Do not copy their identity, images, text, or code without appropriate permission, licence compliance, and attribution.

Describe this project's focused design choices accurately. Do not claim superiority, uniqueness, or enterprise readiness without evidence.

## 27. Milestones

Work through these milestones, adapting order where dependencies require it:

1. Repository inspection, architecture, support assumptions, and requirements checklist.
2. Restricted Kubernetes tools and deterministic evidence collection.
3. Bounded investigation loop, mock adapter, and live-provider implementation.
4. Authentication, persistence, API, reports, and usable interface.
5. Helm packaging, local demonstration, and sample failures.
6. Security, failure handling, operational signals, and evaluation suite.
7. CI and release preparation.
8. Complete documentation, visual identity, genuine captures, and README narrative.
9. Fresh-environment verification and final audit.

Run relevant checks after each milestone.

Keep implemented, tested, unverified, and planned features distinct.

Resolve failures rather than hiding them or weakening tests to obtain a passing result.

## 28. Working boundaries

You may implement files, run local tests, build containers, and use a dedicated disposable local cluster when the environment supports these actions.

Do not:

- Access an existing production cluster.
- Provision paid infrastructure.
- Make paid model calls.
- Create provider accounts or API keys.
- Change unrelated repositories.
- Send messages to other people.
- Change GitHub repository settings.
- Publish packages or documentation externally.
- Create release tags.
- Push to GitHub.

Those external actions require my explicit instruction.

Prepare scripts and workflows for later use without triggering external publishing.

Do not stop for approval on ordinary local implementation work already covered by this brief.

## 29. Completion criteria

Before claiming the implementation is complete, verify:

- The application starts from a fresh documented setup.
- The Helm chart installs in the tested environment.
- Setup diagnostics identify common configuration problems.
- Authentication works.
- Namespace restrictions are enforced.
- Runtime Kubernetes permissions remain read-only.
- All three sample incidents can be investigated through the UI and API.
- Evidence can be inspected.
- Reports can be exported.
- Follow-up investigations use fresh evidence.
- Persistence and retention work.
- Failure states are handled honestly.
- Mock mode is clearly labelled.
- Secret and sensitive-data checks pass for tracked files and visual captures.
- Documentation commands and relative links work.
- README visuals render correctly.
- No package, release, integration, test result, adopter, or supported environment is falsely claimed.

Any live-provider, multi-architecture, cloud, or external-publishing checks that could not be run must remain explicitly unverified.

## 30. Final handoff

Finish with:

1. What was implemented.
2. What was tested and the actual results.
3. Supported and unverified environments.
4. Remaining limitations and blockers.
5. Exact commands for the local demonstration.
6. Exact commands for deployment against an authorised cluster.
7. Optional live-model evaluation instructions and expected costs.
8. Upgrade, rollback, and cleanup commands.
9. Documentation and visual-asset locations.
10. Any GitHub owner setup tasks.
11. Whether anything was committed, pushed, published, or deployed externally.
12. A recommendation for the next release based on observed gaps.

The goal is a useful, understandable, maintainable open-source product that engineers can evaluate and deploy within a clearly documented support range.