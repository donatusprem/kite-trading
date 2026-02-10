#!/usr/bin/env python3
"""
Kite Data Refresher - Run after daily Kite login
Fetches live data from Kite MCP and updates the cache file
that the dashboard API reads from.

Usage:
  python3 refresh_data.py              # One-time refresh
  python3 refresh_data.py --loop       # Keep refreshing every 60s
  python3 refresh_data.py --loop 30    # Refresh every 30s
"""

import subprocess
import json
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CACHE_FILE = BASE_DIR / "trading-system-v3" / "data" / "live_cache.json"

# Ensure data dir exists
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


def call_claude_mcp(prompt: str, tools: str) -> str:
    """Call claude CLI with specific MCP tools."""
    try:
        result = subprocess.run(
            ['claude', '-p', '--allowedTools', tools, prompt],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=str(BASE_DIR)
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception as e:
        print(f"  Error calling claude: {e}")
        return ""


def fetch_positions() -> list:
    """Fetch positions from Kite."""
    print("  Fetching positions...")
    raw = call_claude_mcp(
        "Get my current positions. Return ONLY a JSON array of positions.",
        "mcp__kite__get_positions"
    )
    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass
    return []


def fetch_margins() -> dict:
    """Fetch margins from Kite."""
    print("  Fetching margins...")
    raw = call_claude_mcp(
        "Get my account margins. Return ONLY JSON with keys: net, cash, collateral, option_premium_used (all numbers).",
        "mcp__kite__get_margins"
    )
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass
    return {}


def fetch_profile() -> dict:
    """Fetch profile from Kite."""
    print("  Fetching profile...")
    raw = call_claude_mcp(
        "Get my profile. Return ONLY JSON with keys: user_name, user_shortname, user_id, broker.",
        "mcp__kite__get_profile"
    )
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass
    return {}


def fetch_ltp() -> float:
    """Fetch Nifty 50 LTP."""
    print("  Fetching Nifty LTP...")
    raw = call_claude_mcp(
        "Get LTP for NSE:NIFTY 50. Return ONLY the number, nothing else.",
        "mcp__kite__get_ltp"
    )
    try:
        # Find a number in the output
        for word in raw.replace(',', '').split():
            try:
                val = float(word)
                if val > 10000:  # Nifty is > 10000
                    return val
            except ValueError:
                continue
    except Exception:
        pass
    return 0


def process_positions(raw_positions: list) -> tuple:
    """Process raw Kite positions into dashboard format."""
    positions = []
    session_pnl = 0
    total_realized = 0
    total_unrealized = 0

    for pos in raw_positions:
        symbol = pos.get("tradingsymbol", pos.get("symbol", ""))
        quantity = pos.get("quantity", 0)
        avg_price = pos.get("average_price", 0)
        last_price = pos.get("last_price", 0)
        buy_price = pos.get("buy_price", 0)
        sell_price = pos.get("sell_price", 0)
        pnl = pos.get("pnl", 0)
        product = pos.get("product", "")

        if avg_price == 0 and buy_price > 0:
            avg_price = buy_price

        pnl_pct = (pnl / (abs(avg_price * (pos.get("buy_quantity", 0) or abs(quantity) or 1))) * 100) if avg_price else 0

        entry = {
            "symbol": symbol,
            "exchange": pos.get("exchange", ""),
            "quantity": quantity,
            "average_price": round(avg_price, 2),
            "last_price": round(last_price, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "product": product,
        }

        if quantity == 0:
            entry["type"] = "closed"
            entry["sell_price"] = round(sell_price, 2)
            total_realized += pnl
        else:
            entry["type"] = "short" if quantity < 0 else "long"
            total_unrealized += pnl

        session_pnl += pnl
        positions.append(entry)

    return positions, round(session_pnl, 2), round(total_realized, 2), round(total_unrealized, 2)


def refresh():
    """Main refresh function."""
    print(f"\n{'='*50}")
    print(f"  Refreshing Kite data - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")

    profile = fetch_profile()
    margins_raw = fetch_margins()
    raw_positions = fetch_positions()
    nifty_ltp = fetch_ltp()

    positions, session_pnl, total_realized, total_unrealized = process_positions(raw_positions)

    # Build margins from raw data
    margins = {
        "net": margins_raw.get("net", margins_raw.get("equity", {}).get("net", 0) if isinstance(margins_raw.get("equity"), dict) else 0),
        "cash": margins_raw.get("cash", 0),
        "collateral": margins_raw.get("collateral", 0),
        "option_premium_used": margins_raw.get("option_premium_used", 0)
    }

    cache = {
        "timestamp": datetime.now().isoformat(),
        "nifty_ltp": nifty_ltp,
        "account": {
            "user_name": profile.get("user_name", "Trader"),
            "user_shortname": profile.get("user_shortname", ""),
            "user_id": profile.get("user_id", ""),
            "broker": profile.get("broker", "")
        },
        "margins": margins,
        "positions": positions,
        "holdings": [],
        "session_pnl": session_pnl,
        "total_realized": total_realized,
        "total_unrealized": total_unrealized,
        "is_live": True
    }

    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"\n  Cache updated: {CACHE_FILE}")
    print(f"  Positions: {len(positions)}")
    print(f"  Session PnL: {session_pnl:+,.2f}")
    print(f"  Nifty: {nifty_ltp:,.2f}")
    print(f"  Margin: {margins.get('net', 0):,.2f}")
    return True


def main():
    loop = "--loop" in sys.argv
    interval = 60

    # Parse custom interval
    if loop:
        idx = sys.argv.index("--loop")
        if idx + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[idx + 1])
            except ValueError:
                pass

    if loop:
        print(f"Running in loop mode (every {interval}s). Ctrl+C to stop.")
        try:
            while True:
                refresh()
                print(f"\n  Next refresh in {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        refresh()
        print("\nDone. Run with --loop to keep refreshing.")


if __name__ == "__main__":
    main()
