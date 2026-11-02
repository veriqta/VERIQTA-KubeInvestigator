import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("evaluation", Path("scripts/evaluate.py"))
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def test_plan_is_bounded_and_human_review_stays_ungraded():
    plan = evaluation.plan()
    assert plan["investigations"] == 8 and plan["max_requests_total"] == 48
    assert plan["estimated_upper_envelope_usd"] < plan["proposed_budget_usd"] == 0.5
    assert plan["status"] == "not_executed"
    item = evaluation.review_item({"id": "healthy"}, {})
    assert item["review"]["acceptable_outcome"] is None
    assert item["review"]["incorrect_diagnosis"] is None


def test_private_evaluation_output_never_overwrites_evidence(tmp_path):
    output = tmp_path / "evaluation.json"
    evaluation.save(output, {"mode": "offline"})
    assert output.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        evaluation.save(output, {"mode": "changed"})


def test_replay_rejects_synthetic_evidence():
    from kubeinvestigator.schemas import Report

    r = Report(
        id="fixture",
        namespace="veriqta-demo",
        workload="frontend",
        problem="Service unavailable",
        scenario="service",
        provider="mock",
        model="mock",
        source="fixture",
        mock=True,
        status="completed",
    )
    with pytest.raises(ValueError, match="real Kubernetes"):
        evaluation.checked_report(r.model_dump(), live=False)
