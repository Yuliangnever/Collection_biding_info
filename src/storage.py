from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.models import TenderItem


class TenderStorage:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenders (
                    dedupe_key TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    matched_keywords TEXT NOT NULL,
                    matched_companies TEXT NOT NULL,
                    notified INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_many(self, items: list[TenderItem]) -> int:
        inserted = 0
        with self._connect() as conn:
            for item in items:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO tenders (
                        dedupe_key, title, url, source, published_at,
                        matched_keywords, matched_companies, notified, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.dedupe_key(),
                        item.title,
                        item.url,
                        item.source,
                        item.published_at,
                        json.dumps(item.matched_keywords, ensure_ascii=False),
                        json.dumps(item.matched_companies, ensure_ascii=False),
                        int(item.notified),
                        item.created_at,
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def list_latest(self, limit: int = 10) -> list[TenderItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT title, url, source, published_at, matched_keywords,
                       matched_companies, notified, created_at
                FROM tenders
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def list_pending(self) -> list[TenderItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT title, url, source, published_at, matched_keywords,
                       matched_companies, notified, created_at
                FROM tenders
                WHERE notified = 0
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def mark_notified(self, item: TenderItem) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE tenders SET notified = 1 WHERE source = ? AND url = ?",
                (item.source, item.url),
            )

    @staticmethod
    def _row_to_item(row: tuple[object, ...]) -> TenderItem:
        return TenderItem(
            title=str(row[0]),
            url=str(row[1]),
            source=str(row[2]),
            published_at=str(row[3]),
            matched_keywords=json.loads(str(row[4])),
            matched_companies=json.loads(str(row[5])),
            notified=bool(row[6]),
            created_at=str(row[7]),
        )

