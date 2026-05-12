from src.models import TenderItem
from src.parser import enrich_matches


def test_enrich_matches_records_keywords_and_companies() -> None:
    item = TenderItem(
        title="国家电网储能系统采购招标公告",
        url="demo://parser",
        source="demo",
        published_at="2026-05-12",
    )
    keywords = {
        "must_include": ["招标", "采购", "中标"],
        "categories": {"storage": ["储能"]},
    }
    companies = [{"name": "国家电网", "aliases": ["国网", "State Grid"]}]

    enriched = enrich_matches(item, keywords, companies)

    assert enriched.matched_keywords == ["招标", "采购", "储能"]
    assert enriched.matched_companies == ["国家电网"]

