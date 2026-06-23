#!/usr/bin/env bash
# Catch-up premarket scan if laptop was asleep at 8:30am ET.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Weekday only (Mon–Fri)
dow=$(TZ=America/New_York date +%u)
if [[ "$dow" -gt 5 ]]; then exit 0; fi

# Before 4pm ET, after 4am ET
hour=$(TZ=America/New_York date +%H)
if [[ "$hour" -lt 4 || "$hour" -ge 16 ]]; then exit 0; fi

today=$(TZ=America/New_York date +%Y-%m-%d)
if [[ -f "$ROOT/premarket_gappers_${today}.json" ]]; then exit 0; fi

exec python3 "$ROOT/scripts/premarket_gappers.py"
