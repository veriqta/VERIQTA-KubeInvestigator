"""Fail on unknown/restricted runtime dependency licences pending human review."""

import json
import sys
from pathlib import Path

items = json.loads(Path(sys.argv[1]).read_text())
for item in items:
    license_name = item["License"]
    if any(marker in license_name.lower() for marker in ["unknown", "gpl", "proprietary"]):
        raise SystemExit(f"Review dependency licence: {item['Name']} — {license_name}")
print(
    f"Reviewed basic licence flags for {len(items)} installed distributions; retain upstream notices in release SBOM."
)
