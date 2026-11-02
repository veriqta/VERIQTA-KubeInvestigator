import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "sqlite_update", Path(__file__).resolve().parents[1] / "scripts/check_sqlite_update.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_release_monitor_rejects_changed_release_checksum_and_invalid_feed():
    pinned = {
        "version": "3.54.1",
        "url": "https://sqlite.org/2026/sqlite-autoconf-3540100.tar.gz",
        "sha3_256": "a" * 64,
    }
    feed = "PRODUCT,3.54.1,2026/sqlite-autoconf-3540100.tar.gz,123," + "a" * 64
    assert module.compare_release(feed, pinned)["status"] == "current"
    for altered in [feed.replace("3.54.1,", "3.55.0,"), feed[:-1] + "b", "unrecognised feed"]:
        with pytest.raises(ValueError):
            module.compare_release(altered, pinned)


def test_sqlite_pin_recipe_and_startup_floor_stay_aligned():
    import json
    from kubeinvestigator.sqlite_runtime import MINIMUM_SQLITE

    root = Path(__file__).resolve().parents[1]
    pinned = json.loads((root / "packaging/sqlite/source.json").read_text())
    assert tuple(map(int, pinned["version"].split("."))) >= MINIMUM_SQLITE
    recipe = (root / "packaging/sqlite/APKBUILD").read_text()
    assert "pkgver=" + pinned["version"] in recipe
    assert pinned["sha512"] in recipe
