import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .schemas import Report, HistoryItem
from .maintenance import DatabaseLease
from .sqlite_runtime import require_sqlite


class Store:
    def __init__(self, settings):
        require_sqlite()
        self.s = settings
        settings.prepare()
        self.lock = threading.RLock()
        self.lease = DatabaseLease(settings.database)
        try:
            self.db = sqlite3.connect(settings.database, check_same_thread=False)
            Path(settings.database).chmod(0o600)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA busy_timeout=3000")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise RuntimeError("Database schema is newer than this application")
            if version == 0:
                tables = {
                    row[0]
                    for row in self.db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                }
                if tables - {"reports"}:
                    raise RuntimeError("Unrecognised database; refusing automatic migration")
                self.db.execute("BEGIN IMMEDIATE")
                try:
                    self.db.execute(
                        "CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, created TEXT NOT NULL, body TEXT NOT NULL)"
                    )
                    columns = [row[1] for row in self.db.execute("PRAGMA table_info(reports)")]
                    if columns != ["id", "created", "body"]:
                        raise RuntimeError("Unrecognised report table; migration refused")
                    self.db.execute("PRAGMA user_version=1")
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    raise
            if self.db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise RuntimeError("Database integrity check failed; restore a verified backup")
        except Exception:
            if hasattr(self, "db"):
                self.db.close()
            self.lease.close()
            raise
        try:
            interrupted_ids = [
                row[0]
                for row in self.db.execute(
                    "SELECT id FROM reports WHERE json_extract(body, '$.status') IN ('queued','running')"
                )
            ]
            for identifier in interrupted_ids:
                report = self.get(identifier)
                if report is not None:
                    report.status = "interrupted"
                    report.failures.append(
                        "Application restarted. Create a follow-up to collect fresh evidence."
                    )
                    self.save(report)
            self.cleanup()
        except Exception:
            self.close()
            raise

    def save(self, report):
        with self.lock:
            try:
                self.db.execute(
                    "INSERT OR REPLACE INTO reports VALUES (?, ?, ?)",
                    (report.id, report.created_at, report.model_dump_json()),
                )
                self.db.commit()
            except sqlite3.Error:
                self.db.rollback()
                raise

    def get(self, identifier):
        with self.lock:
            row = self.db.execute("SELECT body FROM reports WHERE id=?", (identifier,)).fetchone()
            return Report.model_validate_json(row[0]) if row else None

    def list(self):
        with self.lock:
            return [
                Report.model_validate_json(r[0])
                for r in self.db.execute("SELECT body FROM reports ORDER BY created DESC")
            ]

    def history(self, namespaces, limit=30, offset=0):
        fields = list(HistoryItem.model_fields)
        projection = ", ".join("json_extract(body, '$." + field + "')" for field in fields)
        placeholders = ",".join("?" for _ in namespaces)
        with self.lock:
            rows = self.db.execute(
                "SELECT "
                + projection
                + " FROM reports WHERE json_extract(body, '$.namespace') IN ("
                + placeholders
                + ") ORDER BY created DESC, id DESC LIMIT ? OFFSET ?",
                (*namespaces, limit, offset),
            ).fetchall()
            return [HistoryItem.model_validate(dict(zip(fields, row))) for row in rows]

    def state_counts(self):
        with self.lock:
            return dict(
                self.db.execute(
                    "SELECT json_extract(body, '$.status'), count(*) FROM reports GROUP BY json_extract(body, '$.status')"
                )
            )

    def delete(self, identifier):
        with self.lock:
            self.db.execute("DELETE FROM reports WHERE id=?", (identifier,))
            self.db.commit()

    def cleanup(self):
        cutoff = (datetime.now(UTC) - timedelta(days=self.s.retention_days)).isoformat()
        with self.lock:
            self.db.execute(
                "DELETE FROM reports WHERE created < ? AND json_extract(body, '$.status') NOT IN ('queued','running')",
                (cutoff,),
            )
            self.db.commit()
            self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def capacity(self):
        self.cleanup()
        size = sum(
            p.stat().st_size
            for p in Path(self.s.database).parent.glob(Path(self.s.database).name + "*")
            if p.is_file()
        )
        return sum(self.state_counts().values()) < self.s.max_records and size < self.s.max_db_bytes

    def close(self):
        self.db.close()
        self.lease.close()
