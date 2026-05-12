from __future__ import annotations

from datetime import date

from src.models import TenderItem
from src.notifier import WebhookNotifier
from src.parser import enrich_matches
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
        notified = self._notify_pending(limit=notify_limit) if notify else 0
        return {"crawled": len(enriched_items), "inserted": inserted, "notified": notified}

    def preview_today(self, topics: list[str]) -> dict[str, object]:
        today = date.today().isoformat()
        items = [
            item
            for item in self.crawl_items()
            if item.published_at == today
            and any(topic in item.title or topic in item.matched_keywords for topic in topics)
        ]
        inserted = self.storage.save_many(items)
        messages = [self.notifier.format_tender_message(item) for item in items]
        return {
            "date": today,
            "topics": topics,
            "crawled": len(items),
            "inserted": inserted,
            "messages": messages,
        }

    def push_pending(self, limit: int | None = None) -> dict[str, int]:
        return {"notified": self._notify_pending(limit=limit)}

    def _notify_pending(self, limit: int | None = None) -> int:
        notified = 0
        allow_demo = bool(self.settings.get("allow_demo_notifications", False))
        today = date.today().isoformat()
        notify_today_only = bool(self.settings.get("notify_today_only", True))
        for item in self.storage.list_pending():
            if limit is not None and notified >= limit:
                break
            if item.source == DemoTenderScraper.source and not allow_demo:
                continue
            if not is_procurement_notice(item.title):
                continue
            if notify_today_only and item.published_at != today:
                continue
            if self.notifier.send(item):
                self.storage.mark_notified(item)
                notified += 1
        return notified
