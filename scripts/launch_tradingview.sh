#!/usr/bin/env bash
# Launch TradingView Desktop with CDP or run tv CLI health check.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

MCP_PATH="${TRADINGVIEW_MCP_PATH:-$HOME/tradingview-mcp/versions/v1}"
NODE="${TV_CLI_NODE:-$(command -v node)}"
PORT="${CDP_PORT:-9222}"
TV_CLI="$NODE $MCP_PATH/src/cli/index.js"

cmd="${1:-status}"

case "$cmd" in
  launch)
    echo "Launching TradingView with --remote-debugging-port=$PORT ..."
    pkill -x TradingView 2>/dev/null || true
    sleep 1
    open -a TradingView --args "--remote-debugging-port=$PORT"
  sleep 3
    $TV_CLI launch --port "$PORT" 2>/dev/null || true
    ;;
  status)
    $TV_CLI status
    ;;
  *)
    echo "Usage: $0 {launch|status}" >&2
    exit 1
    ;;
esac
