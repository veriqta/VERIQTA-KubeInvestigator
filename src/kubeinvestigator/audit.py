"""Allowlisted security records; never accept raw request/evidence metadata."""

import json
import logging
from datetime import datetime, timezone


def security_event(event, *, request_id=None, investigation_id=None, status=None):
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event}
    if request_id:
        record["request_id"] = request_id
    if investigation_id:
        record["investigation_id"] = investigation_id
    if status is not None:
        record["status"] = status
    logging.getLogger("kubeinvestigator").info(json.dumps(record))
