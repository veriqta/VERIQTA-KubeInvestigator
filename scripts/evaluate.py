"""Opt-in live evaluation against an already configured, authorised deployment."""

import argparse
import json
import os
import time
from pathlib import Path
from datetime import datetime, timezone
import httpx

p = argparse.ArgumentParser()
p.add_argument("--acknowledge-paid-calls", action="store_true", required=True)
p.add_argument("--url", default="http://127.0.0.1:8080")
p.add_argument("--output", default=".data/live-evaluation.json")
a = p.parse_args()
if not a.url.startswith(("http://127.0.0.1:", "https://")):
    p.error("Use localhost or HTTPS")
results = []
with httpx.Client(
    base_url=a.url,
    headers={"Authorization": "Bearer " + os.environ["KI_TOKEN"]},
    timeout=30,
    follow_redirects=False,
) as c:
    configuration = c.get("/api/config").raise_for_status().json()
    if configuration["mock"]:
        p.error("Deployment uses mock; configure the live provider explicitly")
    for case in json.loads(Path("evals/cases.json").read_text()):
        response = c.post(
            "/api/investigations",
            json={k: case[k] for k in ("scenario", "workload", "problem")}
            | {"namespace": "veriqta-demo"},
        )
        response.raise_for_status()
        identifier = response.json()["id"]
        for _ in range(200):
            report = c.get("/api/investigations/" + identifier).raise_for_status().json()
            if report["status"] not in ("queued", "running"):
                break
            time.sleep(0.5)
        results.append(
            {
                "case": case,
                "report": report,
                "review": {
                    "incorrect_diagnosis": None,
                    "unsupported_claim": None,
                    "acceptable_outcome": None,
                    "notes": "Human review required; null is not a pass",
                },
            }
        )
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
Path(a.output).write_text(
    json.dumps(
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "prompt_version": "1",
            "configuration": configuration,
            "cases": results,
            "estimated_cost": None,
        },
        indent=2,
    )
)
print("Evaluation captured. Review every case; no quality score is inferred automatically.")
