import secrets
import sqlite3
import sys

import pytest

from kubeinvestigator.app import create_app
from kubeinvestigator.config import Settings
from kubeinvestigator.maintenance import backup, restore, main as maintenance_main
from kubeinvestigator.sqlite_runtime import require_sqlite, main
from kubeinvestigator.store import Store


@pytest.mark.parametrize("version", [(3, 53, 1), (3, 54, 0)])
def test_affected_runtime_fails_before_database_or_server_start(tmp_path, monkeypatch, version):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", version)
    monkeypatch.setattr(sqlite3, "sqlite_version", ".".join(map(str, version)))
    settings = Settings(token=secrets.token_urlsafe(32), database=str(tmp_path / "private/db"))
    for operation in (lambda: Store(settings), lambda: create_app(settings)):
        with pytest.raises(RuntimeError, match="SQLite 3.54.1 or newer is required"):
            operation()
    assert not (tmp_path / "private").exists()


def test_preflight_and_maintenance_errors_are_actionable_without_opening_db(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 53, 1))
    monkeypatch.setattr(sqlite3, "sqlite_version", "3.53.1")

    def forbidden(*args, **kwargs):
        pytest.fail("An affected runtime must not open a database")

    monkeypatch.setattr(sqlite3, "connect", forbidden)
    assert main() == 1
    message = capsys.readouterr().err
    assert "3.53.1" in message and "Homebrew" in message and "recreate" in message
    assert "pip packages alone does not patch" in message and "docs/installation.md" in message
    for operation in (backup, restore):
        with pytest.raises(RuntimeError, match="unsupported"):
            operation(tmp_path / "database", tmp_path / "backup")
    monkeypatch.setattr(
        sys, "argv", ["maintenance", "check", "--database", str(tmp_path / "database")]
    )
    with pytest.raises(SystemExit) as exit_code:
        maintenance_main()
    assert exit_code.value.code == 1
    assert "SQLite 3.53.1" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_patched_runtime_preflight_reports_the_loaded_version(monkeypatch, capsys):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 54, 1))
    monkeypatch.setattr(sqlite3, "sqlite_version", "3.54.1")
    require_sqlite()
    assert main() == 0
    assert '"sqlite": "3.54.1"' in capsys.readouterr().out
