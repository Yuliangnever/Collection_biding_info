from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class TenderItem:
    title: str
    url: str
    source: str
    published_at: str
    matched_keywords: list[str] = field(default_factory=list)
    matched_companies: list[str] = field(default_factory=list)
    notified: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def dedupe_key(self) -> str:
        return f"{self.source}|{self.url}"

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "matched_keywords": self.matched_keywords,
            "matched_companies": self.matched_companies,
            "notified": self.notified,
            "created_at": self.created_at,
        }

