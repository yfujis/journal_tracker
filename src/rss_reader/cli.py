from __future__ import annotations

import argparse
import logging
import time

from .config import AppConfig
from .service import RSSNotificationService


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Poll RSS feeds and send email notifications for new items."
    )
    parser.add_argument(
        "command",
        choices=["run-once", "daemon"],
        nargs="?",
        default="run-once",
        help="run-once: check feeds once, daemon: check repeatedly",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    config = AppConfig.from_env()
    service = RSSNotificationService(config)

    if args.command == "run-once":
        service.run_once()
        return

    interval_seconds = max(config.poll_interval_minutes, 1) * 60
    logging.getLogger(__name__).info(
        "Starting daemon mode with interval=%s minute(s)", config.poll_interval_minutes
    )
    while True:
        service.run_once()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
