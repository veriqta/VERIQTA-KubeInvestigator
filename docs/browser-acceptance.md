# Real-cluster browser acceptance

The recorded [browser run](acceptance/2026-11-02-cluster-browser-mock.json) exercised the installed Helm application on disposable local kind Kubernetes 1.35.8 / Linux arm64. The application source was unchanged at the recorded revision; the manifest records the added harness hash. Evidence came from real Kubernetes resources; all interpretations used the deterministic **MOCK provider**. The workloads were disposable samples, not production data. This does not validate live-model accuracy.

Browser assertions covered unauthenticated denial, login, submissions for all three conditions, evidence expansion, JSON/Markdown downloads, exact report retention after deployment restart, expired sessions, three corrections through external installer scripts, newer evidence timestamps in linked follow-ups and logout invalidation. The wrapper verified deletion of its owned cluster. No provider credentials or paid requests were involved.

![Actual report with real Kubernetes evidence and explicitly labelled mock interpretation](assets/cluster/evidence.png)

![Fresh follow-up after the external Service correction](assets/cluster/followup.png)

[Browser recording](assets/cluster/investigation.webm) · [Workspace screenshot](assets/cluster/overview.png) · [Capture manifest and hashes](assets/cluster/manifest.json). The video covers incident submissions/evidence; the follow-up screenshot records the later stage after restart/correction. Password entry uses a masked input; no browser storage-state file or credentials are distributed.

## Reproduce

Use the Docker/kind/kubectl/Helm prerequisites and patched Python environment in [installation](installation.md). Node 22+ and the locked optional authoring tools are additionally required:

```sh
cd scripts/asset-tools
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
cd ../..
NODE_PATH="$PWD/scripts/asset-tools/node_modules" VENV=.venv-source \
  KI_ACCEPTANCE_SUITE=browser bash scripts/smoke.sh
```

Select a local Unix-socket Docker runtime. The wrapper refuses occupied cluster names, isolates installer kubeconfig, builds/installs the chart and cleans up only its owned cluster. Captures are regenerated under docs/assets/cluster. Use a new date/revision record when retaining a later result. Retain the fixture captures separately: they test a different evidence source.
