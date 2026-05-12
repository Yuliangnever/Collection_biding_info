from __future__ import annotations

from typing import Any

import requests

from src.models import TenderItem


class WebhookNotifier:
    def __init__(self, webhook_url: str, timeout: int = 20) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send_text(self, content: str) -> bool:
        if not self.webhook_url:
            return False

        payload: dict[str, Any] = {
            "msgtype": "text",
            "text": {"content": content},
        }
        response = requests.post(self.webhook_url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        result = response.json()
        if result.get("errcode") != 0:
            raise RuntimeError(f"WeCom webhook failed: {result}")
        return True

    def send_test_message(self) -> bool:
        return self.send_text(
            "\n".join(
                [
                    "企业微信机器人测试",
                    "Energy Tender Monitor 已连接成功。",
                    "这是一条测试消息，不代表真实招标信息。",
                ]
            )
        )

    def send(self, item: TenderItem) -> bool:
        content = "\n".join(
            [
                "招标信息提醒",
                "",
                f"标题：{item.title}",
                f"来源：{item.source}",
                f"发布时间：{item.published_at}",
                f"关键词：{'、'.join(item.matched_keywords) or '无'}",
                f"匹配公司：{'、'.join(item.matched_companies) or '无'}",
                f"链接：{item.url}",
            ]
        )
        return self.send_text(content)

