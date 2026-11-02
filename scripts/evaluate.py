"""Plan, replay structural checks, or explicitly run a bounded live evaluation.

No model call occurs in plan/replay. Human labels are required for accuracy.
"""

import argparse
import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from kubeinvestigator.schemas import Report

ROOT = Path(__file__).resolve().parents[1]


def plan():
    cases = json.loads((ROOT / "evals/cases.json").read_text())
    return {
        "provider": "openai",
        "model": "gpt-6-luna",
        "reasoning_effort": "none",
        "investigations": len(cases),
        "max_requests_per_investigation": 6,
        "max_requests_total": len(cases) * 6,
        "max_output_tokens_per_request": 1600,
        "max_model_payload_characters": 48000,
        "conservative_input_token_allowance_per_request": 50000,
        "estimated_upper_envelope_usd": round(
            len(cases) * 6 * (50000 * 0.10 + 1600 * 0.50) / 1000000, 4
        ),
        "proposed_budget_usd": 0.50,
        "price_checked_utc": "2026-11-02",
        "price_source": "https://developers.openai.com/api/docs/models/gpt-6-luna",
        "pricing_assumptions": "Standard text input $0.10/M, output $0.50/M; no cache discount. Conservative input allowance, not a provider-side spending cap. Recheck pricing/account before authorisation.",
        "limits": "90 seconds per running investigation; 8 tool calls; 6 model turns; no retries; sequential cases. Unrelated/mismatched requests may use zero model calls.",
        "status": "not_executed",
        "cases": cases,
    }


def checked_report(value, *, live):
    r = Report.model_validate(value)
    if r.source != "kubernetes" or (live and (r.mock or r.provider != "openai")):
        raise ValueError("Expected real Kubernetes evidence and the explicitly selected provider")
    if r.status in {"queued", "running"}:
        raise ValueError("Investigation did not reach a terminal state")
    known = {e.id for e in r.evidence if not e.error}
    if r.finding and not set(r.finding.evidence_ids) <= known:
        raise ValueError("Unknown evidence reference")
    return r.model_dump()


def review_item(case, report):
    return {
        "case": case,
        "report": report,
        "review": {
            "incorrect_diagnosis": None,
            "unsupported_claim": None,
            "acceptable_outcome": None,
            "notes": "Human review required; null is not a pass",
        },
    }


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Never overwrite earlier evidence and keep raw evaluation outputs private.
    path.touch(mode=0o600, exist_ok=False)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument(
        "--replay", type=Path, help="Validate captured real-cluster reports without calling a model"
    )
    mode.add_argument("--run", action="store_true")
    p.add_argument("--acknowledge-paid-calls", action="store_true")
    p.add_argument("--url", default="http://127.0.0.1:18080")
    p.add_argument("--output", type=Path, default=Path(".data/live-evaluation.json"))
    p.add_argument(
        "--token-file",
        type=Path,
        help="Private file containing only the team token; provider key stays on server",
    )
    a = p.parse_args()
    specification = plan()
    if a.plan:
        print(json.dumps(specification, indent=2))
        return
    if a.output.exists():
        p.error("Choose a new output path; previous evidence is never overwritten")
    result = {
        "created_at": datetime.now(UTC).isoformat(),
        "plan": specification,
        "prompt_version": "1",
        "cases_sha256": hashlib.sha256((ROOT / "evals/cases.json").read_bytes()).hexdigest(),
        "cases": [],
        "diagnostic_accuracy": "unreviewed; no score inferred",
    }
    if a.replay:
        reports = json.loads(a.replay.read_text())
        result["mode"] = "offline structural replay of real Kubernetes evidence; no model calls"
        for name, value in reports.items():
            result["cases"].append(review_item({"id": name}, checked_report(value, live=False)))
        save(a.output, result)
        print("Real-evidence structural replay passed; diagnostic accuracy remains unverified.")
        return
    if not a.acknowledge_paid_calls:
        p.error("--run also requires --acknowledge-paid-calls after independent authorisation")
    target = urlsplit(a.url)
    if (
        target.scheme != "http"
        or target.hostname not in {"127.0.0.1", "localhost"}
        or target.username
        or target.password
        or target.query
        or target.fragment
        or target.path not in {"", "/"}
    ):
        p.error("Use an explicit localhost port-forward to an authorised disposable deployment")
    token = a.token_file.read_text().strip() if a.token_file else os.environ.get("KI_TOKEN", "")
    if a.token_file and a.token_file.stat().st_mode & 0o077:
        p.error("Team token file must be private (chmod 600)")
    if not token:
        p.error("Set KI_TOKEN or --token-file privately; never put provider keys in this command")
    result["mode"] = "live provider with real Kubernetes evidence"
    try:
        with httpx.Client(
            base_url=a.url,
            headers={"Authorization": "Bearer " + token},
            timeout=30,
            follow_redirects=False,
        ) as c:
            config = c.get("/api/config").raise_for_status().json()
            if (
                config["mock"]
                or config["source"] != "kubernetes"
                or config["model"] != specification["model"]
                or not config["logs"]
                or config["namespaces"] != ["veriqta-demo"]
            ):
                raise ValueError(
                    "Expected OpenAI gpt-6-luna, real Kubernetes evidence, optional logs and only the disposable veriqta-demo namespace"
                )
            limits = config["limits"]
            if limits["max_turns"] > 6 or limits["max_calls"] > 8 or limits["duration"] > 90:
                raise ValueError("Deployment limits exceed the proposed evaluation budget")
            result["configuration"] = config
            for case in specification["cases"]:
                created = (
                    c.post(
                        "/api/investigations",
                        json={key: case[key] for key in ("scenario", "workload", "problem")}
                        | {"namespace": "veriqta-demo"},
                    )
                    .raise_for_status()
                    .json()
                )
                identifier = created["id"]
                deadline = time.monotonic() + 120
                while True:
                    report = c.get("/api/investigations/" + identifier).raise_for_status().json()
                    if report["status"] not in {"queued", "running"}:
                        break
                    if time.monotonic() >= deadline:
                        c.post("/api/investigations/" + identifier + "/cancel").raise_for_status()
                        raise ValueError(
                            "Evaluation timed out; cancellation requested; no further cases submitted"
                        )
                    time.sleep(2)
                result["cases"].append(review_item(case, checked_report(report, live=True)))
    except Exception as exc:
        result["execution_failure"] = (
            type(exc).__name__ + ": evaluation stopped; inspect deployment safely"
        )
        save(a.output, result)
        raise SystemExit(
            "Evaluation failed; partial private evidence retained; no automatic retry"
        ) from None
    save(a.output, result)
    print("Live reports captured. Human review is required; no accuracy score inferred.")


if __name__ == "__main__":
    main()
