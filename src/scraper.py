from __future__ import annotations

from datetime import date
from typing import Protocol

from src.models import TenderItem
from src.source_config import TenderSource


class TenderScraper(Protocol):
    source: str

    def crawl(self) -> list[TenderItem]:
        ...


class DemoTenderScraper:
    source = "示例数据源"

    def crawl(self) -> list[TenderItem]:
        today = date.today().isoformat()
        return [
            TenderItem(
                title="国家电网输电线路设备采购招标公告",
                url="demo://grid-001",
                source=self.source,
                published_at=today,
            ),
            TenderItem(
                title="南方电网储能系统项目中标候选人公示",
                url="demo://storage-002",
                source=self.source,
                published_at=today,
            ),
        ]


class ConfiguredSourceScraper:
    def __init__(self, source: TenderSource, timeout: int = 20) -> None:
        self.config = source
        self.source = source.platform
        self.timeout = timeout

    def crawl(self) -> list[TenderItem]:
        # Framework placeholder: each platform needs a parser matched to its page
        # structure, dynamic loading behavior, and access rules.
        return []


def build_scrapers(
    sources: list[TenderSource],
    *,
    request_timeout: int,
    demo_source_enabled: bool,
) -> list[TenderScraper]:
    scrapers: list[TenderScraper] = []
    if demo_source_enabled:
        scrapers.append(DemoTenderScraper())
    scrapers.extend(
        ConfiguredSourceScraper(source, timeout=request_timeout) for source in sources
    )
    return scrapers
