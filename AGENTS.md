# Repository collaboration

- Continue meaningful completed milestones on `codex/kubeinvestigator-development` and update its existing pull request to `main` with actual checks and remaining limitations. Commit and push those milestones; do not rewrite shared history.
- Do not merge, publish releases/packages, or deploy to external environments without separate user authorisation. Push/PR validation may build and exercise disposable local-to-runner kind clusters; it must not publish images or deploy externally.
- Keep credentials, private logs/data, databases, virtual environments, caches and build artifacts out of Git. Review untracked/ignored files before delivery; preserve reproducibility through the canonical source, lockfiles and documented build/test commands.
- Use the patched source interpreter and `make preflight test check VENV=.venv-source` as applicable. Keep native hardware, emulated execution, hosted CI and live-model results distinct. Never claim an unexecuted check passed or a recorded scan proves absence of vulnerabilities.
- Paid model calls and production-cluster access require explicit authorisation. Fixture/mock checks do not establish live-model diagnostic accuracy.
