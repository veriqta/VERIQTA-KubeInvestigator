"""Fail closed on a known affected SQLite runtime; no loader or module overrides."""

import json
import sqlite3
import sys

MINIMUM_SQLITE = (3, 54, 1)


def require_sqlite():
    if sqlite3.sqlite_version_info < MINIMUM_SQLITE:
        raise RuntimeError(
            f"SQLite {sqlite3.sqlite_version} loaded by Python is unsupported; "
            "SQLite 3.54.1 or newer is required (CVE-2026-119373 and subsequent fixes). "
            "Upgrading the sqlite3 command or pip packages alone does not patch Python's library. "
            "On macOS install/upgrade Homebrew python@3.12 and sqlite, then recreate the "
            "virtual environment using that interpreter. On Linux/WSL2 use a maintained "
            "interpreter linked to patched SQLite, or the documented container runtime. "
            "Run make preflight VENV=YOUR_VENV before starting. See docs/installation.md."
        )


def main():
    try:
        require_sqlite()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "passed",
                "python": sys.version.split()[0],
                "sqlite": sqlite3.sqlite_version,
                "minimum_sqlite": ".".join(map(str, MINIMUM_SQLITE)),
                "scope": "known-version prerequisite; not a complete vulnerability assessment",
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
