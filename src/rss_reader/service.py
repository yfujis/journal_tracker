from __future__ import annotations

import logging

from .config import AppConfig
from .feeds import fetch_entries, read_feed_urls
from .notifier import EmailNotifier
from .storage import SeenEntriesStore

logger = logging.getLogger(__name__)


class RSSNotificationService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = SeenEntriesStore(config.state_db)
        self.notifier = EmailNotifier(config)

    def run_once(self) -> int:
        urls = read_feed_urls(self.config.feeds_file)
        if not urls:
            logger.warning("No RSS feeds configured.")
            return 0

        all_new = []
        for url in urls:
            try:
                entries = fetch_entries(url, max_items=self.config.max_items_per_feed)
                new_entries = self.store.filter_and_save_new(entries)
                logger.info(
                    "Feed checked: %s | total=%s new=%s",
                    url,
                    len(entries),
                    len(new_entries),
                )
                all_new.extend(new_entries)
            except Exception as exc:
                logger.exception("Failed to process feed %s: %s", url, exc)

        if all_new:
            self.notifier.send_digest(all_new)
            logger.info("Sent notification with %s new entries", len(all_new))
        else:
            logger.info("No new entries found.")

        return len(all_new)
