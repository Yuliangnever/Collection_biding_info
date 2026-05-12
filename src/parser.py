from __future__ import annotations

from collections.abc import Iterable

from src.models import TenderItem


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _collect_keywords(value: object) -> list[str]:
    keywords: list[str] = []
    if isinstance(value, list):
        for item in value:
            _append_unique(keywords, str(item))
    elif isinstance(value, dict):
        for nested_value in value.values():
            for keyword in _collect_keywords(nested_value):
                _append_unique(keywords, keyword)
    return keywords


def configured_keywords(keyword_config: dict[str, object]) -> list[str]:
    keywords: list[str] = []
    for key in ("must_include", "categories"):
        for keyword in _collect_keywords(keyword_config.get(key, [])):
            _append_unique(keywords, keyword)
    return keywords


def enrich_matches(
    item: TenderItem,
    keyword_config: dict[str, object],
    companies: Iterable[dict[str, object]],
) -> TenderItem:
    text = item.title
    all_keywords = configured_keywords(keyword_config)
    item.matched_keywords = [keyword for keyword in all_keywords if keyword in text]

    matched_companies: list[str] = []
    for company in companies:
        canonical_name = str(company.get("name", ""))
        aliases = [canonical_name, *[str(alias) for alias in company.get("aliases", [])]]
        if any(alias and alias in text for alias in aliases):
            _append_unique(matched_companies, canonical_name)
    item.matched_companies = matched_companies
    return item

