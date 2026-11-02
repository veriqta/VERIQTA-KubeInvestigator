"""Check the pinned SQLite release/checksum against its official download feed.

This detects a stale release pin, not every security advisory. Run manually and
in validation; network failure is an error, never a successful security result.
"""

import json
from pathlib import Path
import re
import sys

import httpx

FEED = "https://sqlite.org/download.html"


def compare_release(text, pinned):
    products = re.findall(
        r"^PRODUCT,([0-9.]+),([^,\s]*sqlite-autoconf-[0-9]+\.tar\.gz),[0-9]+,([a-f0-9]{64})",
        text,
        re.MULTILINE,
    )
    if len(products) != 1:
        raise ValueError("Official SQLite autoconf product feed was not recognised")
    version, path, checksum = products[0]
    if (version, "https://sqlite.org/" + path, checksum) != (
        pinned["version"],
        pinned["url"],
        pinned["sha3_256"],
    ):
        raise ValueError(
            f"SQLite pin {pinned['version']} differs from official release {version} "
            "or its URL/checksum. Review upstream security/release notes, verify source "
            "hashes and update packaging/sqlite, the preflight floor and runtime checks together."
        )
    return {"status": "current", "version": version, "feed": FEED, "sha3_256": checksum}


def main():
    try:
        pinned = json.loads(
            (Path(__file__).resolve().parents[1] / "packaging/sqlite/source.json").read_text()
        )
        response = httpx.get(FEED, timeout=30, follow_redirects=False)
        response.raise_for_status()
        if len(response.content) > 1_000_000:
            raise ValueError("Unexpectedly large SQLite feed")
        print(json.dumps(compare_release(response.text, pinned)))
        return 0
    except (httpx.HTTPError, ValueError, OSError) as error:
        print(f"SQLite update check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
