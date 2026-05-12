from __future__ import annotations

from datetime import datetime

from src.models import TenderItem
from src.notifier import WebhookNotifier
from src.parser import enrich_matches
from src.scraper import DemoTenderScraper, build_scrapers
from src.source_config import load_enabled_sources
from src.storage import TenderStorage


class TenderPipeline:
    def __init__(self, settings: dict[str, object]) -> None:
        self.settings = settings
        self.storage = TenderStorage(str(settings["database_path"]))
        sources = load_enabled_sources(settings.get("sources", []))
        self.scrapers = build_scrapers(
            sources,
            request_timeout=int(settings.get("request_timeout", 20)),
            demo_source_enabled=bool(settings.get("demo_source_enabled", True)),
        )
        self.notifier = WebhookNotifier(
            webhook_url=str(settings.get("webhook_url", "")),
            timeout=int(settings.get("request_timeout", 20)),
        )

    def send_startup_message(self, command: str) -> bool:
        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.notifier.send_text(
            "\n".join(
                [
                    "Energy Tender Monitor 已启动",
                    f"启动时间：{started_at}",
                    f"运行命令：{command}",
                ]
            )
        )

    def send_test_message(self) -> dict[str, int]:
        return {"sent": int(self.notifier.send_test_message())}

    def run_once(self, notify: bool) -> dict[str, int]:
        raw_items: list[TenderItem] = []
        for scraper in self.scrapers:
            raw_items.extend(scraper.crawl())
        enriched_items = [
            enrich_matches(
                item,
                keyword_config=dict(self.settings.get("keywords", {})),
                companies=list(self.settings.get("companies", [])),
            )
            for item in raw_items
        ]
        inserted = self.storage.save_many(enriched_items)
        notified = self._notify_pending() if notify else 0
        return {"crawled": len(raw_items), "inserted": inserted, "notified": notified}

    def push_pending(self) -> dict[str, int]:
        return {"notified": self._notify_pending()}

    def _notify_pending(self) -> int:
        notified = 0
        allow_demo = bool(self.settings.get("allow_demo_notifications", False))
        for item in self.storage.list_pending():
            if item.source == DemoTenderScraper.source and not allow_demo:
                continue
            if self.notifier.send(item):
                self.storage.mark_notified(item)
                notified += 1
        return notified
