"""Offline, single-writer SQLite maintenance. No Kubernetes or provider access."""

import argparse
from contextlib import closing
import fcntl
import os
import sqlite3
import tempfile
from pathlib import Path
from uuid import uuid4

from .schemas import Report
from .sqlite_runtime import require_sqlite


class DatabaseLease:
    def __init__(self, path):
        self.fd = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
        os.fchmod(self.fd, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            self.fd = -1
            raise RuntimeError(
                "Database is already in use; stop every application worker before maintenance"
            ) from None

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def validate(connection):
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("Database integrity check failed")
    if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise ValueError(
            "Only database schema 1 is supported; use the matching application version"
        )
    rows = connection.execute("SELECT id, body FROM reports").fetchall()
    for identifier, body in rows:
        if Report.model_validate_json(body).id != identifier:
            raise ValueError("Report identity does not match its database row")
    return len(rows)


def readonly(path):
    require_sqlite()
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def snapshot(source, destination):
    require_sqlite()
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Backup destination exists; choose a new private filename")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".ki-backup-", dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        with closing(readonly(source)) as origin, closing(sqlite3.connect(temporary)) as target:
            validate(origin)
            origin.backup(target)
            count = validate(target)
        # sqlite context managers commit, but do not close connections.
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.link(temporary, destination)  # Exclusive creation; never overwrite a backup.
        return count
    finally:
        temporary.unlink(missing_ok=True)


def backup(database, destination):
    require_sqlite()
    database = Path(database)
    if not database.is_file() or database.is_symlink():
        raise ValueError("Database must be an existing regular file")
    with DatabaseLease(database):
        return snapshot(database, destination)


def restore(database, source):
    require_sqlite()
    database, source = Path(database), Path(source)
    if database.is_symlink() or database.resolve() == source.resolve():
        raise ValueError("Restore target must be a separate regular database path")
    database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with DatabaseLease(database):
        prepared = database.with_name(".ki-restore-" + uuid4().hex)
        previous = None
        try:
            count = snapshot(source, prepared)  # Validate source before modifying target.
            if database.exists():
                previous = database.with_name(database.name + ".before-restore-" + uuid4().hex)
                snapshot(database, previous)
                with closing(sqlite3.connect(database)) as current:
                    if current.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] != 0:
                        raise RuntimeError("Database checkpoint is busy; restore refused")
            for suffix in ["-wal", "-shm"]:
                Path(str(database) + suffix).unlink(missing_ok=True)
            os.replace(prepared, database)
            os.chmod(database, 0o600)
            directory = os.open(database.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return count, previous
        finally:
            prepared.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["backup", "restore", "check"])
    parser.add_argument("--database", required=True)
    parser.add_argument("--file", help="New backup destination or existing restore source")
    args = parser.parse_args()
    try:
        require_sqlite()
        if args.operation == "check":
            with DatabaseLease(args.database), closing(readonly(args.database)) as connection:
                count = validate(connection)
            print(f"Schema 1 integrity and {count} report(s) verified")
        elif not args.file:
            parser.error("--file is required for backup/restore")
        elif args.operation == "backup":
            print(f"Backed up {backup(args.database, args.file)} report(s)")
        else:
            count, previous = restore(args.database, args.file)
            print(
                f"Restored {count} report(s); previous database snapshot: {previous or 'not applicable'}"
            )
    except RuntimeError as error:
        parser.exit(1, str(error) + "\n")
    except (OSError, ValueError, sqlite3.Error):
        parser.exit(
            1,
            "Maintenance failed: stop the application; check paths, schema, integrity, permissions and free space. No credentials or database content are printed.\n",
        )


if __name__ == "__main__":
    main()
