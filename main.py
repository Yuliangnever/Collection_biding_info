from __future__ import annotations

import argparse
import json

from src.config_loader import load_settings
from src.pipeline import TenderPipeline
from src.scheduler import run_forever


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Energy tender monitoring CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run-once", help="crawl, persist, and notify")
    subparsers.add_parser("crawl-only", help="crawl and persist without notifying")
    subparsers.add_parser("push-pending", help="send pending notifications")

    latest = subparsers.add_parser("list-latest", help="print latest tender items")
    latest.add_argument("--limit", type=int, default=10)

    schedule = subparsers.add_parser("schedule", help="run continuously")
    schedule.add_argument("--interval-minutes", type=int, default=30)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings()
    pipeline = TenderPipeline(settings)
    startup_sent = pipeline.send_startup_message(args.command)
    if startup_sent:
        print("企业微信启动通知已发送")
    else:
        print("未配置 WEBHOOK_URL，跳过企业微信启动通知")

    if args.command == "run-once":
        summary = pipeline.run_once(notify=True)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "crawl-only":
        summary = pipeline.run_once(notify=False)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "push-pending":
        summary = pipeline.push_pending()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "list-latest":
        items = pipeline.storage.list_latest(args.limit)
        print(json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2))
        return

    if args.command == "schedule":
        run_forever(pipeline, interval_minutes=args.interval_minutes)
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
