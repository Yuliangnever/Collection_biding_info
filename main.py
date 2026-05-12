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
    subparsers.add_parser("test-wecom", help="send a WeCom webhook test message")

    latest = subparsers.add_parser("list-latest", help="print latest tender items")
    latest.add_argument("--limit", type=int, default=10)

    schedule = subparsers.add_parser("schedule", help="run continuously")
    schedule.add_argument("--interval-minutes", type=int, default=30)
    return parser


def _print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings()
    pipeline = TenderPipeline(settings)
    startup_sent = pipeline.send_startup_message(args.command)
    if startup_sent:
        print("企业微信启动通知已发送")
    else:
        print("未配置 WEBHOOK_URL，跳过企业微信启动通知")

    if args.command == "test-wecom":
        _print_json(pipeline.send_test_message())
        return

    if args.command == "run-once":
        _print_json(pipeline.run_once(notify=True))
        return

    if args.command == "crawl-only":
        _print_json(pipeline.run_once(notify=False))
        return

    if args.command == "push-pending":
        _print_json(pipeline.push_pending())
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

