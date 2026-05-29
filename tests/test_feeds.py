from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from rss_reader.feeds import fetch_entries, read_feed_urls


def test_read_feed_urls_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    feeds_file = tmp_path / "feeds.txt"
    feeds_file.write_text("\n# comment\nhttps://a.example/rss\n\nhttps://b.example/rss\n", encoding="utf-8")

    urls = read_feed_urls(feeds_file)

    assert urls == ["https://a.example/rss", "https://b.example/rss"]


def test_fetch_entries_maps_feedparser_data(monkeypatch) -> None:
    monkeypatch.setattr("rss_reader.feeds._infer_nature_article_type", lambda *_: None)

    fake_parsed = SimpleNamespace(
        feed={"title": "Test Journal"},
        entries=[
            {
                "title": "Paper One",
                "link": "https://paper/1",
                "id": "id-1",
                "dc_type": "Research Article",
                "tags": [{"term": "Neuroscience"}, {"term": "Immunology"}],
                "authors": [{"name": "Ada Lovelace"}, {"name": "Alan Turing"}],
                "published_parsed": (2026, 5, 1, 10, 0, 0, 0, 0, -1),
            },
            {
                "title": "Author Correction: Paper Two",
                "link": "https://paper/2",
                "id": "id-2",
                "author": "Grace Hopper, Edsger Dijkstra",
            },
            {
                "title": "Paper Three",
                "link": "https://www.nature.com/articles/d41586-026-01589-3",
                "id": "id-3",
            },
        ],
    )

    monkeypatch.setattr("rss_reader.feeds.feedparser.parse", lambda _: fake_parsed)

    items = fetch_entries("https://journal/rss", max_items=5)

    assert len(items) == 3
    assert items[0].article_type == "Research Articles"
    assert items[0].feed_title == "Test Journal"
    assert items[0].title == "Paper One"
    assert items[0].authors == ["Ada Lovelace", "Alan Turing"]
    assert items[0].link == "https://paper/1"
    assert items[0].published is not None
    assert items[1].article_type == "Author Correction"
    assert items[1].authors == ["Grace Hopper", "Edsger Dijkstra"]
    assert items[1].published is None
    assert items[2].article_type == "News"


def test_fetch_entries_uses_nature_type_when_available(monkeypatch) -> None:
    fake_parsed = SimpleNamespace(
        feed={"title": "Nature"},
        entries=[
            {
                "title": "Some title",
                "link": "https://www.nature.com/articles/d41586-026-01589-3",
                "id": "id-1",
            }
        ],
    )

    monkeypatch.setattr("rss_reader.feeds.feedparser.parse", lambda _: fake_parsed)
    monkeypatch.setattr(
        "rss_reader.feeds._infer_nature_article_type", lambda *_: "Research Highlight"
    )

    items = fetch_entries("https://www.nature.com/nature.rss", max_items=5)

    assert items[0].article_type == "Research Highlight"
