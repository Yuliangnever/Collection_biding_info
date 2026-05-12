from pathlib import Path

from src.pipeline import TenderPipeline


def test_pipeline_crawls_and_persists(tmp_path: Path) -> None:
    pipeline = TenderPipeline(
        {
            "database_path": str(tmp_path / "tenders.sqlite3"),
            "webhook_url": "",
            "request_timeout": 1,
            "keywords": {
                "must_include": ["招标", "中标"],
                "grid": ["输电"],
                "storage": ["储能"],
            },
            "companies": [],
        }
    )

    summary = pipeline.run_once(notify=False)

    assert summary["crawled"] == 2
    assert summary["inserted"] == 2
    assert len(pipeline.storage.list_latest()) == 2

