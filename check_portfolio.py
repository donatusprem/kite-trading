#!/usr/bin/env python3
"""
Quick Portfolio Check - Shows your complete account snapshot.
Run authenticate_kite.py first if you haven't logged in today.

Usage:
  python3 check_portfolio.py
  python3 check_portfolio.py --watch        # Refresh every 60s
  python3 check_portfolio.py --watch 30     # Refresh every 30s
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "trading-system-v3"))

from scripts.kite_client import KiteClient

BASE_DIR = Path(__file__).parent
CACHE_FILE = BASE_DIR / "trading-system-v3" / "data" / "live_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


def print_header():
    print("\n" + "=" * 70)
    print("  KITE PORTFOLIO - LIVE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


def print_profile(client: KiteClient):
    profile = client.get_profile()
    print(f"\n  Account: {profile.get('user_name')} ({profile.get('user_id')})")
    print(f"  Broker:  {profile.get('broker')}")
    return profile


def print_margins(client: KiteClient):
    margins = client.get_margins()
    net = margins.get("net", 0)
    available = margins.get("available", {})
    cash = available.get("cash", margins.get("cash", 0))
    collateral = margins.get("collateral", 0)

    print(f"\n{'─' * 70}")
    print("  MARGINS")
    print(f"{'─' * 70}")
    print(f"  Net:        {net:>12,.2f}")
    print(f"  Cash:       {cash:>12,.2f}")
    print(f"  Collateral: {collateral:>12,.2f}")
    return margins


def print_positions(client: KiteClient):
    positions = client.get_positions()
    net_positions = positions.get("net", [])
    day_positions = positions.get("day", [])

    active = [p for p in net_positions if p.get("quantity", 0) != 0]
    closed = [p for p in net_positions if p.get("quantity", 0) == 0 and p.get("pnl", 0) != 0]

    total_pnl = sum(p.get("pnl", 0) for p in net_positions)
    unrealized = sum(p.get("unrealised", p.get("pnl", 0)) for p in active)
    realized = sum(p.get("pnl", 0) for p in closed)

    if active:
        print(f"\n{'─' * 70}")
        print("  OPEN POSITIONS")
        print(f"{'─' * 70}")
        print(f"  {'Symbol':<25} {'Qty':>6} {'Avg':>10} {'LTP':>10} {'P&L':>12}")
        print(f"  {'─' * 63}")
        for p in active:
            symbol = p.get("tradingsymbol", "")
            qty = p.get("quantity", 0)
            avg = p.get("average_price", 0)
            ltp = p.get("last_price", 0)
            pnl = p.get("pnl", 0)
            sign = "+" if pnl >= 0 else ""
            print(f"  {symbol:<25} {qty:>6} {avg:>10.2f} {ltp:>10.2f} {sign}{pnl:>11,.2f}")

    if closed:
        print(f"\n{'─' * 70}")
        print("  CLOSED POSITIONS (today)")
        print(f"{'─' * 70}")
        for p in closed:
            symbol = p.get("tradingsymbol", "")
            pnl = p.get("pnl", 0)
            sign = "+" if pnl >= 0 else ""
            print(f"  {symbol:<25} {sign}{pnl:>11,.2f}")

    if not active and not closed:
        print(f"\n  No positions today.")

    print(f"\n{'─' * 70}")
    print(f"  Unrealized P&L: {unrealized:>+12,.2f}")
    print(f"  Realized P&L:   {realized:>+12,.2f}")
    print(f"  Total P&L:      {total_pnl:>+12,.2f}")

    return positions, total_pnl, realized, unrealized


def print_holdings(client: KiteClient):
    holdings = client.get_holdings()

    if not holdings:
        print(f"\n  No holdings.")
        return holdings

    total_value = 0
    total_pnl = 0

    print(f"\n{'─' * 70}")
    print("  HOLDINGS")
    print(f"{'─' * 70}")
    print(f"  {'Symbol':<20} {'Qty':>6} {'Avg':>10} {'LTP':>10} {'Value':>12} {'P&L':>10}")
    print(f"  {'─' * 68}")

    for h in holdings:
        symbol = h.get("tradingsymbol", "")
        qty = h.get("quantity", 0)
        avg = h.get("average_price", 0)
        ltp = h.get("last_price", 0)
        pnl = h.get("pnl", 0)
        value = ltp * qty
        total_value += value
        total_pnl += pnl
        sign = "+" if pnl >= 0 else ""
        print(f"  {symbol:<20} {qty:>6} {avg:>10.2f} {ltp:>10.2f} {value:>12,.2f} {sign}{pnl:>9,.2f}")

    print(f"  {'─' * 68}")
    print(f"  {'Total':<20} {'':>6} {'':>10} {'':>10} {total_value:>12,.2f} {'+' if total_pnl >= 0 else ''}{total_pnl:>9,.2f}")

    return holdings


def print_nifty(client: KiteClient):
    ltp_data = client.get_ltp(["NSE:NIFTY 50"])
    nifty_ltp = ltp_data.get("NSE:NIFTY 50", {}).get("last_price", 0)
    print(f"\n  NIFTY 50: {nifty_ltp:>12,.2f}")
    return nifty_ltp


def update_cache(profile, margins, positions, holdings, nifty_ltp, total_pnl, realized, unrealized):
    """Save data to cache file for dashboard."""
    net_positions = positions.get("net", [])
    cache = {
        "timestamp": datetime.now().isoformat(),
        "is_live": True,
        "source": "kiteconnect_sdk",
        "account": {
            "user_name": profile.get("user_name", ""),
            "user_id": profile.get("user_id", ""),
            "broker": profile.get("broker", ""),
            "status": "connected"
        },
        "margins": {
            "net": margins.get("net", 0),
            "available": margins.get("available", {}).get("cash", 0),
            "used": margins.get("utilised", {}).get("debits", 0) if isinstance(margins.get("utilised"), dict) else 0
        },
        "positions": [
            {
                "symbol": p.get("tradingsymbol", ""),
                "exchange": p.get("exchange", ""),
                "quantity": p.get("quantity", 0),
                "average_price": round(p.get("average_price", 0), 2),
                "last_price": round(p.get("last_price", 0), 2),
                "pnl": round(p.get("pnl", 0), 2),
                "product": p.get("product", ""),
                "type": "short" if p.get("quantity", 0) < 0 else "long" if p.get("quantity", 0) > 0 else "closed"
            }
            for p in net_positions if p.get("quantity", 0) != 0
        ],
        "holdings": [
            {
                "symbol": h.get("tradingsymbol", ""),
                "quantity": h.get("quantity", 0),
                "average_price": round(h.get("average_price", 0), 2),
                "current_price": round(h.get("last_price", 0), 2),
                "pnl": round(h.get("pnl", 0), 2)
            }
            for h in (holdings or [])
        ],
        "session_pnl": round(total_pnl, 2),
        "total_realized": round(realized, 2),
        "total_unrealized": round(unrealized, 2),
        "nifty_ltp": nifty_ltp
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def run_once(client: KiteClient):
    print_header()
    profile = print_profile(client)
    margins = print_margins(client)
    positions, total_pnl, realized, unrealized = print_positions(client)
    holdings = print_holdings(client)
    nifty_ltp = print_nifty(client)
    print("\n" + "=" * 70)

    update_cache(profile, margins, positions, holdings, nifty_ltp, total_pnl, realized, unrealized)
    print(f"  Cache updated: {CACHE_FILE}")


def main():
    client = KiteClient()

    if not client.authenticated:
        print("  Not authenticated. Run: python3 authenticate_kite.py")
        sys.exit(1)

    watch = "--watch" in sys.argv
    interval = 60
    if watch:
        idx = sys.argv.index("--watch")
        if idx + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[idx + 1])
            except ValueError:
                pass

    if watch:
        print(f"  Watch mode (every {interval}s). Ctrl+C to stop.")
        try:
            while True:
                run_once(client)
                print(f"\n  Next refresh in {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n  Stopped.")
    else:
        run_once(client)


if __name__ == "__main__":
    main()
