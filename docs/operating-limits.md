# First-release operating profile

Run one application replica and one worker with reliable local/PVC SQLite locking. This profile provides neither high availability nor a distributed queue. The chart defaults to two running investigations, at most 20 total active/queued tasks, eight collection calls and six model turns per investigation, with a 90-second running deadline. Queue wait is additional; callers must handle HTTP 429 and use bounded retry/backoff. Restart marks retained unfinished work interrupted rather than silently resuming it.

## Recorded measurement

The [local bounded run](acceptance/2026-11-02-bounded-load-mock.json) used a disposable kind 1.35.8 cluster on an arm64 Docker VM allocated two CPUs and 4 GiB. The application used its default 100m CPU/128Mi request, 1 CPU/512Mi limits, real Kubernetes evidence and mock interpretations. Kubernetes samples were small: three incidents and a few pods. It is not a large-namespace, sustained-load or live-provider benchmark.

| Client concurrency | Submissions | Accepted / HTTP 429 | Largest sampled queue | Longest observed completion |
| --- | --- | --- | --- | --- |
| 1 | 8 | 8 / 0 | 0 | 0.288 s |
| 2 | 8 | 8 / 0 | 2 | 0.302 s |
| 4 | 8 | 8 / 0 | 4 | 0.323 s |
| 32 | 32 | 20 / 12 | 16 | 0.403 s |

All accepted investigations completed. The rate limiter rejected excess requests and recovered within its documented window. Nine kubelet samples observed a maximum **73.18 MiB working set** and **9.97m CPU** over the sampled averaging windows; these are not peak CPU or memory bounds. Metrics observed two running jobs. Sampled queue depth can miss short transitions. Client timings include port-forward and polling delay. The local kubectl was 1.37.2 against server 1.35.8, outside supported minor skew; requests succeeded, but supported reproductions must use the matching 1.35.8 installer. Hosted jobs install matching tools.

For a small initial team installation, reserve at least **250m CPU and 256Mi memory**, retaining a **1 CPU/512Mi limit**, one replica and default investigation concurrency two. This is a conservative starting allocation above the measured small-workload baseline, not a validated production throughput guarantee. Retain the default 1Gi PVC, separate backup capacity and the 100MB database-family admission threshold. Watch queue, rejection, storage and resource signals before raising limits. Provider latency, long logs, larger namespaces, exports and other workloads require environment-specific measurements; do not extrapolate the mock response times to live mode.

## Reproduce safely

With a patched source setup and a local Docker runtime:

```sh
bash scripts/install-kind-tools.sh v1.35.8 "$PWD/.capture/acceptance-bin"
PATH="$PWD/.capture/acceptance-bin:$PATH" VENV=.venv-source \
  KI_ACCEPTANCE_SUITE=load bash scripts/smoke.sh
```

The bounded harness submits 56 investigations, never calls a model, samples only application resource fields, tests queue/rate failures and recovery, and cleans up its dedicated cluster. Installer credentials read kubelet statistics; the application account receives no node permissions. Raw environment dumps, cluster-wide samples and credentials are not retained. Use a fresh result filename/date/revision when recording a later run.

Physical storage loss, multi-writer/HA operation and cross-release schema downgrade are outside this first-release contract. Backup/restore and same-schema rollback are separately tested; a future migration must define and test its own compatibility pair.
