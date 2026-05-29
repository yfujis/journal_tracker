from __future__ import annotations

from datetime import datetime, timezone

from rss_reader.models import FeedEntry
from rss_reader.storage import SeenEntriesStore


def _entry(entry_id: str) -> FeedEntry:
    return FeedEntry(
        article_type="Other",
        feed_url="https://journal/rss",
        feed_title="Journal",
        title=f"Paper {entry_id}",
        authors=["A. Researcher"],
        link=f"https://paper/{entry_id}",
        entry_id=entry_id,
        published=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )


def test_filter_and_save_new_deduplicates(tmp_path) -> None:
    db_path = tmp_path / "state.db"
    store = SeenEntriesStore(db_path)

    first_batch = [_entry("1"), _entry("2")]
    second_batch = [_entry("2"), _entry("3")]

    new_first = store.filter_and_save_new(first_batch)
    new_second = store.filter_and_save_new(second_batch)

    assert [e.entry_id for e in new_first] == ["1", "2"]
    assert [e.entry_id for e in new_second] == ["3"]
