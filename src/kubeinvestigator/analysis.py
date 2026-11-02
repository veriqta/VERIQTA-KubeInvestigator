from .schemas import Finding


def observations(report):
    rows: dict[str, list] = {k: [] for k in ["pods", "services", "endpointslices", "events"]}
    for evidence in report.evidence:
        if not evidence.error:
            kind = evidence.resource.split("/")[1]
            if kind in rows and isinstance(evidence.data, list):
                rows[kind].extend(evidence.data)
    results = []
    if report.scenario in {"crash", "image"}:
        reasons = {"crash": {"CrashLoopBackOff"}, "image": {"ImagePullBackOff", "ErrImagePull"}}[
            report.scenario
        ]
        for pod in rows["pods"]:
            for c in pod.get("containers", []):
                if (c.get("waiting") or {}).get("reason") in reasons:
                    results.append(
                        f"Pod {pod['name']} container {c['name']} is waiting: {c['waiting']['reason']}; last exit: {c.get('last_exit')}; message: {c['waiting'].get('message', '')}"
                    )
                elif (
                    report.scenario == "crash"
                    and c.get("restarts", 0) > 0
                    and (c.get("terminated") or {}).get("exit_code", 0) != 0
                ):
                    results.append(
                        f"Pod {pod['name']} container {c['name']} has repeatedly exited and is currently terminated: {c['terminated']}; restart count: {c['restarts']}. A waiting reason may be absent between backoff updates; this does not establish the root cause."
                    )
    else:
        required = [e for e in report.evidence if e.resource.split("/")[1] in {"pods", "services"}]
        if len(required) < 2 or any(e.error or e.truncated for e in required):
            return []
        for service in rows["services"]:
            selector = service.get("selector", {})
            if selector and not any(
                all(p.get("labels", {}).get(k) == v for k, v in selector.items())
                for p in rows["pods"]
            ):
                results.append(
                    f"Service {service['name']} selector {selector} matches no pods in the collected namespace snapshot."
                )
    return results


def mock_finding(report):
    has = bool(report.observations)
    diagnoses = {
        "service": "The Service selector matches no collected pods. Compare the intended workload labels before correcting the selector manually.",
        "crash": "Repeated container exits are observed. Exit status alone does not establish why the application failed.",
        "image": "An image pull backoff is observed. Inspect the collected message and events to distinguish an invalid image reference from registry access or availability failures.",
    }
    return Finding(
        diagnosis=("MOCK — " + diagnoses[report.scenario])
        if has
        else "MOCK — Requested condition not observed in this snapshot; this does not establish health.",
        assessment="tentative" if has else "insufficient evidence",
        evidence_ids=[e.id for e in report.evidence if not e.error],
        alternatives=[
            "Missing permissions, transient state, incomplete snapshots, or a different workload may explain the result."
        ],
        next_steps=[
            "Inspect the evidence and compare it with the intended workload configuration.",
            "Make any correction independently, then run a linked follow-up investigation.",
        ],
    )
