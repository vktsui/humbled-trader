#!/usr/bin/env python3
"""
Premarket Gappers Scanner (Scanner A) — Humbled Trader workflow.

Fetches top gainers from NASDAQ market-movers (reflects pre/extended hours),
enriches volume from the NASDAQ screener, pulls a best-effort Benzinga catalyst,
saves JSON, and emails the result.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from html import unescape
from pathlib import Path

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from send_email import send_email  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MIN_PREMARKET_VOLUME = 50_000
TOP_N = 10
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
NASDAQ_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def fetch(url: str, timeout: int = 30, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _to_float(s: str) -> float | None:
    try:
        return float(re.sub(r"[^0-9.\-]", "", s))
    except (ValueError, TypeError):
        return None


def fetch_nasdaq_gainers() -> list[dict]:
    """Top % gainers from NASDAQ market-movers (reflects pre/extended hours)."""
    body = fetch(
        "https://api.nasdaq.com/api/marketmovers", headers=NASDAQ_HEADERS
    )
    data = json.loads(body).get("data", {})
    section = data.get("STOCKS", {}).get("MostAdvanced", {})
    rows = section.get("table", {}).get("rows", [])
    out: list[dict] = []
    for r in rows:
        symbol = (r.get("symbol") or "").upper()
        price = _to_float(r.get("lastSalePrice", ""))
        gap_pct = _to_float(r.get("change", ""))  # "% Change" column
        if not symbol or price is None or gap_pct is None:
            continue
        out.append(
            {
                "symbol": symbol,
                "price": price,
                "gap_pct": gap_pct,
                "premarket_volume": None,
            }
        )
    return out


def fetch_volume_map() -> dict[str, int]:
    """Map of symbol -> volume from the NASDAQ stock screener (best effort)."""
    try:
        body = fetch(
            "https://api.nasdaq.com/api/screener/stocks"
            "?tableonly=true&limit=0&offset=0&download=true",
            timeout=40,
            headers=NASDAQ_HEADERS,
        )
        rows = json.loads(body).get("data", {}).get("rows", []) or []
    except (urllib.error.URLError, ValueError, TimeoutError) as e:
        print(f"  volume lookup failed: {e}", file=sys.stderr)
        return {}
    vmap: dict[str, int] = {}
    for r in rows:
        sym = (r.get("symbol") or "").upper()
        vol = _to_float(r.get("volume", "")) or 0
        if sym:
            vmap[sym] = int(vol)
    return vmap


def fetch_benzinga_catalyst(symbol: str) -> tuple[str | None, list[str]]:
    url = f"https://www.benzinga.com/quote/{symbol}"
    try:
        html = fetch(url, timeout=20)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  catalyst fetch failed for {symbol}: {e}", file=sys.stderr)
        return None, []

    junk = re.compile(
        r"stock price|quote, news|key statistics|price target|"
        r"news & history|^overview$",
        re.I,
    )
    headlines: list[str] = []
    for m in re.finditer(r'<h[1-3][^>]*>([^<]{12,200})</h[1-3]>', html, re.I):
        t = unescape(m.group(1)).strip()
        if t and not junk.search(t) and t not in headlines:
            headlines.append(t)
        if len(headlines) >= 2:
            break

    catalyst = headlines[0] if headlines else None
    return catalyst, headlines[:2]


def main() -> int:
    load_env()
    today = date.today().isoformat()
    out_path = ROOT / f"premarket_gappers_{today}.json"

    if out_path.exists():
        print(f"Already scanned today: {out_path}")
        return 0

    print("Fetching NASDAQ top gainers...")
    raw = fetch_nasdaq_gainers()
    if not raw:
        print("No gainers returned from NASDAQ market-movers.", file=sys.stderr)
        return 1

    vmap = fetch_volume_map()
    for r in raw:
        if r["symbol"] in vmap:
            r["premarket_volume"] = vmap[r["symbol"]]

    # Keep names with known volume above threshold; keep unknown-volume names too
    # (premarket volume often unavailable pre-open) so the scan is never empty.
    filtered = [
        r
        for r in raw
        if r["premarket_volume"] is None
        or r["premarket_volume"] > MIN_PREMARKET_VOLUME
    ]
    filtered.sort(key=lambda x: x["gap_pct"], reverse=True)
    top = filtered[:TOP_N]

    results = []
    for i, row in enumerate(top, start=1):
        print(f"  catalyst: {row['symbol']}...")
        catalyst, headlines = fetch_benzinga_catalyst(row["symbol"])
        results.append(
            {
                "rank": i,
                "symbol": row["symbol"],
                "price": row["price"],
                "gap_pct": row["gap_pct"],
                "premarket_volume": row["premarket_volume"],
                "catalyst": catalyst,
                "headlines": headlines,
            }
        )

    payload = {
        "scanned_at": datetime.now().astimezone().isoformat(),
        "gappers": results,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n")

    top3 = results[:3]
    parts = [
        f"{g['symbol']} ({g['gap_pct']:+.1f}%) — {g['catalyst'] or 'no catalyst'}"
        for g in top3
    ]
    summary = (
        f"Premarket Gappers: {len(results)} names. Top: " + ", ".join(parts)
    )
    print(summary)

    if results:
        lines = [f"Premarket Gappers — {today}", ""]
        for g in results:
            cat = f" — {g['catalyst']}" if g["catalyst"] else ""
            lines.append(
                f"  {g['symbol']}  ${g['price']:.2f}  +{g['gap_pct']:.1f}%{cat}"
            )
        send_email(f"Premarket Gappers — {today}", "\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
