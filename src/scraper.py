from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
import re
from typing import Protocol
import unicodedata
from urllib.parse import urljoin

import requests

from src.models import TenderItem
from src.parser import target_topic_keywords
from src.source_config import TenderSource


class TenderScraper(Protocol):
    source: str

    def crawl(self) -> list[TenderItem]:
        ...


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


@dataclass(slots=True)
class LinkCandidate:
    title: str
    url: str


class TenderLinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._href_stack: list[str] = []
        self._text_parts: list[str] = []
        self.links: list[LinkCandidate] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_map = {key.lower(): value for key, value in attrs}
        href = attrs_map.get("href")
        if not href:
            return
        self._href_stack.append(urljoin(self.base_url, href.strip()))
        self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._href_stack:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href_stack:
            return
        href = self._href_stack.pop()
        title = clean_text(" ".join("".join(self._text_parts).split()))
        self._text_parts = []
        if title and href.startswith(("http://", "https://")):
            self.links.append(LinkCandidate(title=title, url=href))


def clean_text(text: str) -> str:
    return "".join(
        char
        for char in text
        if unicodedata.category(char) not in {"Cc", "Cf", "Co", "Cs"}
    ).strip()


def extract_published_date(title: str, url: str = "") -> str:
    match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})日?", title)
    if not match and url:
        match = re.search(r"(20\d{2})[-/.]?(\d{2})[-/.]?(\d{2})", url)
    if not match:
        return date.today().isoformat()
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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
    def __init__(
        self,
        source: TenderSource,
        *,
        keyword_config: dict[str, object],
        timeout: int = 20,
        max_items: int = 50,
        max_pages: int = 5,
    ) -> None:
        self.config = source
        self.source = source.platform
        self.timeout = timeout
        self.max_items = max_items
        self.max_pages = max_pages
        self.target_keywords = target_topic_keywords(keyword_config)

    def crawl(self) -> list[TenderItem]:
        items: list[TenderItem] = []
        seen_urls: set[str] = set()
        pages_to_visit = list(self.config.urls)
        visited_pages: set[str] = set()

        while pages_to_visit and len(visited_pages) < self.max_pages:
            page_url = pages_to_visit.pop(0)
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)

            for candidate in self._fetch_candidates(page_url):
                if self._is_listing_link(candidate) and candidate.url not in visited_pages:
                    pages_to_visit.append(candidate.url)
                if candidate.url in seen_urls:
                    continue
                if not self._is_relevant_title(candidate.title):
                    continue
                seen_urls.add(candidate.url)
                items.append(
                    TenderItem(
                        title=candidate.title,
                        url=candidate.url,
                        source=self.source,
                        published_at=extract_published_date(candidate.title, candidate.url),
                    )
                )
                if len(items) >= self.max_items:
                    return items
        return items

    def _fetch_candidates(self, url: str) -> list[LinkCandidate]:
        try:
            response = requests.get(
                url,
                headers=REQUEST_HEADERS,
                timeout=self.timeout,
            )
            if response.status_code == 412:
                print(
                    f"抓取受限：{self.source} {url} 返回 412，"
                    "该平台需要浏览器执行 JS/WAF 校验，普通 HTTP 爬虫无法直接读取。"
                )
                return []
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"抓取失败：{self.source} {url} - {exc}")
            return []

        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding
        parser = TenderLinkParser(response.url)
        parser.feed(response.text)
        return parser.links

    def _is_relevant_title(self, title: str) -> bool:
        if not any(word in title for word in ("招标", "采购", "中标", "成交", "公示")):
            return False
        return any(keyword in title for keyword in self.target_keywords)

    @staticmethod
    def _is_listing_link(candidate: LinkCandidate) -> bool:
        text = f"{candidate.title} {candidate.url}"
        listing_markers = (
            "招标公告",
            "采购公告",
            "中标公示",
            "成交公告",
            "招标采购",
            "采购信息",
            "jyxx",
            "notice",
            "bulletin",
        )
        return any(marker in text for marker in listing_markers)


def build_scrapers(
    sources: list[TenderSource],
    *,
    keyword_config: dict[str, object],
    request_timeout: int,
    demo_source_enabled: bool,
    max_items_per_source: int = 50,
    max_pages_per_source: int = 5,
) -> list[TenderScraper]:
    scrapers: list[TenderScraper] = []
    if demo_source_enabled:
        scrapers.append(DemoTenderScraper())
    scrapers.extend(
        ConfiguredSourceScraper(
            source,
            keyword_config=keyword_config,
            timeout=request_timeout,
            max_items=max_items_per_source,
            max_pages=max_pages_per_source,
        )
        for source in sources
    )
    return scrapers
