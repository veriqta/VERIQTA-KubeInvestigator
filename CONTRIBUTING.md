# Contributing

Contributions should improve evidence quality, reproducibility or usability within the read-only scope. Discuss larger changes in a feature issue first; no external account beyond the repository host or contributor agreement is required.

Use Python 3.12+, `make setup PYTHON=python3.12`, `make test` and `make check`. See [installation](docs/installation.md) to run the UI on localhost. Do not use a production kubeconfig. Start with fixture/mock mode; run cluster acceptance only in the disposable named kind cluster. Live evaluations are opt-in and paid. Add meaningful tests for policy, evidence interpretation and failure handling; do not weaken bounds to pass tests. Check keyboard/mobile behaviour after UI changes. Capture real app states and label mock mode.

Submit a PR describing the user-visible problem, implementation and actual validation. Keep secrets, private logs, personal infrastructure names and provider keys out of commits and test fixtures. Report vulnerabilities privately; see [security policy](SECURITY.md). Do not put exploit details in a public issue.

Dependencies are pinned in requirements.lock and requirements-dev.lock. Update with Python 3.12 using `pip-compile pyproject.toml --output-file requirements.lock` and `pip-compile pyproject.toml --extra dev --output-file requirements-dev.lock`; preserve reviewed build tooling pins needed for --no-build-isolation. Review upstream changelogs, licences, CVEs and API changes, run tests/chart checks/cluster matrix, and record changes. CI scanners are evidence of specific checks, not a security guarantee. Base image digests and action SHA pinning should be reviewed before a published release.

## Current development delivery

Completed milestones are committed and pushed to `codex/kubeinvestigator-development`, with the existing pull request targeting `main` updated as work progresses. Keep commits logically grouped and preserve shared history. The initial empty repository requires only an empty initialization commit on main; all project implementation is reviewed through the development PR. Automatic validation remains enabled, including disposable kind acceptance. Release-artifact preparation is manual and performs no publication. Merging, release/package publication and external deployment require separate owner authorisation.

Use a GitHub noreply commit address to avoid exposing a private email. Review the complete staged tree, untracked files and ignored directories before pushing. The dated evidence/scan summaries and genuine mock-labelled assets are intentional project artifacts; local runtime archives, environments, private captures and caches are excluded. Historical evidence describes earlier execution boundaries; current hosted check outcomes belong to the pull request and must not be inferred from local runs.
