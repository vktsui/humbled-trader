#!/usr/bin/env bash
# Install launchd jobs for Scanner A (8:30am ET) and Scanner B (every 30m 10am–2pm ET).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$PLIST_DIR" "$ROOT/.state"

sed "s|__ROOT__|$ROOT|g" "$ROOT/launchd/com.humbledtrader.premarket.plist.template" \
  > "$PLIST_DIR/com.humbledtrader.premarket.plist"
sed "s|__ROOT__|$ROOT|g" "$ROOT/launchd/com.humbledtrader.tjl.plist.template" \
  > "$PLIST_DIR/com.humbledtrader.tjl.plist"
sed "s|__ROOT__|$ROOT|g" "$ROOT/launchd/com.humbledtrader.catchup.plist.template" \
  > "$PLIST_DIR/com.humbledtrader.catchup.plist"

launchctl unload "$PLIST_DIR/com.humbledtrader.premarket.plist" 2>/dev/null || true
launchctl unload "$PLIST_DIR/com.humbledtrader.tjl.plist" 2>/dev/null || true
launchctl unload "$PLIST_DIR/com.humbledtrader.catchup.plist" 2>/dev/null || true

launchctl load "$PLIST_DIR/com.humbledtrader.premarket.plist"
launchctl load "$PLIST_DIR/com.humbledtrader.tjl.plist"
launchctl load "$PLIST_DIR/com.humbledtrader.catchup.plist"

echo "Installed launchd jobs:"
launchctl list | grep -i humbledtrader || true
echo ""
echo "Verify with: launchctl list | grep -i premarket"
