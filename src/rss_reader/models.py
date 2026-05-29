from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256


@dataclass(frozen=True)
class FeedEntry:
    article_type: str
    feed_url: str
    feed_title: str
    title: str
    authors: list[str]
    link: str
    entry_id: str
    published: datetime | None

    @property
    def fingerprint(self) -> str:
        stable_id = self.entry_id or self.link or self.title
        base = f"{self.feed_url}|{stable_id}"
        return sha256(base.encode("utf-8")).hexdigest()
