from __future__ import annotations

from datetime import date

from src.models import TenderItem
from src.notifier import WebhookNotifier
from src.parser import enrich_matches
from src.parser import target_topic_keywords
from src.scraper import DemoTenderScraper, build_scrapers, is_procurement_notice
from src.source_config import load_enabled_sources
from src.storage import TenderStorage


class TenderPipeline:
    def __init__(self, settings: dict[str, object]) -> None:
        self.settings = settings
        self.storage = TenderStorage(str(settings["database_path"]))
        sources = load_enabled_sources(settings.get("sources", []))
        self.scrapers = build_scrapers(
            sources,
            keyword_config=dict(settings.get("keywords", {})),
            request_timeout=int(settings.get("request_timeout", 20)),
            demo_source_enabled=bool(settings.get("demo_source_enabled", True)),
            max_items_per_source=int(settings.get("max_items_per_source", 50)),
            max_pages_per_source=int(settings.get("max_pages_per_source", 5)),
        )
        self.notifier = WebhookNotifier(
            webhook_url=str(settings.get("webhook_url", "")),
            timeout=int(settings.get("request_timeout", 20)),
        )

    def send_test_message(self) -> dict[str, int]:
        return {"sent": int(self.notifier.send_test_message())}

    def crawl_items(self) -> list[TenderItem]:
        raw_items: list[TenderItem] = []
        for scraper in self.scrapers:
            raw_items.extend(scraper.crawl())
        return [
            enrich_matches(
                item,
                keyword_config=dict(self.settings.get("keywords", {})),
                companies=list(self.settings.get("companies", [])),
            )
            for item in raw_items
        ]

    def run_once(self, notify: bool) -> dict[str, int]:
        enriched_items = self.crawl_items()
        inserted = self.storage.save_many(enriched_items)
        notify_limit = int(self.settings.get("max_notifications_per_run", 10))
        topics = target_topic_keywords(dict(self.settings.get("keywords", {})))
        notified = self._notify_pending(limit=notify_limit, topics=topics) if notify else 0
        return {"crawled": len(enriched_items), "inserted": inserted, "notified": notified}

    def preview_today(self, topics: list[str]) -> dict[str, object]:
        today = date.today().isoformat()
        return self.preview_range(topics, today, today)

    def preview_range(
        self,
        topics: list[str],
        start_date: str,
        end_date: str,
    ) -> dict[str, object]:
        items = self._filter_date_range_topics(
            self.crawl_items(),
            topics,
            start_date,
            end_date,
        )
        inserted = self.storage.save_many(items)
        messages = [self.notifier.format_tender_message(item) for item in items]
        return {
            "start_date": start_date,
            "end_date": end_date,
            "topics": topics,
            "crawled": len(items),
            "inserted": inserted,
            "messages": messages,
            "items": [item.to_dict() for item in items],
        }

    def push_pending(self, limit: int | None = None) -> dict[str, int]:
        return {"notified": self._notify_pending(limit=limit)}

    def notify_today_topics(
        self,
        topics: list[str],
        limit: int | None = None,
    ) -> dict[str, int]:
        items = self._filter_today_topics(self.crawl_items(), topics)
        inserted = self.storage.save_many(items)
        notified = self._notify_pending(limit=limit, topics=topics)
        return {"crawled": len(items), "inserted": inserted, "notified": notified}

    def notify_range_topics(
        self,
        topics: list[str],
        start_date: str,
        end_date: str,
        limit: int | None = None,
    ) -> dict[str, int]:
        items = self._filter_date_range_topics(
            self.crawl_items(),
            topics,
            start_date,
            end_date,
        )
        inserted = self.storage.save_many(items)
        notified = self._notify_pending(
            limit=limit,
            topics=topics,
            start_date=start_date,
            end_date=end_date,
        )
        return {"crawled": len(items), "inserted": inserted, "notified": notified}

    def _notify_pending(
        self,
        limit: int | None = None,
        topics: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> int:
        notified = 0
        allow_demo = bool(self.settings.get("allow_demo_notifications", False))
        today = date.today().isoformat()
        notify_today_only = bool(self.settings.get("notify_today_only", True))
        if start_date and end_date:
            notify_today_only = False
        for item in self.storage.list_pending():
            if limit is not None and notified >= limit:
                break
            if item.source == DemoTenderScraper.source and not allow_demo:
                continue
            if not is_procurement_notice(item.title):
                continue
            if notify_today_only and item.published_at != today:
                continue
            if start_date and end_date and not (start_date <= item.published_at <= end_date):
                continue
            if topics and not self._matches_topics(item, topics):
                continue
            if self.notifier.send(item):
                self.storage.mark_notified(item)
                notified += 1
        return notified

    @staticmethod
    def _matches_topics(item: TenderItem, topics: list[str]) -> bool:
        return any(topic in item.title or topic in item.matched_keywords for topic in topics)

    def _filter_today_topics(
        self,
        items: list[TenderItem],
        topics: list[str],
    ) -> list[TenderItem]:
        today = date.today().isoformat()
        return self._filter_date_range_topics(items, topics, today, today)

    def _filter_date_range_topics(
        self,
        items: list[TenderItem],
        topics: list[str],
        start_date: str,
        end_date: str,
    ) -> list[TenderItem]:
        return [
            item
            for item in items
            if start_date <= item.published_at <= end_date
            and is_procurement_notice(item.title)
            and self._matches_topics(item, topics)
        ]
