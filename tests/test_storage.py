from src.models import TenderItem
from src.storage import TenderStorage
from tests.test_helpers import fresh_test_database


def test_storage_deduplicates_items() -> None:
    storage = TenderStorage(fresh_test_database("storage.sqlite3"))
    item = TenderItem(
        title="招标公告",
        url="demo://storage-test",
        source="测试",
        published_at="2026-05-12",
    )

    assert storage.save_many([item]) == 1
    assert storage.save_many([item]) == 0
    assert len(storage.list_latest()) == 1

