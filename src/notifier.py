from __future__ import annotations

from typing import Any

import requests

from src.models import TenderItem


class WebhookNotifier:
    def __init__(self, webhook_url: str, timeout: int = 20) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send(self, item: TenderItem) -> bool:
        if not self.webhook_url:
            return False

        payload: dict[str, Any] = {
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "published_at": item.published_at,
            "matched_keywords": item.matched_keywords,
            "matched_companies": item.matched_companies,
        }
        response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return True

