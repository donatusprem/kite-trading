#!/usr/bin/env python3
"""
run_monitor.py — Systematic Nifty Conviction Monitor

Runs the nifty_conviction_engine in a continuous loop, alerting when
|conviction_score| >= 5 (HIGH threshold per Ajay's trading rules).

Usage:
    python execution/run_monitor.py --loop --market-hours-only --no-options

Flags:
    --loop              Run continuously (every --interval minutes)
    --market-hours-only Run a pre-market scan at startup, then loop 9:15–3:30 IST
    --no-options        Start without options chain; auto-upgrade to full mode at 9:15 AM
    --interval N        Scan interval in minutes (default: 5)

See directives/systematic_monitor.md for full SOP.
"""

import argparse
import sys
import time
from datetime import datetime, date, timedelta
from pathlib import Path

import pytz

# Project root on sys.path so imports work from any working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from execution.kite_client import KiteMCPClient
from nifty_conviction_engine.conviction_scorer import ConvictionScorer

# ── Constants ──────────────────────────────────────────────────────────────────

IST = pytz.timezone("Asia/Kolkata")

MARKET_OPEN_H, MARKET_OPEN_M = 9, 15
MARKET_CLOSE_H, MARKET_CLOSE_M = 15, 30

DEFAULT_INTERVAL_MINUTES = 5
CONVICTION_ALERT_THRESHOLD = 5.0  # |score| >= this → ALERT

# Zerodha's stable instrument token for NSE:NIFTY 50 spot
NIFTY_INSTRUMENT_TOKEN = 256265


# ── Time helpers ───────────────────────────────────────────────────────────────

def ist_now() -> datetime:
    return datetime.now(IST)


def is_market_open() -> bool:
    now = ist_now()
    open_dt = now.replace(hour=MARKET_OPEN_H, minute=MARKET_OPEN_M, second=0, microsecond=0)
    close_dt = now.replace(hour=MARKET_CLOSE_H, minute=MARKET_CLOSE_M, second=0, microsecond=0)
    return open_dt <= now <= close_dt


def is_past_market_open() -> bool:
    now = ist_now()
    open_dt = now.replace(hour=MARKET_OPEN_H, minute=MARKET_OPEN_M, second=0, microsecond=0)
    return now >= open_dt


def seconds_until_market_open() -> float:
    now = ist_now()
    open_dt = now.replace(hour=MARKET_OPEN_H, minute=MARKET_OPEN_M, second=0, microsecond=0)
    if now >= open_dt:
        return 0
    return (open_dt - now).total_seconds()


# ── Data fetching ──────────────────────────────────────────────────────────────

def fetch_candles(client: KiteMCPClient, token: int, interval: str, days_back: int) -> list:
    """Fetch historical candles for Nifty spot."""
    to_date = date.today()
    from_date = to_date - timedelta(days=days_back)
    raw = client.get_historical_data(token, str(from_date), str(to_date), interval)
    candles = []
    for c in (raw or []):
        candles.append({
            "date": str(c.get("date", "")),
            "open": float(c.get("open", 0)),
            "high": float(c.get("high", 0)),
            "low": float(c.get("low", 0)),
            "close": float(c.get("close", 0)),
            "volume": float(c.get("volume", 0)),
        })
    return candles


def fetch_options_chain(client: KiteMCPClient, spot_price: float) -> list | None:
    """
    Fetch ATM ± 500 options chain for nearest weekly NIFTY expiry.
    Returns list of option dicts, or None if unavailable.
    """
    atm = round(spot_price / 50) * 50

    # Load NFO instruments (cached daily by kite_client)
    instruments = client.search_instruments("NFO:NIFTY", filter_on="underlying", limit=3000)
    if not instruments:
        return None

    # Filter to CE/PE only
    options = [i for i in instruments if i.get("instrument_type") in ("CE", "PE")]
    if not options:
        return None

    # Find nearest expiry
    today_str = str(date.today())
    expiries = sorted(set(
        i["expiry"] for i in options
        if i.get("expiry") and str(i["expiry"]) > today_str
    ))
    if not expiries:
        return None
    nearest_expiry = expiries[0]

    # Filter for nearest expiry + ATM ± 500 strikes
    valid_strikes = set(range(atm - 500, atm + 550, 50))
    relevant = [
        i for i in options
        if str(i.get("expiry")) == str(nearest_expiry)
        and i.get("strike") in valid_strikes
    ]
    if not relevant:
        return None

    # Fetch quotes in one call
    trading_symbols = [f"NFO:{i['tradingsymbol']}" for i in relevant]
    quotes = client.get_quotes(trading_symbols) or {}

    options_data = []
    for inst in relevant:
        ts = f"NFO:{inst['tradingsymbol']}"
        q = quotes.get(ts, {})
        if not q:
            continue
        depth = q.get("depth", {}) or {}
        buy_depth = depth.get("buy", []) or []
        sell_depth = depth.get("sell", []) or []
        options_data.append({
            "strike": inst.get("strike"),
            "type": inst.get("instrument_type"),  # "CE" or "PE"
            "oi": q.get("oi", 0),
            "volume": q.get("volume", 0),
            "ltp": q.get("last_price", 0),
            "bid": buy_depth[0].get("price", 0) if buy_depth else 0,
            "ask": sell_depth[0].get("price", 0) if sell_depth else 0,
            "change_oi": (q.get("oi_day_high", 0) or 0) - (q.get("oi_day_low", 0) or 0),
        })

    return options_data if options_data else None


