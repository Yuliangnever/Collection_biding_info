from __future__ import annotations

from collections.abc import Iterable

from src.models import TenderItem


def _flatten_keyword_groups(groups: dict[str, object]) -> list[str]:
    keywords: list[str] = []
    for key, value in groups.items():
        if key == "must_include":
            continue
        if isinstance(value, list):
            keywords.extend(str(item) for item in value)
    return keywords


def enrich_matches(
    item: TenderItem,
    keyword_config: dict[str, object],
    companies: Iterable[dict[str, object]],
) -> TenderItem:
    text = item.title
    must_include = [str(value) for value in keyword_config.get("must_include", [])]
    category_keywords = _flatten_keyword_groups(keyword_config)

    if must_include and not any(keyword in text for keyword in must_include):
        return item

    item.matched_keywords = [keyword for keyword in category_keywords if keyword in text]

    matched_companies: list[str] = []
    for company in companies:
        canonical_name = str(company.get("name", ""))
        aliases = [canonical_name, *[str(alias) for alias in company.get("aliases", [])]]
        if any(alias and alias in text for alias in aliases):
            matched_companies.append(canonical_name)
    item.matched_companies = matched_companies
    return item

