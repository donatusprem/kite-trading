#!/usr/bin/env python3
"""
Kite Data Refresher - Fetches live data and updates dashboard cache.
Uses kiteconnect SDK directly (no MCP dependency).

Run authenticate_kite.py first if you haven't logged in today.

Usage:
  python3 refresh_data.py              # One-time refresh
  python3 refresh_data.py --loop       # Keep refreshing every 60s
  python3 refresh_data.py --loop 30    # Refresh every 30s
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "trading-system-v3"))

from scripts.kite_client import KiteClient

BASE_DIR = Path(__file__).parent
CACHE_FILE = BASE_DIR / "trading-system-v3" / "data" / "live_cache.json"
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


def fetch_all(client: KiteClient) -> dict:
    """Fetch all data from Kite in one go."""
    print(f"\n{'='*50}")
    print(f"  Refreshing Kite data - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")

    print("  Fetching profile...")
    profile = client.get_profile()

    print("  Fetching margins...")
    margins = client.get_margins()

    print("  Fetching positions...")
    positions = client.get_positions()

    print("  Fetching holdings...")
    holdings = client.get_holdings()

    print("  Fetching Nifty LTP...")
    ltp_data = client.get_ltp(["NSE:NIFTY 50"])
    nifty_ltp = ltp_data.get("NSE:NIFTY 50", {}).get("last_price", 0)

    return {
        "profile": profile,
        "margins": margins,
        "positions": positions,
        "holdings": holdings,
        "nifty_ltp": nifty_ltp,
    }


def process_positions(raw_positions: dict) -> tuple:
    """Process Kite positions into dashboard format."""
    net_positions = raw_positions.get("net", [])
    processed = []
    session_pnl = 0
    total_realized = 0
    total_unrealized = 0

    for pos in net_positions:
        symbol = pos.get("tradingsymbol", "")
        quantity = pos.get("quantity", 0)
        avg_price = pos.get("average_price", 0)
        last_price = pos.get("last_price", 0)
        pnl = pos.get("pnl", 0)
        product = pos.get("product", "")

        entry = {
            "symbol": symbol,
            "exchange": pos.get("exchange", ""),
            "quantity": quantity,
            "average_price": round(avg_price, 2),
            "last_price": round(last_price, 2),
            "pnl": round(pnl, 2),
            "product": product,
        }

        if quantity == 0:
            entry["type"] = "closed"
            total_realized += pnl
        else:
            entry["type"] = "short" if quantity < 0 else "long"
            total_unrealized += pnl

        session_pnl += pnl
        processed.append(entry)

    return processed, round(session_pnl, 2), round(total_realized, 2), round(total_unrealized, 2)


def refresh(client: KiteClient) -> bool:
    """Main refresh function."""
    data = fetch_all(client)

    profile = data["profile"]
    margins = data["margins"]
    positions, session_pnl, total_realized, total_unrealized = process_positions(data["positions"])
    holdings = data["holdings"]
    nifty_ltp = data["nifty_ltp"]

    cache = {
        "timestamp": datetime.now().isoformat(),
        "is_live": True,
        "source": "kiteconnect_sdk",
        "account": {
            "user_name": profile.get("user_name", ""),
            "user_shortname": profile.get("user_shortname", ""),
            "user_id": profile.get("user_id", ""),
            "broker": profile.get("broker", ""),
            "status": "connected"
        },
        "margins": {
            "net": margins.get("net", 0),
            "cash": margins.get("available", {}).get("cash", 0),
            "collateral": margins.get("collateral", 0),
            "option_premium_used": margins.get("utilised", {}).get("option_premium", 0) if isinstance(margins.get("utilised"), dict) else 0
        },
        "positions": positions,
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
        "session_pnl": session_pnl,
        "total_realized": total_realized,
        "total_unrealized": total_unrealized,
        "nifty_ltp": nifty_ltp
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\n  Cache updated: {CACHE_FILE}")
    print(f"  Account: {profile.get('user_name', '')} ({profile.get('user_id', '')})")
    print(f"  Positions: {len([p for p in positions if p['type'] != 'closed'])}")
    print(f"  Session PnL: {session_pnl:+,.2f}")
    print(f"  Nifty: {nifty_ltp:,.2f}")
    print(f"  Margin: {margins.get('net', 0):,.2f}")
    return True


def main():
    client = KiteClient()

    if not client.authenticated:
        print("  Not authenticated. Run: python3 authenticate_kite.py")
        sys.exit(1)

    loop = "--loop" in sys.argv
    interval = 60

    if loop:
        idx = sys.argv.index("--loop")
        if idx + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[idx + 1])
            except ValueError:
                pass

    if loop:
        print(f"  Loop mode (every {interval}s). Ctrl+C to stop.")
        try:
            while True:
                refresh(client)
                print(f"\n  Next refresh in {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        refresh(client)
        print("\nDone. Run with --loop to keep refreshing.")


if __name__ == "__main__":
    main()
