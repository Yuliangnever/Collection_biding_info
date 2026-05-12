from __future__ import annotations

import time

from src.pipeline import TenderPipeline


def run_forever(pipeline: TenderPipeline, interval_minutes: int) -> None:
    interval_seconds = max(interval_minutes, 1) * 60
    while True:
        pipeline.run_once(notify=True)
        time.sleep(interval_seconds)

