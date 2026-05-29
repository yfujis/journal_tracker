from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_dotenv(dotenv_path: Path = Path(".env")) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class AppConfig:
    feeds_file: Path
    state_db: Path
    poll_interval_minutes: int
    max_items_per_feed: int
    dry_run: bool
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_username: str
    smtp_password: str
    smtp_from: str
    notify_to: list[str]
    subject_prefix: str

    @staticmethod
    def from_env() -> "AppConfig":
        _load_dotenv()
        return AppConfig(
            feeds_file=Path(os.getenv("FEEDS_FILE", "feeds.txt")),
            state_db=Path(os.getenv("STATE_DB", "data/rss_state.db")),
            poll_interval_minutes=int(os.getenv("POLL_INTERVAL_MINUTES", "60")),
            max_items_per_feed=int(os.getenv("MAX_ITEMS_PER_FEED", "30")),
            dry_run=_to_bool(os.getenv("DRY_RUN", "false"), default=False),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_use_tls=_to_bool(os.getenv("SMTP_USE_TLS", "true"), default=True),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", ""),
            notify_to=_split_csv(os.getenv("NOTIFY_TO", "")),
            subject_prefix=os.getenv("SUBJECT_PREFIX", "[RSS Alerts]"),
        )

    def validate_email_settings(self) -> None:
        missing = []
        if not self.smtp_host:
            missing.append("SMTP_HOST")
        if not self.smtp_from:
            missing.append("SMTP_FROM")
        if not self.notify_to:
            missing.append("NOTIFY_TO")

        if missing:
            names = ", ".join(missing)
            raise ValueError(f"Missing required email settings: {names}")
