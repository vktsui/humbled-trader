#!/usr/bin/env bash
# Shared Telegram helper (reads .env from project root).
set -euo pipefail

send_telegram() {
  local body="$1"
  local root="${HUMBLED_TRADER_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"

  if [[ -f "$root/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$root/.env"
    set +a
  fi

  if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_CHAT_ID:-}" ]]; then
    echo "Telegram skipped: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env" >&2
    return 0
  fi

  if ! curl -sf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${body}" \
    -d "parse_mode=Markdown" >/dev/null; then
    echo "Telegram send failed (scan continues)" >&2
  fi
}
