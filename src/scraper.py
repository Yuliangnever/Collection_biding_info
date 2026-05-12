from __future__ import annotations

from datetime import date

from src.models import TenderItem


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

