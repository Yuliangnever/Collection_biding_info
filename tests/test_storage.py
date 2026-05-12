from pathlib import Path

from src.models import TenderItem
from src.storage import TenderStorage


def test_storage_deduplicates_items(tmp_path: Path) -> None:
    storage = TenderStorage(str(tmp_path / "tenders.sqlite3"))
    item = TenderItem(
        title="招标公告",
        url="https://example.com/demo",
        source="demo",
        published_at="2026-05-12",
    )

    assert storage.save_many([item]) == 1
    assert storage.save_many([item]) == 0
    assert len(storage.list_latest()) == 1

