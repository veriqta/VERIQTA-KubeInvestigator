"""Run inside the final image, offline, as its configured non-root user."""

import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import ssl
import tempfile

import certifi
from kubeinvestigator.config import Settings
from kubeinvestigator.store import Store
from kubeinvestigator.sqlite_runtime import require_sqlite

assert os.getuid() == 10001
require_sqlite()
assert not importlib.util.find_spec("pip"), "Packaging tools leaked into runtime"
for command in ("gcc", "g++", "cc", "make", "abuild", "perl", "apt-get"):
    assert shutil.which(command) is None, f"Unnecessary runtime tool: {command}"
context = ssl.create_default_context()
assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
assert context.cert_store_stats()["x509_ca"] > 0
assert Path(certifi.where()).is_file()

# Adapted from SQLite's public-domain upstream regression for CVE-2026-119373:
# https://github.com/sqlite/sqlite/commit/e1c9934f9f11a499029abb020ea715a08970da80
# Keep FTS5 enabled; fix the library rather than disabling a feature.
with sqlite3.connect(":memory:") as connection:
    for detail in ("none", "column", "full"):
        connection.execute(f"CREATE VIRTUAL TABLE fts USING fts5(x, detail={detail})")
        connection.executemany(
            "INSERT INTO fts(rowid,x) VALUES(?,?)", [(n, "ab") for n in range(1, 56)]
        )
        connection.execute("INSERT INTO fts(rowid,x) VALUES(?,?)", (-(2**63), "abc"))
        assert connection.execute("SELECT count(*) FROM fts('a*')").fetchone()[0] == 56
        connection.execute("DROP TABLE fts")
    assert connection.execute("SELECT json_extract(?, '$.a')", ('{"a":1}',)).fetchone()[0] == 1
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

with tempfile.TemporaryDirectory() as directory:
    settings = Settings(token="x" * 32, database=str(Path(directory) / "test.db"))
    store = Store(settings)
    assert store.db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    store.close()
    store = Store(settings)
    store.close()

libraries = sorted({str(p.resolve()) for p in Path("/usr/lib").glob("libsqlite3.so*")})
assert libraries, "SQLite shared library missing"
assert any("libsqlite3.so" in line for line in Path("/proc/self/maps").read_text().splitlines())
print(
    json.dumps(
        {
            "status": "passed",
            "uid": os.getuid(),
            "python": os.sys.version.split()[0],
            "sqlite": sqlite3.sqlite_version,
            "sqlite_libraries": {
                path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in libraries
            },
            "checks": [
                "non-root",
                "no runtime packaging/compiler tools",
                "TLS verification and CA stores",
                "FTS5 negative-rowid prefix regression, three detail modes",
                "JSON functions and database integrity",
                "application WAL initialisation and restart",
            ],
            "application": importlib.metadata.version("veriqta-kubeinvestigator"),
        },
        indent=2,
    )
)
