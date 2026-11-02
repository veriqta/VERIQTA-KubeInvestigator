# Archived status — superseded

Historical snapshot preserved for traceability. Pending statements describe that earlier checkpoint, not current support. See [current readiness](../release-readiness.md).

# Current validation summary

The corrected hosted Validate run **41473405003** at **d261de7** passed all ten jobs. [Recorded evidence](../acceptance/2026-11-02-hosted-validation.json) includes native amd64 Ubuntu source **80 tests**, three actual Kubernetes versions/PVC recovery and both native image/runtime scans. The latest local source suite also passed 80 tests. Former local/QEMU records are retained below and in their dated files; native hosted results now supersede the previously unexecuted profiles.

Image records have **no findings detected by the recorded scan**, not proof of no vulnerabilities. The hosted secret gate covered one PR commit. A separate complete-history Gitleaks audit returned six upstream public signing-fingerprint matches, exit 1, each source-verified and [retained without suppressions](../security/findings/2026-11-02-history-secret-review.json). No automated clean-history result is claimed.

Live-model accuracy, managed clouds, WSL2/physical-host profiles, actual staging ingress/TLS/CNI, physical storage failure, independent review and release signing/provenance remain unverified. No paid call, publication, external deployment or assistant merge occurred. Later documentation revision check status must be read from PR #3 rather than inferred from this exact code run.

---

## Historical validation before runtime installation

# Validation evidence — 0.1.0 local working tree

Recorded 2026-11-01 (America/Los_Angeles). The repository remote is verified as `https://github.com/veriqta/VERIQTA-KubeInvestigator.git` and was empty at connection. No commits, pushes, release tags, packages, paid calls, settings changes or external deployments were made.

| Check | Actual result |
| --- | --- |
| Fresh source setup | Pinned requirements installed into a new `.venv-fresh` with Python 3.12.14 on macOS arm64; editable package installation succeeded |
| Component/API/adversarial suite | **50 passed**; one Starlette deprecation warning about httpx TestClient (not a test failure) |
| Ruff lint / format | Passed for src, tests and Python scripts |
| mypy | Passed for 10 application modules |
| Browser integration | Passed login, all three uniquely identified scenario submissions, report completion, keyboard-expandable evidence, downloaded JSON export, linked fresh follow-up, keyboard focus and no horizontal overflow at 390px; no browser page errors |
| Genuine captures | Five PNGs, short WebM screen recording and GIF sequence captured from real UI with MOCK + fixture labels; no live cluster/model representation |
| Uvicorn startup | Served the working interface on 127.0.0.1:8080; no external listener |
| Helm 3.19.0 | Lint passed; rendered six valid YAML documents at target versions 1.35.0, 1.36.0 and 1.37.0; explicit runtime Roles inspected for read-only verbs/resources |
| Example and workflow syntax | Example YAML, Helm JSON schema and workflow YAML parsed; shell scripts pass bash -n |
| Python package | Wheel and sdist built locally with --no-isolation; static UI files included |
| Runtime dependency audit | pip-audit 2.10.1 reported **no known vulnerabilities** in the pinned runtime requirements on this date; advisory coverage is not proof of safety |
| Licence flags | pip-licenses metadata from 73 locally installed distributions (including audit tooling) passed the basic unknown/GPL/proprietary flag check; release still needs upstream notices review |
| Relative links / assets | Local relative-link, SVG XML, nonempty-asset and supplemental credential-pattern checks pass; README browser checks also loaded real remote badges and local images in light/dark/narrow layouts. Exact hosted GitHub rendering remains unverified. |
| Credential/data review | Source pattern checks plus private generated-token exclusion and visual inspection of synthetic captures; not a complete secret-history or OCR audit |

## Unrun acceptance and limitations

- **No Docker daemon, Docker CLI or kind was available.** No container was built or executed; no Helm installation, actual Kubernetes collection, restricted runtime RBAC denial, real correction/follow-up, PVC restart, backup/restore or upgrade/rollback was exercised. `bash scripts/smoke.sh` implements that next acceptance path.
- No paid model call was authorised or made. The OpenAI adapter's HTTP contract, errors and parsing were tested with synthetic HTTP responses. Model quality, real credentials, account capability, latency and cost remain unverified. No live model configuration is claimed tested.
- Linux amd64/arm64 containers, Linux/WSL2 host setup, managed clouds, ingress/TLS and CNI policy enforcement remain unverified. Kubernetes 1.35–1.37 is a target range, not an executed support matrix.
- GitHub Actions, container/dependency scanning there, full gitleaks history scanning, SBOM release workflow and external OpenTelemetry Collector export have not executed. No signature or build provenance was produced. Action commits and the base-image index are now pinned; container execution and signature/provenance checks remain unverified.
- The 50 tests and browser run are specific control evidence, not exhaustive security, accessibility, performance or model-quality guarantees. No benchmark or coverage percentage is fabricated.

The complete release brief is **not yet accepted**. [Requirements](../requirements.md) retains the gaps; [checkpoint](../checkpoint.md) identifies the next executable work. Do not change the README to imply cluster or live-model certification before those checks succeed.

## Follow-on audit evidence

The current suite has 50 passing tests in the clean `.venv-audit` environment, with the same single TestClient deprecation warning. The clean locked setup and application startup were rerun. Helm lint and default/optional hardened templates pass locally; wheel/sdist and chart packaging were rerun. Read-only action tag resolution and official Docker registry manifest verification pinned CI/base-image references without executing an action or container. [audit-results.md](../audit-results.md) records fixes, exact blockers, actual smoke coverage and the implemented/tested/blocked/remaining table. Older 42-test references describe the initial run, not the current total.
