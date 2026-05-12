from __future__ import annotations

from pathlib import Path


TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "test"


def fresh_test_database(name: str) -> str:
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    database_path = TEST_DATA_DIR / name
    if database_path.exists():
        database_path.unlink()
    return str(database_path)