# ── Analysis ───────────────────────────────────────────────────────────────────

def run_analysis(client: KiteMCPClient, use_options: bool) -> dict | None:
    """Fetch all data, run ConvictionScorer, return result dict."""
    now = ist_now()

    # Spot price
    ltp_data = client.get_ltp(["NSE:NIFTY 50"]) or {}
    spot = (ltp_data.get("NSE:NIFTY 50") or {}).get("last_price", 0)
    if not spot:
        print(f"[{now.strftime('%H:%M:%S')}] ERROR: Could not fetch Nifty spot price")
        return None

    # Candles (4 timeframes)
    candles_5min  = fetch_candles(client, NIFTY_INSTRUMENT_TOKEN, "5minute",  2)
    candles_15min = fetch_candles(client, NIFTY_INSTRUMENT_TOKEN, "15minute", 5)
    candles_60min = fetch_candles(client, NIFTY_INSTRUMENT_TOKEN, "60minute", 20)
    candles_daily = fetch_candles(client, NIFTY_INSTRUMENT_TOKEN, "day",      60)

    # Options chain
    options_data = None
    if use_options:
        options_data = fetch_options_chain(client, spot)
        if options_data is None:
            print(f"[{now.strftime('%H:%M:%S')}] WARNING: Options chain unavailable — running without it")

    # Score
    scorer = ConvictionScorer(
        candles_5min=candles_5min,
        candles_15min=candles_15min,
        candles_60min=candles_60min,
        candles_daily=candles_daily,
        spot_price=spot,
        options_data=options_data,
    )
    result = scorer.compute_final_conviction()
    result["timestamp"] = now.isoformat()
    result["spot_price"] = spot
    result["options_used"] = use_options and (options_data is not None)
    return result


# ── Output ─────────────────────────────────────────────────────────────────────

def print_full_report(result: dict):
    score       = result.get("conviction_score", 0)
    level       = result.get("conviction_level", "NEUTRAL")
    direction   = result.get("direction", "NEUTRAL")
    rec         = result.get("recommendation", {})
    action      = rec.get("action", "NO_TRADE")
    spot        = result.get("spot_price", 0)
    ts          = result.get("timestamp", "")[:19].replace("T", " ")
    layers      = result.get("layers", {})
    tf_scores   = result.get("timeframe_scores", {})
    key_levels  = result.get("key_levels", {})
    risks       = result.get("risk_factors", [])
    options_used = result.get("options_used", False)

    mode_tag = "FULL" if options_used else "NO-OPTIONS"
    is_alert = abs(score) >= CONVICTION_ALERT_THRESHOLD
    header = "ALERT" if is_alert else "UPDATE"

    SEP = "=" * 55
    print(f"\n{SEP}")
    print(f"{'NIFTY CONVICTION ' + header + ' [' + mode_tag + ']':^55}")
    print(f"{SEP}")
    print(f"  Time:        {ts} IST")
    print(f"  Spot:        {spot:,.2f}")
    print(f"  Conviction:  {score:+.2f} / 10  [{level}]")
    print(f"  Direction:   {direction}")
    print(f"  Action:      {action}")

    if action != "NO_TRADE":
        opt_type = "CE" if action == "BUY_CE" else "PE"
        print(f"  Strike:      NIFTY {rec.get('atm_strike')} {opt_type}")
        print(f"  SL:          Nifty {rec.get('stop_loss_level')}")
        print(f"  Target:      Nifty {rec.get('target_level')}")
        print(f"  R/R:         1:{rec.get('risk_reward_ratio')}")
        print(f"  Confidence:  {rec.get('confidence')}%")

    print(f"\n  Key Levels:")
    print(f"    Support:    {key_levels.get('support', 'N/A')}")
    print(f"    Resistance: {key_levels.get('resistance', 'N/A')}")
    print(f"    VWAP:       {key_levels.get('vwap', 'N/A')}")
    if key_levels.get("max_pain"):
        print(f"    Max Pain:   {key_levels.get('max_pain')}")

    print(f"\n  Layer Scores:")
    if layers.get("technical"):
        print(f"    Technical:    {layers['technical'].get('score', 0):+.2f}")
    if layers.get("candlestick"):
        print(f"    Candlestick:  {layers['candlestick'].get('score', 0):+.2f}")
    if layers.get("options"):
        pcr = layers["options"].get("pcr", "N/A")
        print(f"    Options:      {layers['options'].get('score', 0):+.2f}  (PCR={pcr})")
    if layers.get("price_action"):
        print(f"    Price Action: {layers['price_action'].get('score', 0):+.2f}")

    print(f"\n  Timeframes:")
    for tf in ("5min", "15min", "60min", "daily"):
        tfd = tf_scores.get(tf, {})
        print(f"    {tf:6s}:  {tfd.get('direction', 'N/A'):18s}  ({tfd.get('score', 0):+.2f})")

    if risks:
        print(f"\n  Risk Factors:")
        for r in risks:
            print(f"    - {r}")

    print(f"{SEP}")

    if is_alert:
        print(f"\n*** CONVICTION THRESHOLD HIT: {score:+.2f} / 10 ***")
        print(f"    {result.get('trade_setup', '')}\n")


