from src.scraper import ConfiguredSourceScraper, clean_text, extract_published_date
from src.source_config import TenderSource


class FakeResponse:
    url = "https://example.com/list"
    encoding = "utf-8"
    apparent_encoding = "utf-8"
    text = """
    <html>
      <body>
        <a href="/notice/1">光伏柔性支架采购招标公告</a>
        <a href="/notice/2">办公用品采购公告</a>
        <a href="https://example.com/notice/3">风电储能项目中标公示</a>
      </body>
    </html>
    """

    def raise_for_status(self) -> None:
        return None


def test_configured_source_scraper_extracts_relevant_links(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("src.scraper.requests.get", fake_get)
    scraper = ConfiguredSourceScraper(
        TenderSource(
            id="demo",
            group="测试",
            company="测试公司",
            platform="测试平台",
            urls=("https://example.com/list",),
        ),
        keyword_config={
            "target_topics": ["光伏", "风电", "储能", "柔性支架"],
            "must_include": ["招标", "采购", "中标", "公示"],
            "categories": {
                "generation": ["光伏", "风电"],
                "storage": ["储能"],
                "mounting": ["柔性支架"],
            },
        },
    )

    items = scraper.crawl()

    assert [item.title for item in items] == [
        "光伏柔性支架采购招标公告",
        "风电储能项目中标公示",
    ]
    assert items[0].url == "https://example.com/notice/1"
    assert items[0].source == "测试平台"


def test_configured_source_scraper_rejects_non_target_procurement(monkeypatch) -> None:
    class BroadProcurementResponse(FakeResponse):
        text = """
        <a href="/notice/1">设备检修维护服务公开招标公告</a>
        <a href="/notice/2">漂浮光伏项目采购公告</a>
        """

    def fake_get(*args, **kwargs):
        return BroadProcurementResponse()

    monkeypatch.setattr("src.scraper.requests.get", fake_get)
    scraper = ConfiguredSourceScraper(
        TenderSource(
            id="demo",
            group="测试",
            company="测试公司",
            platform="测试平台",
            urls=("https://example.com/list",),
        ),
        keyword_config={
            "target_topics": ["光伏", "风电", "储能", "柔性支架", "漂浮光伏"],
            "must_include": ["招标", "采购", "中标", "公示"],
            "categories": {"grid": ["设备"]},
        },
    )

    items = scraper.crawl()

    assert [item.title for item in items] == ["漂浮光伏项目采购公告"]


def test_extracts_published_date_from_title() -> None:
    assert extract_published_date("风电项目招标公告 2026-05-12") == "2026-05-12"
    assert extract_published_date("光伏项目中标公示 2026年5月2日") == "2026-05-02"
    assert (
        extract_published_date(
            "光伏项目采购公告",
            "https://example.com/notice/20260512/demo.html",
        )
        == "2026-05-12"
    )


def test_clean_text_removes_private_use_characters() -> None:
    assert clean_text("公告\ue638标题") == "公告标题"
