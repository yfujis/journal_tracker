# RSS Reader + Email Notifier for Journal Updates

This project monitors journal RSS/Atom feeds and sends an email digest whenever new publications appear.

It is designed for researchers who want a Feedly-like workflow focused on scientific updates, with simple self-hosted automation.

## What It Does

- Polls multiple RSS/Atom feeds.
- Tracks seen entries in SQLite so each item is emailed once.
- Sends a single digest email with all new items found in a polling run.
- Supports one-time runs and continuous daemon mode.
- Includes scheduler setup scripts for Windows and macOS.

## Project Layout

```text
.
├─ src/rss_reader/
│  ├─ cli.py              # CLI entrypoint (run-once / daemon)
│  ├─ config.py           # .env and environment variable loading
│  ├─ feeds.py            # RSS feed discovery and parsing
│  ├─ storage.py          # SQLite deduplication store
│  ├─ notifier.py         # SMTP email digest sender
│  └─ service.py          # orchestration logic
├─ tests/                 # unit tests
├─ feeds.example.txt      # sample feed list
├─ .env.example           # sample config
├─ run.ps1                # Windows one-shot runner
├─ setup_task.ps1         # Windows Task Scheduler setup
├─ run.sh                 # macOS/Linux one-shot runner
└─ setup_launchd.sh       # macOS launchd setup
```

## Requirements

- Python 3.10+
- Network access to your feed URLs and SMTP server
- SMTP account (institutional mail, Gmail app password, SendGrid, Mailgun, etc.)

## Quick Start

### Windows (PowerShell)

1. Create and activate virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create local config files.

```powershell
Copy-Item .env.example .env
Copy-Item feeds.example.txt feeds.txt
```

4. Edit `.env` and `feeds.txt`.

5. Start with a dry run.

```powershell
$env:PYTHONPATH = "src"
python -m rss_reader run-once --verbose
```

### macOS/Linux

1. Create and activate virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

| SMTP_PORT | No | 587 | SMTP server port |
| SMTP_USE_TLS | No | true | Enable STARTTLS |
| SMTP_USERNAME | No | - | SMTP login username |
| SMTP_PASSWORD | No | - | SMTP login password |
| SMTP_FROM | Yes* | - | Sender address |
| NOTIFY_TO | Yes* | - | Comma-separated recipients |
| SUBJECT_PREFIX | No | [RSS Alerts] | Email subject prefix |

`*` Required only when `DRY_RUN=false`.

## Feed File Format

Add one RSS/Atom URL per line in `feeds.txt`.

```text
https://www.nature.com/nature.rss
https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science
```

Lines starting with `#` and blank lines are ignored.

Digest ordering rule:

- Entries are grouped by journal first, then by article type inside each journal.
- Article type is inferred per article from feed metadata (`dc_type`) and title/link heuristics.

## Running Modes

### Run Once

Use this for ad hoc checks and for schedulers.

```bash
python -m rss_reader run-once --verbose
```

### Daemon Mode

Runs continuously and polls every `POLL_INTERVAL_MINUTES`.

```bash
python -m rss_reader daemon --verbose
```

## Web Dashboard (GitHub Pages)

This repository includes a static dashboard in [docs/index.html](docs/index.html) that displays your feeds in a Feedly-like layout.

How it works:

- [scripts/build_feed_json.py](scripts/build_feed_json.py) fetches feeds and generates [docs/feed-data.json](docs/feed-data.json).
- [docs/app.js](docs/app.js) renders journals, article-type groups, search, and filters.
- [.github/workflows/update_feed_data.yml](.github/workflows/update_feed_data.yml) refreshes feed data hourly.

Run locally to build dashboard data:

```bash
python scripts/build_feed_json.py --feeds-file feeds.txt --output docs/feed-data.json --max-items 25
```

Publish from this repo (project page):

1. Push these files to GitHub.
2. In GitHub repo settings, open Pages.
3. Set source to `Deploy from a branch`.
4. Choose branch `main` and folder `/docs`.

Your URL will be like:

- `https://yfujis.github.io/<repo-name>/`

Publish at root domain `https://yfujis.github.io/`:

- Put the `docs` site files (`index.html`, `styles.css`, `app.js`, `feed-data.json`) in the root of a repository named `yfujis.github.io`.
- Copy the workflow and script there as well if you want automatic hourly updates.

## Scheduling

### Windows Task Scheduler

Create a recurring task:

```powershell
.\setup_task.ps1 -TaskName "Journal RSS Alerts" -EveryMinutes 60
```

Remove the task:

```powershell
Unregister-ScheduledTask -TaskName "Journal RSS Alerts" -Confirm:$false
```

Notes:

- Runs as your current user account.
- Calls `run.ps1`, which automatically uses `.venv` when available.
- Keep the project path unchanged after registration.

### macOS launchd

1. Make scripts executable.

```bash
chmod +x run.sh setup_launchd.sh
```

2. Install launch agent (hourly = 3600 seconds).

```bash
./setup_launchd.sh 3600
```

3. Monitor logs.

```bash
tail -f logs/launchd.out.log
tail -f logs/launchd.err.log
```

4. Remove launch agent.

```bash
launchctl unload "$HOME/Library/LaunchAgents/com.${USER}.journal-rss-alerts.plist"
rm "$HOME/Library/LaunchAgents/com.${USER}.journal-rss-alerts.plist"
```

## Testing

Install dev dependencies and run tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

Current tests cover:

- Feed URL parsing behavior
- SQLite deduplication behavior
- Email digest formatting behavior

## Troubleshooting

### No email arrives

- Set `DRY_RUN=false`.
- Verify `SMTP_HOST`, `SMTP_FROM`, and `NOTIFY_TO`.
- Confirm your SMTP provider allows app-based SMTP access.
- Try running `run-once --verbose` manually and inspect logs/errors.

### Duplicate notifications

- Ensure `STATE_DB` points to a persistent location.
- Do not delete the `data/rss_state.db` file between runs.

### Feeds not updating

- Confirm feed URL is valid and publicly reachable.
- Increase `MAX_ITEMS_PER_FEED` if your feed updates rapidly.

## Sharing on GitHub

Recommended before publishing:

- Keep `.env` excluded from git (already ignored).
- Include only `.env.example` and `feeds.example.txt` as templates.
- Add your project description and usage examples to the repository homepage.
- Optionally add CI to run `pytest` on Windows and macOS.

## Security Notes

- Do not commit real SMTP credentials.
- Prefer app passwords or scoped SMTP tokens over your primary password.
- Use a dedicated sender account for notifications.
