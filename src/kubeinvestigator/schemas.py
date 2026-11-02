from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def now():
    return datetime.now(UTC).isoformat()


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Request(Strict):
    namespace: str = Field(min_length=1, max_length=63)
    workload: str = Field(default="", max_length=253, pattern=r"^[a-z0-9.\-]*$")
    problem: str = Field(min_length=8, max_length=2000)
    scenario: Literal["crash", "image", "service"]


class ToolArgs(Strict):
    namespace: str
    resource: Literal[
        "pods", "events", "services", "endpointslices", "deployments", "replicasets", "logs"
    ]
    name: str = Field(default="", max_length=253, pattern=r"^[a-z0-9.\-]*$")
    container: str = Field(default="", max_length=253, pattern=r"^[a-z0-9.\-]*$")
    previous: bool = False


class Finding(Strict):
    diagnosis: str = Field(max_length=4000)
    assessment: Literal["supported", "tentative", "insufficient evidence"]
    evidence_ids: list[str] = Field(max_length=32)
    resource_refs: list[str] = Field(default_factory=list, max_length=100)
    alternatives: list[str] = Field(max_length=10)
    next_steps: list[str] = Field(max_length=10)


class Evidence(Strict):
    id: str
    resource: str
    collected_at: str = Field(default_factory=now)
    data: Any
    truncated: bool = False
    error: str | None = None


class Report(Strict):
    schema_version: str = "1.0"
    software_version: str = "0.1.0"
    id: str
    created_at: str = Field(default_factory=now)
    completed_at: str | None = None
    namespace: str
    workload: str
    problem: str
    scenario: str
    status: Literal[
        "queued",
        "running",
        "completed",
        "insufficient evidence",
        "failed",
        "cancelled",
        "interrupted",
    ] = "queued"
    provider: str
    model: str
    source: str
    mock: bool
    evidence: list[Evidence] = []
    observations: list[str] = []
    finding: Finding | None = None
    limitations: list[str] = [
        "A point-in-time investigation cannot guarantee application health.",
        "Redaction is best effort; review exports before sharing.",
    ]
    failures: list[str] = []
    usage: dict = {}
    estimated_cost: float | None = None
    duration_seconds: float = 0
    parent_id: str | None = None
    followup_ids: list[str] = []
    verification: str | None = None


class HistoryItem(Strict):
    id: str
    created_at: str
    namespace: str
    workload: str
    scenario: str
    status: str
    mock: bool
    source: str
