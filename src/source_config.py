from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TenderSource:
    id: str
    group: str
    company: str
    platform: str
    urls: tuple[str, ...]
    notes: str = ""
    enabled: bool = True
    parser: str = "generic_html"
    access_note: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TenderSource":
        return cls(
            id=str(data["id"]),
            group=str(data.get("group", "")),
            company=str(data.get("company", "")),
            platform=str(data.get("platform", "")),
            urls=tuple(str(url) for url in data.get("urls", [])),
            notes=str(data.get("notes", "")),
            enabled=bool(data.get("enabled", True)),
            parser=str(data.get("parser", "generic_html")),
            access_note=str(data.get("access_note", "")),
        )


def load_enabled_sources(raw_sources: object) -> list[TenderSource]:
    if not isinstance(raw_sources, list):
        return []
    sources = [TenderSource.from_dict(item) for item in raw_sources if isinstance(item, dict)]
    return [source for source in sources if source.enabled]
