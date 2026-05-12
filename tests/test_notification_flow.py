from datetime import date, timedelta

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
            "notify_today_only": True,
            "keywords": {},
            "companies": [],
            "sources": [],
        }
    )
    item = TenderItem(
        title="光伏项目采购招标公告",
        url="https://example.com/notice/1",
        source="测试平台",
        published_at=date.today().isoformat(),
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
            "notify_today_only": True,
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
                published_at=date.today().isoformat(),
            ),
            TenderItem(
                title="风电项目中标公示",
                url="https://example.com/notice/2",
                source="测试平台",
                published_at=date.today().isoformat(),
            ),
        ]
    )
    notifier = RecordingNotifier()
    pipeline.notifier = notifier

    summary = pipeline.push_pending(limit=1)

    assert summary == {"notified": 1}
    assert notifier.sent == ["光伏项目采购招标公告"]


def test_push_pending_skips_non_today_items_by_default() -> None:
    pipeline = TenderPipeline(
        {
            "database_path": fresh_test_database("notification-non-today.sqlite3"),
            "webhook_url": "",
            "request_timeout": 1,
            "demo_source_enabled": False,
            "allow_demo_notifications": False,
            "notify_today_only": True,
            "keywords": {},
            "companies": [],
            "sources": [],
        }
    )
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    pipeline.storage.save_many(
        [
            TenderItem(
                title="风电项目中标公示",
                url="https://example.com/notice/old",
                source="测试平台",
                published_at=yesterday,
            )
        ]
    )
    notifier = RecordingNotifier()
    pipeline.notifier = notifier

    summary = pipeline.push_pending()

    assert summary == {"notified": 0}
    assert notifier.sent == []


def test_preview_today_returns_messages_without_notifying() -> None:
    pipeline = TenderPipeline(
        {
            "database_path": fresh_test_database("preview-today.sqlite3"),
            "webhook_url": "",
            "request_timeout": 1,
            "demo_source_enabled": False,
            "allow_demo_notifications": False,
            "keywords": {
                "must_include": ["招标", "采购"],
                "categories": {"generation": ["光伏", "风电"], "storage": ["储能"]},
            },
            "companies": [],
            "sources": [],
        }
    )
    pipeline.crawl_items = lambda: [
        TenderItem(
            title="光伏项目采购招标公告",
            url="https://example.com/pv",
            source="测试平台",
            published_at=date.today().isoformat(),
            matched_keywords=["光伏", "采购", "招标"],
        ),
        TenderItem(
            title="储能项目采购招标公告",
            url="https://example.com/storage",
            source="测试平台",
            published_at=date.today().isoformat(),
            matched_keywords=["储能", "采购", "招标"],
        ),
    ]

    result = pipeline.preview_today(topics=["光伏", "风电"])

    assert result["crawled"] == 1
    assert result["inserted"] == 1
    assert len(result["messages"]) == 1
    assert "光伏项目采购招标公告" in result["messages"][0]
