from __future__ import annotations

import argparse
import json
import sys

from src.config_loader import load_settings
from src.pipeline import TenderPipeline
from src.scheduler import run_forever
from src.topic_utils import settings_with_topics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Energy tender monitoring CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run-once", help="crawl, persist, and notify")
    subparsers.add_parser("crawl-only", help="crawl and persist without notifying")
    preview_today = subparsers.add_parser(
        "preview-today",
        help="crawl today's tender notices and print message previews without notifying",
    )
    preview_today.add_argument("--topics", nargs="+", default=["光伏", "风电"])
    preview_today.add_argument("--start-date", default=None)
    preview_today.add_argument("--end-date", default=None)
    push_pending = subparsers.add_parser(
        "push-pending", help="send pending notifications"
    )
    push_pending.add_argument("--limit", type=int, default=None)
    subparsers.add_parser("test-wecom", help="send a WeCom webhook test message")

    latest = subparsers.add_parser("list-latest", help="print latest tender items")
    latest.add_argument("--limit", type=int, default=10)

    schedule = subparsers.add_parser("schedule", help="run continuously")
    schedule.add_argument("--interval-minutes", type=int, default=30)
    return parser


def _print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = build_parser().parse_args()
    settings = load_settings()
    if hasattr(args, "topics"):
        settings = settings_with_topics(settings, list(args.topics))
    pipeline = TenderPipeline(settings)

    if args.command == "test-wecom":
        _print_json(pipeline.send_test_message())
        return

    if args.command == "run-once":
        _print_json(pipeline.run_once(notify=True))
        return

    if args.command == "crawl-only":
        _print_json(pipeline.run_once(notify=False))
        return

    if args.command == "preview-today":
        if args.start_date and args.end_date:
            result = pipeline.preview_range(
                topics=args.topics,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            date_label = f"{result['start_date']} 至 {result['end_date']}"
        else:
            result = pipeline.preview_today(topics=args.topics)
            date_label = str(result["start_date"])
        print(
            f"招标信息预览：日期={date_label}，主题={','.join(result['topics'])}，"
            f"抓取到={result['crawled']}，新增入库={result['inserted']}，不会推送企业微信"
        )
        messages = result["messages"]
        if not messages:
            print("没有找到符合条件的今日招标信息。")
            return
        for index, message in enumerate(messages, start=1):
            print("\n" + "=" * 80)
            print(f"消息 {index}")
            print("=" * 80)
            print(message)
        return

    if args.command == "push-pending":
        _print_json(pipeline.push_pending(limit=args.limit))
        return

    if args.command == "list-latest":
        items = pipeline.storage.list_latest(args.limit)
        _print_json([item.to_dict() for item in items])
        return

    if args.command == "schedule":
        run_forever(pipeline, interval_minutes=args.interval_minutes)
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
