#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/.env" ]]; then
  # Export non-comment KEY=VALUE lines from .env
  set -a
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.env"
  set +a
fi

export PYTHONPATH="$SCRIPT_DIR/src"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ -x "$VENV_PYTHON" ]]; then
  "$VENV_PYTHON" -m rss_reader run-once --verbose
else
  python3 -m rss_reader run-once --verbose
fi
