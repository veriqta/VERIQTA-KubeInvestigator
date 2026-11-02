import sqlite3
import secrets
import subprocess
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from kubeinvestigator.config import Settings
from kubeinvestigator.store import Store
from kubeinvestigator.maintenance import backup, restore
from kubeinvestigator.schemas import Report
from kubeinvestigator.app import create_app


def settings(tmp_path):
    return Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "records.db"))


def seed(store):
    r = Report(
        id="persisted",
        namespace="veriqta-demo",
        workload="",
        problem="Sample failure",
        scenario="service",
        provider="mock",
        model="fixture",
        source="fixture",
        mock=True,
        status="completed",
    )
    store.save(r)
    return r


def test_writer_exclusion_and_offline_maintenance(tmp_path):
    s = settings(tmp_path)
    store = Store(s)
    seed(store)
    with pytest.raises(RuntimeError, match="already in use"):
        Store(s)
    with pytest.raises(RuntimeError, match="already in use"):
        backup(s.database, tmp_path / "backup.db")
    store.close()
    assert backup(s.database, tmp_path / "backup.db") == 1
    assert (tmp_path / "backup.db").stat().st_mode & 0o077 == 0
    with pytest.raises(ValueError, match="exists"):
        backup(s.database, tmp_path / "backup.db")


def test_atomic_restore_validation_and_rollback_snapshot(tmp_path):
    s = settings(tmp_path)
    store = Store(s)
    original = seed(store)
    store.close()
    backup_file = tmp_path / "backup.db"
    backup(s.database, backup_file)
    store = Store(s)
    store.delete(original.id)
    store.close()
    count, previous = restore(s.database, backup_file)
    assert count == 1 and previous.exists()
    store = Store(s)
    assert store.get(original.id).model_dump() == original.model_dump()
    store.close()
    # Reversing restoration uses the automatically preserved prior snapshot.
    restore(s.database, previous)
    store = Store(s)
    assert store.get(original.id) is None
    store.close()
    before = Path(s.database).read_bytes()
    malformed = tmp_path / "bad.db"
    malformed.write_bytes(b"not a database")
    with pytest.raises(sqlite3.DatabaseError):
        restore(s.database, malformed)
    assert Path(s.database).read_bytes() == before
    # A corrupt existing target is preserved, never silently discarded.
    corrupt_target = tmp_path / "corrupt.db"
    corrupt_target.write_bytes(b"damaged original")
    with pytest.raises(sqlite3.DatabaseError):
        restore(corrupt_target, backup_file)
    assert corrupt_target.read_bytes() == b"damaged original"
    # Recover to a new private path while leaving damaged files for diagnosis.
    recovered_path = tmp_path / "recovered.db"
    count, previous = restore(recovered_path, backup_file)
    assert count == 1 and previous is None
    assert recovered_path.stat().st_mode & 0o077 == 0
    recovered = Store(s.model_copy(update={"database": str(recovered_path)}))
    assert recovered.get(original.id).model_dump() == original.model_dump()
    recovered.close()
    with sqlite3.connect(backup_file) as c:
        c.execute("PRAGMA user_version=2")
    with pytest.raises(ValueError, match="schema 1"):
        restore(s.database, backup_file)
    assert Path(s.database).read_bytes() == before


def test_full_sqlite_rolls_back_and_api_returns_safe_507(tmp_path):
    s = settings(tmp_path)
    with TestClient(create_app(s)) as client:
        client.headers["Authorization"] = "Bearer " + s.token.get_secret_value()
        store = client.app.state.store
        seed(store)
        pages = store.db.execute("PRAGMA page_count").fetchone()[0]
        store.db.execute(f"PRAGMA max_page_count={pages}")
        large = Report(
            id="oversize",
            namespace="veriqta-demo",
            workload="",
            problem="x" * 100000,
            scenario="service",
            provider="mock",
            model="fixture",
            source="fixture",
            mock=True,
        )
        with pytest.raises(sqlite3.OperationalError, match="full"):
            store.save(large)
        assert not store.db.in_transaction and store.get("persisted") is not None
        original = store.capacity

        def full():
            raise sqlite3.OperationalError("disk is full /private/operator-path")

        store.capacity = full
        response = client.post(
            "/api/investigations",
            json={"namespace": "veriqta-demo", "scenario": "service", "problem": "Sample failure"},
        )
        assert response.status_code == 507 and "/private/" not in response.text
        store.capacity = original


def test_cli_and_wal_snapshot_survive_process_exit(tmp_path):
    s = settings(tmp_path)
    # Abrupt process exit leaves any committed WAL available for backup recovery.
    code = """import os\nfrom kubeinvestigator.config import Settings\nfrom kubeinvestigator.store import Store\nfrom kubeinvestigator.schemas import Report\ns=Store(Settings(token='x'*32,database=__import__('sys').argv[1]))\ns.save(Report(id='crashed',namespace='veriqta-demo',workload='',problem='Sample failure',scenario='service',provider='mock',model='fixture',source='fixture',mock=True,status='running'))\nos._exit(0)"""
    subprocess.run([sys.executable, "-c", code, s.database], check=True)
    target = tmp_path / "wal-backup.db"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "kubeinvestigator.maintenance",
            "backup",
            "--database",
            s.database,
            "--file",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    restore(s.database, target)
    store = Store(s)
    assert store.get("crashed").status == "interrupted"
    store.close()


def test_migration_refuses_foreign_or_malformed_schema_without_marking_it_current(tmp_path):
    s = settings(tmp_path)
    with sqlite3.connect(s.database) as connection:
        connection.execute("CREATE TABLE reports (wrong TEXT)")
    with pytest.raises(RuntimeError, match="migration refused"):
        Store(s)
    with sqlite3.connect(s.database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert [row[1] for row in connection.execute("PRAGMA table_info(reports)")] == ["wrong"]
        connection.execute("DROP TABLE reports")
        connection.execute("CREATE TABLE unrelated (data TEXT)")
    with pytest.raises(RuntimeError, match="refusing automatic migration"):
        Store(s)
    with sqlite3.connect(s.database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall() == [("unrelated",)]
