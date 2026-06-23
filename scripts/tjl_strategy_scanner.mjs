#!/usr/bin/env node
/**
 * Trend Join Long strategy scanner (Scanner B) — Humbled Trader workflow.
 * Uses TradingView MCP CLI (tv) to read live chart data.
 */

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const STATE_DIR = join(ROOT, ".state");

const TICKERS = (process.env.TJL_TICKERS || "AMD,NVDA,MU").split(",").map((s) => s.trim());
const NODE = process.env.TV_CLI_NODE || "node";
const MCP_PATH =
  process.env.TRADINGVIEW_MCP_PATH ||
  join(process.env.HOME || "", "tradingview-mcp/versions/v1");
const TV = join(MCP_PATH, "src/cli/index.js");

function loadEnv() {
  const envPath = join(ROOT, ".env");
  if (!existsSync(envPath)) return;
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#") || !t.includes("=")) continue;
    const i = t.indexOf("=");
    const k = t.slice(0, i).trim();
    const v = t.slice(i + 1).trim();
    if (!process.env[k]) process.env[k] = v;
  }
}

async function tv(...args) {
  const { stdout } = await execFileAsync(NODE, [TV, ...args], {
    cwd: ROOT,
    maxBuffer: 10 * 1024 * 1024,
  });
  return JSON.parse(stdout);
}

function nyTimeParts() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const get = (t) => parts.find((p) => p.type === t)?.value;
  const hour = Number(get("hour"));
  const minute = Number(get("minute"));
  const y = get("year");
  const m = get("month");
  const d = get("day");
  return { hour, minute, minutes: hour * 60 + minute, stamp: `${y}${m}${d}`, label: `${hour}:${String(minute).padStart(2, "0")}` };
}

function inTradingWindow() {
  const { minutes } = nyTimeParts();
  return minutes >= 10 * 60 && minutes <= 15 * 60 + 30; // 10:00–15:30 ET
}

function mean(arr) {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function todayEtStartSec() {
  const now = new Date();
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const get = (t) => fmt.find((p) => p.type === t)?.value;
  const y = Number(get("year"));
  const m = Number(get("month"));
  const d = Number(get("day"));
  // 04:00 ET premarket start
  const et4am = new Date(`${y}-${m}-${d}T04:00:00-04:00`);
  return Math.floor(et4am.getTime() / 1000);
}

async function sendTelegram(body) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chatId) {
    console.error("Telegram skipped: missing .env credentials");
    return;
  }
  const params = new URLSearchParams({
    chat_id: chatId,
    text: body,
    parse_mode: "Markdown",
  });
  try {
    await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params,
    });
  } catch (e) {
    console.error("Telegram send failed:", e.message);
  }
}

function loadState() {
  mkdirSync(STATE_DIR, { recursive: true });
  const path = join(STATE_DIR, "tjl_notify.json");
  if (!existsSync(path)) return { day: null, hits: [], firstRunSent: false };
  return JSON.parse(readFileSync(path, "utf8"));
}

function saveState(state) {
  writeFileSync(join(STATE_DIR, "tjl_notify.json"), JSON.stringify(state, null, 2));
}

async function analyzeTicker(symbol) {
  await tv("symbol", symbol);
  await tv("timeframe", "D");
  const daily = await tv("ohlcv", "-n", "210");
  const bars = daily.bars || daily.data || [];
  if (bars.length < 200) throw new Error(`Not enough daily bars for ${symbol}`);
  const last = bars[bars.length - 1];
  const closes = bars.slice(-200).map((b) => b.close ?? b.c);
  const prev_daily_high = last.high ?? last.h;
  const prev_daily_close = last.close ?? last.c;
  const sma200 = mean(closes);

  const quote = await tv("quote", symbol);
  const curr_px = quote.last ?? quote.price ?? quote.close;

  await tv("timeframe", "1");
  const intraday = await tv("ohlcv", "-n", "400");
  const ibars = intraday.bars || intraday.data || [];
  const pmStart = todayEtStartSec();
  const pmBars = ibars.filter((b) => (b.time ?? b.t) >= pmStart);
  const pmh = pmBars.length ? Math.max(...pmBars.map((b) => b.high ?? b.h)) : 0;
  const today_hod = ibars.length ? Math.max(...ibars.map((b) => b.high ?? b.h)) : 0;

  const daily_ok = curr_px > prev_daily_high && prev_daily_close > sma200;
  const intraday_ok = curr_px > pmh && curr_px > today_hod;
  let result = "fail_daily";
  if (daily_ok && intraday_ok) result = "PASS";
  else if (daily_ok) result = "fail_intraday";

  return {
    symbol,
    result,
    curr_price: curr_px,
    prev_daily_high,
    sma200,
    pmh,
    today_hod,
  };
}

async function main() {
  loadEnv();
  const { stamp, label } = nyTimeParts();
  const outPath = join(ROOT, `tjl_watchlist_${stamp}_${label.replace(":", "")}ET.json`);

  if (!inTradingWindow()) {
    const err = {
      scanned_at: new Date().toISOString(),
      error: "Outside trading window (10:00–15:30 ET)",
    };
    writeFileSync(outPath, JSON.stringify(err, null, 2));
    console.error(err.error);
    return 1;
  }

  const health = await tv("status");
  if (!health.cdp_connected || !health.api_available) {
    console.error(
      "TradingView not connected. Launch with:\n" +
        "  open -a TradingView --args --remote-debugging-port=9222"
    );
    return 2;
  }

  const all_results = [];
  const hits = [];
  for (const symbol of TICKERS) {
    console.log(`Checking ${symbol}...`);
    const row = await analyzeTicker(symbol);
    all_results.push({ symbol: row.symbol, result: row.result });
    console.log(`${row.symbol}: ${row.result}`);
    if (row.result === "PASS") hits.push(row);
  }

  const payload = {
    scanned_at: new Date().toISOString(),
    candidates_checked: TICKERS.length,
    hits,
    all_results,
  };
  writeFileSync(outPath, JSON.stringify(payload, null, 2));

  const state = loadState();
  const hitSymbols = hits.map((h) => h.symbol).sort().join(",");
  const prevHitSymbols = (state.hits || []).sort().join(",");
  const newHit = hitSymbols !== prevHitSymbols;
  const firstRunToday = state.day !== stamp;

  let shouldNotify = firstRunToday || newHit;
  if (hits.length === 0 && !firstRunToday && !newHit) shouldNotify = false;

  if (shouldNotify) {
    let body;
    if (hits.length === 0) {
      body = `🎯 *TJL Watchlist* — ${label} ET\nNo TJL hits this run.`;
    } else {
      body = `🎯 *TJL Watchlist* — ${label} ET\n` + hits
        .map(
          (h) =>
            `• ${h.symbol} @ $${h.curr_price.toFixed(2)} (PMH $${h.pmh.toFixed(2)}, prev_high $${h.prev_daily_high.toFixed(2)}, SMA200 $${h.sma200.toFixed(2)})`
        )
        .join("\n");
    }
    await sendTelegram(body);
    saveState({ day: stamp, hits: hits.map((h) => h.symbol), firstRunSent: true });
  } else {
    console.log("Telegram gated: no new hits and not first run of day.");
    saveState({ day: stamp, hits: hits.map((h) => h.symbol), firstRunSent: state.firstRunSent });
  }

  return 0;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
