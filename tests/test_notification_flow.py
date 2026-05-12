from src.models import TenderItem
from src.pipeline import TenderPipeline
from tests.test_helpers import fresh_test_database


class RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, item: TenderItem) -> bool:
        self.sent.append(item.title)
        return True


def test_push_pending_sends_and_marks_real_items() -> None:
    pipeline = TenderPipeline(
        {
            "database_path": fresh_test_database("notification.sqlite3"),
            "webhook_url": "",
            "request_timeout": 1,
            "demo_source_enabled": False,
            "allow_demo_notifications": False,
            "keywords": {},
            "companies": [],
            "sources": [],
        }
    )
    item = TenderItem(
        title="光伏项目采购招标公告",
        url="https://example.com/notice/1",
        source="测试平台",
        published_at="2026-05-12",
    )
    pipeline.storage.save_many([item])
    notifier = RecordingNotifier()
    pipeline.notifier = notifier

    summary = pipeline.push_pending()

    assert summary == {"notified": 1}
    assert notifier.sent == ["光伏项目采购招标公告"]
    assert pipeline.storage.list_latest()[0].notified is True


def test_push_pending_respects_limit() -> None:
    pipeline = TenderPipeline(
        {
            "database_path": fresh_test_database("notification-limit.sqlite3"),
            "webhook_url": "",
            "request_timeout": 1,
            "demo_source_enabled": False,
            "allow_demo_notifications": False,
            "keywords": {},
            "companies": [],
            "sources": [],
        }
    )
    pipeline.storage.save_many(
        [
            TenderItem(
                title="光伏项目采购招标公告",
                url="https://example.com/notice/1",
                source="测试平台",
                published_at="2026-05-12",
            ),
            TenderItem(
                title="风电项目中标公示",
                url="https://example.com/notice/2",
                source="测试平台",
                published_at="2026-05-12",
            ),
        ]
    )
    notifier = RecordingNotifier()
    pipeline.notifier = notifier

    summary = pipeline.push_pending(limit=1)

    assert summary == {"notified": 1}
    assert notifier.sent == ["光伏项目采购招标公告"]
