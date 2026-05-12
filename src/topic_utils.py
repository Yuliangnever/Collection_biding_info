from __future__ import annotations

import re
from copy import deepcopy


DEFAULT_TOPICS = ["光伏", "风电", "储能", "柔性支架", "漂浮"]


def parse_topics(raw_text: str | None) -> list[str]:
    if not raw_text:
        return DEFAULT_TOPICS.copy()
    topics = [topic.strip() for topic in re.split(r"[\s,，、;；]+", raw_text)]
    return [topic for topic in topics if topic] or DEFAULT_TOPICS.copy()


def settings_with_topics(settings: dict[str, object], topics: list[str]) -> dict[str, object]:
    updated = deepcopy(settings)
    keywords = dict(updated.get("keywords", {}))
    keywords["target_topics"] = topics
    updated["keywords"] = keywords
    return updated

