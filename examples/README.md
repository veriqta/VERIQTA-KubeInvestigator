# Disposable failure scenarios

Run only through the dedicated kind setup in [installation](../docs/installation.md). All examples create resources in veriqta-demo: three Pods and one Service; Kubernetes creates associated events and EndpointSlices. Only sample scripts modify these workloads. The application service account remains read-only.

| Example | Purpose and expected failure | Request | Expected report | Manual correction |
| --- | --- | --- | --- | --- |
| checkout-crash | BusyBox prints a missing-configuration message then exits 1; CrashLoopBackOff develops | scenario=crash, workload=checkout-crash, problem="Checkout container keeps restarting" | Pod waiting/restart/last-exit evidence and relevant events; root cause remains uncertain without logs | `bash scripts/demo.sh correct-crash` replaces only this sample with a long-running container |
| catalog-image | Intentionally nonexistent BusyBox tag; ImagePullBackOff develops after pulls fail | scenario=image, workload=catalog-image, problem="Catalog cannot pull its image" | Waiting message and pull events; check tag/access, no invented credentials | `bash scripts/demo.sh correct-image` sets a valid tag |
| frontend | Ready nginx pod labelled app=frontend, Service selects app=frontned | scenario=service, workload=frontend, problem="Frontend Service has no endpoints" | Pod labels, selector mismatch and EndpointSlice evidence; recommend comparing intended labels | `bash scripts/demo.sh correct-service` updates the sample selector |

After each correction, select Run fresh follow-up on the original report. Expect fresh timestamps and a related investigation ID. A real Kubernetes snapshot may report the prior condition absent, with an explicit health limitation. A fixture follow-up never verifies an actual correction. Allow controller and image-pull backoff convergence; scripts use bounded waits. Setup checks refuse unrelated contexts. After stopping port-forward, `bash scripts/demo.sh cleanup` deletes only the dedicated demo cluster; never run generic namespace deletion against your own cluster.
