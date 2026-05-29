from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import re
from time import mktime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import feedparser

from .models import FeedEntry


NATURE_TYPE_ALIASES = {
    "article": "Article",
    "book review": "Book Review",
    "books & arts": "Books & Arts",
    "books and arts": "Books & Arts",
    "books received": "Books Received",
    "correspondence": "Correspondence",
    "editorial": "Editorial",
    "erratum": "Erratum",
    "letter": "Letter",
    "matters arising": "Matters Arising",
    "miscellany": "Miscellany",
    "nature briefing": "Nature Briefing",
    "news": "News",
    "news & views": "News & Views",
    "news and views": "News & Views",
    "news feature": "News Feature",
    "news in brief": "News in Brief",
    "obituary": "Obituary",
    "opinion": "Opinion",
    "research highlight": "Research Highlight",
    "research highlights": "Research Highlights",
    "scientific correspondence": "Scientific Correspondence",
    "author correction": "Author Correction",
    "publisher correction": "Publisher Correction",
}

SCIENCE_TYPE_ALIASES = {
    "research article": "Research Articles",
    "research articles": "Research Articles",
    "report": "Reports",
    "reports": "Reports",
    "review": "Reviews",
    "reviews": "Reviews",
    "perspective": "Perspectives",
    "perspectives": "Perspectives",
    "policy forum": "Policy Forum",
    "editorial": "Editorials",
    "editorials": "Editorials",
    "letter": "Letters",
    "letters": "Letters",
    "technical comment": "Technical Comments",
    "technical comments": "Technical Comments",
    "news": "News",
    "news feature": "News Features",
    "news features": "News Features",
    "news focus": "News Focus",
    "careers": "Careers",
    "books et al.": "Books et al.",
    "book et al.": "Books et al.",
}


def read_feed_urls(feeds_file: Path) -> list[str]:
    if not feeds_file.exists():
        raise FileNotFoundError(
            f"Feed file not found at {feeds_file}. Create it with one feed URL per line."
        )

    urls: list[str] = []
    for raw_line in feeds_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    return urls


def _parse_published(entry: dict) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)


def _parse_authors(entry: dict) -> list[str]:
    authors = entry.get("authors")
    if authors:
        names = [str(author.get("name", "")).strip() for author in authors]
        return [name for name in names if name]

    author = str(entry.get("author", "")).strip()
    if not author:
        return []

    if "," in author:
        return [name.strip() for name in author.split(",") if name.strip()]
    if " and " in author.lower():
        # A small fallback for feeds that join names with "and".
        raw_names = author.replace(" and ", "|and|")
        return [name.strip() for name in raw_names.split("|and|") if name.strip()]

    return [author]


def _normalize_article_type(raw_type: str) -> str:
    value = raw_type.strip()
    if not value:
        return "Other"
    lowered = value.lower()
    mapping = {
        "research article": "Research Articles",
        "review": "Review",
        "author correction": "Author Correction",
        "publisher correction": "Publisher Correction",
        "news": "News",
        "editorial": "Editorial",
        "perspective": "Perspective",
        "commentary": "Commentary",
        "letter": "Letter",
        "book et al.": "Books et al.",
        "books et al.": "Books et al.",
    }
    if lowered in mapping:
        return mapping[lowered]

    if lowered in SCIENCE_TYPE_ALIASES:
        return SCIENCE_TYPE_ALIASES[lowered]

    if lowered in NATURE_TYPE_ALIASES:
        return NATURE_TYPE_ALIASES[lowered]

    return value


@lru_cache(maxsize=512)
def _fetch_url_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; rss-reader-bot/0.1)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")


def _extract_nature_type_from_html(html: str) -> str | None:
    patterns = [
        r'name="dc\.type"\s+content="([^"]+)"',
        r'property="article:section"\s+content="([^"]+)"',
        r'"articleType"\s*:\s*"([^"]+)"',
        r'"article_type"\s*:\s*"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return _normalize_article_type(match.group(1))
    return None


def _infer_nature_article_type(link: str, title: str) -> str | None:
    parsed = urlparse(link)
    host = (parsed.netloc or "").lower()
    if "nature.com" not in host or "/articles/" not in parsed.path:
        return None

    try:
        html = _fetch_url_text(link)
        html_type = _extract_nature_type_from_html(html)
        if html_type:
            return html_type
    except Exception:
        pass

    # Fallback title-based extraction for Nature feeds.
    if ":" in title:
        prefix = title.split(":", 1)[0].strip()
        normalized = _normalize_article_type(prefix)
        if normalized != "Other":
            return normalized

    return None


def _parse_article_type(entry: dict) -> str:
    dc_type = str(entry.get("dc_type", "")).strip()
    if dc_type:
        return _normalize_article_type(dc_type)

    title = str(entry.get("title", "")).strip()
    link = str(entry.get("link", "")).strip()

    nature_type = _infer_nature_article_type(link, title)
    if nature_type:
        return nature_type

    if ":" in title:
        prefix = title.split(":", 1)[0].strip()
        prefixed_type = _normalize_article_type(prefix)
        if prefixed_type != "Other":
            return prefixed_type

    link_lower = link.lower()
    if re.search(r"/articles/s\d", link_lower):
        return "Research Articles"
    if re.search(r"/articles/d\d", link_lower):
        return "News"

    return "Other"


def fetch_entries(feed_url: str, max_items: int) -> list[FeedEntry]:
    parsed = feedparser.parse(feed_url)
    feed_title = parsed.feed.get("title", feed_url)

    entries: list[FeedEntry] = []
    for entry in parsed.entries[:max_items]:
        title = (entry.get("title") or "Untitled").strip()
        link = (entry.get("link") or "").strip()
        entry_id = (entry.get("id") or link or title).strip()
        entries.append(
            FeedEntry(
                article_type=_parse_article_type(entry),
                feed_url=feed_url,
                feed_title=feed_title,
                title=title,
                authors=_parse_authors(entry),
                link=link,
                entry_id=entry_id,
                published=_parse_published(entry),
            )
        )

    return entries
