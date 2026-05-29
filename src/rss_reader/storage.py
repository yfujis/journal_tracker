from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .models import FeedEntry


class SeenEntriesStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_entries (
                    fingerprint TEXT PRIMARY KEY,
                    feed_url TEXT NOT NULL,
                    feed_title TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    published TEXT,
                    seen_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def filter_and_save_new(self, entries: list[FeedEntry]) -> list[FeedEntry]:
        if not entries:
            return []

        fingerprints = [entry.fingerprint for entry in entries]
        placeholders = ",".join("?" for _ in fingerprints)

        with closing(self._connect()) as conn:
            existing: set[str] = set()
            cursor = conn.execute(
                f"SELECT fingerprint FROM seen_entries WHERE fingerprint IN ({placeholders})",
                fingerprints,
            )
            existing.update(row[0] for row in cursor.fetchall())

            new_entries = [entry for entry in entries if entry.fingerprint not in existing]
            if not new_entries:
                return []

            now = datetime.now(timezone.utc).isoformat()
            conn.executemany(
                """
                INSERT INTO seen_entries (
                    fingerprint, feed_url, feed_title, title, link, published, seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry.fingerprint,
                        entry.feed_url,
                        entry.feed_title,
                        entry.title,
                        entry.link,
                        entry.published.isoformat() if entry.published else None,
                        now,
                    )
                    for entry in new_entries
                ],
            )
            conn.commit()

        return new_entries
