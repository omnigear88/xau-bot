#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  echo "Missing .venv."
  echo "Set up the project first:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Missing .env."
  echo "Create .env with MASSIVE_API_KEY and Telegram settings before running the bot."
  exit 1
fi

source ".venv/bin/activate"

exec python bot.py "$@"
