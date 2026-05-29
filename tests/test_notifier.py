from __future__ import annotations

from datetime import datetime, timezone

from rss_reader.config import AppConfig
from rss_reader.models import FeedEntry
from rss_reader.notifier import EmailNotifier


def _config() -> AppConfig:
    return AppConfig(
        feeds_file=None,
        state_db=None,
        poll_interval_minutes=60,
        max_items_per_feed=30,
        dry_run=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_use_tls=True,
        smtp_username="",
        smtp_password="",
        smtp_from="alerts@example.com",
        notify_to=["you@example.com"],
        subject_prefix="[Alerts]",
    )


def test_build_plain_text_groups_by_feed_title() -> None:
    notifier = EmailNotifier(_config())
    entries = [
        FeedEntry(
            feed_url="u1",
            feed_title="Nature",
            article_type="Author Correction",
            title="Paper A",
            authors=["Ada Lovelace", "Alan Turing"],
            link="https://a",
            entry_id="a",
            published=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
        ),
        FeedEntry(
            feed_url="u1",
            feed_title="Nature",
            article_type="Research Articles",
            title="Paper B",
            authors=[f"Author {i}" for i in range(1, 12)],
            link="https://b",
            entry_id="b",
            published=None,
        ),
    ]

    text = notifier._build_plain_text(entries)

    assert "New publications found: 2" in text
    assert "Nature (2)" in text
    assert "  Research Articles (1)" in text
    assert "  Author Correction (1)" in text
    assert "Paper A" in text
    assert "Authors: Ada Lovelace, Alan Turing" in text
    assert "... (5 omitted)" in text
    assert "Unknown date" in text
    assert text.index("  Research Articles (1)") < text.index("  Author Correction (1)")


def test_build_html_uses_hyperlinked_titles() -> None:
    notifier = EmailNotifier(_config())
    entries = [
        FeedEntry(
            feed_url="u1",
            feed_title="Nature",
            article_type="Research Articles",
            title="Paper A",
            authors=["Ada Lovelace"],
            link="https://a",
            entry_id="a",
            published=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
        )
    ]

    html = notifier._build_html(entries)

    assert '<a href="https://a">Paper A</a>' in html
    assert "Authors: Ada Lovelace" in html
    assert "<h2>Nature (1)</h2>" in html
    assert "<h3>Research Articles (1)</h3>" in html