def print_brief(result: dict):
    now_str    = result.get("timestamp", "")[:19].replace("T", " ")
    score      = result.get("conviction_score", 0)
    level      = result.get("conviction_level", "NEUTRAL")
    direction  = result.get("direction", "NEUTRAL")
    action     = result.get("recommendation", {}).get("action", "NO_TRADE")
    spot       = result.get("spot_price", 0)
    mode       = "FULL" if result.get("options_used") else "NO-OPT"
    print(f"[{now_str}] [{mode}] Spot={spot:,.0f}  Score={score:+.2f} [{level}]  {direction}  {action}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Nifty Conviction Monitor")
    parser.add_argument("--loop",               action="store_true", help="Run continuously")
    parser.add_argument("--market-hours-only",  action="store_true", help="Pre-market scan + loop 9:15–3:30 IST")
    parser.add_argument("--no-options",         action="store_true", help="Start without options; auto-upgrade at 9:15 AM")
    parser.add_argument("--interval",           type=int, default=DEFAULT_INTERVAL_MINUTES, help="Scan interval in minutes")
    args = parser.parse_args()

    print(f"\nNifty Conviction Monitor")
    print(f"  Loop:          {'ON' if args.loop else 'OFF'}")
    print(f"  Market hours:  {'ON' if args.market_hours_only else 'OFF'}")
    print(f"  No-options:    {'YES (auto-upgrade at 9:15 AM)' if args.no_options else 'NO (full mode always)'}")
    print(f"  Interval:      {args.interval} min")
    print(f"  Alert at:      |score| >= {CONVICTION_ALERT_THRESHOLD}\n")

    # Init Kite
    client = KiteMCPClient()
    if not client.kite:
        print("ERROR: Kite not authenticated. Run: python execution/authenticate_kite.py")
        sys.exit(1)
    print("Kite connected.\n")

    scan_count = 0

    while True:
        now = ist_now()
        market_open_now = is_market_open()
        past_open       = is_past_market_open()

        # Determine options mode
        # --no-options: no options before market opens, full mode once past 9:15 AM
        if args.no_options:
            use_options = past_open
        else:
            use_options = True

        # ── Market-hours gating ──────────────────────────────────────────────
        if args.market_hours_only:
            if not past_open:
                # Pre-market: run one analysis, then sleep until open
                if scan_count == 0:
                    print(f"[{now.strftime('%H:%M:%S')}] PRE-MARKET scan (no options)...")
                    try:
                        result = run_analysis(client, use_options=False)
                        if result:
                            print_full_report(result)
                    except Exception as e:
                        print(f"[{now.strftime('%H:%M:%S')}] ERROR: {e}")
                    scan_count += 1

                wait_secs = seconds_until_market_open()
                if wait_secs > 0:
                    wait_min = int(wait_secs / 60)
                    print(f"[{now.strftime('%H:%M:%S')}] Waiting {wait_min} min for market to open (9:15 AM IST)...")
                    time.sleep(min(wait_secs, 60))  # check every 60s
                    continue

            if not market_open_now:
                # Market closed for the day
                print(f"[{now.strftime('%H:%M:%S')}] Market closed (past 3:30 PM). Monitor stopping.")
                break

        # ── Run scan ─────────────────────────────────────────────────────────
        scan_count += 1
        mode_label = "FULL" if use_options else "NO-OPTIONS"
        print(f"[{now.strftime('%H:%M:%S')}] Scan #{scan_count} [{mode_label}]...")

        try:
            result = run_analysis(client, use_options)
            if result:
                score = result.get("conviction_score", 0)
                is_alert = abs(score) >= CONVICTION_ALERT_THRESHOLD

                # Always print full report on alert or every 3rd scan; brief otherwise
                if is_alert or scan_count % 3 == 1:
                    print_full_report(result)
                else:
                    print_brief(result)

        except Exception as e:
            print(f"[{now.strftime('%H:%M:%S')}] ERROR during analysis: {e}")

        if not args.loop:
            break

        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
