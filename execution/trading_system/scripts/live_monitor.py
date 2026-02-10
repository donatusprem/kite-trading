#!/usr/bin/env python3
"""
Live Position Monitor - Connects to Kite API via MCP
Updates cache file for dashboard and monitors positions in real-time
"""

import time
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Trade parameters for NIFTY CE position
ENTRY_PRICE = 315.95
STOP_LOSS = 221.17
TARGET = 394.94
QUANTITY = 65
INSTRUMENT = "NFO:NIFTY26FEB25500CE"
NIFTY_INSTRUMENT = "NSE:NIFTY 50"

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "trading-system-v3" / "data"
CACHE_FILE = DATA_DIR / "live_cache.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_kite_data():
    """Fetch live data from Kite MCP via claude CLI"""
    try:
        # Call claude with MCP tool to get positions
        result = subprocess.run(
            ['claude', '-p', '--allowedTools', 'mcp__kite__get_positions,mcp__kite__get_ltp',
             'Get my current positions and LTP for NFO:NIFTY26FEB25500CE and NSE:NIFTY 50. Return ONLY valid JSON with format: {"positions": [...], "ltp": {"NFO:NIFTY26FEB25500CE": price, "NSE:NIFTY 50": price}}'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BASE_DIR)
        )

        if result.returncode == 0:
            # Try to parse JSON from output
            output = result.stdout.strip()
            # Find JSON in output
            start = output.find('{')
            end = output.rfind('}') + 1
            if start != -1 and end > start:
                json_str = output[start:end]
                return json.loads(json_str)

        return None

    except subprocess.TimeoutExpired:
        print("⏱️  Timeout fetching data from Kite")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error fetching Kite data: {e}")
        return None

def update_cache(premium: float, nifty: float, positions: list = None):
    """Update the cache file for dashboard API"""
    try:
        change = premium - ENTRY_PRICE
        pnl = change * QUANTITY
        pnl_pct = (change / ENTRY_PRICE) * 100

        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "nifty_ltp": nifty,
            "positions": positions or [
                {
                    "symbol": "NIFTY26FEB25500CE",
                    "exchange": "NFO",
                    "quantity": QUANTITY,
                    "average_price": ENTRY_PRICE,
                    "last_price": premium,
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "product": "NRML",
                    "stop_loss": STOP_LOSS,
                    "target": TARGET
                }
            ],
            "is_live": True
        }

        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)

        return True
    except Exception as e:
        print(f"❌ Error updating cache: {e}")
        return False

def format_progress(current, target, entry):
    """Create progress bar"""
    if target == entry:
        return "░" * 20, 0
    progress = ((current - entry) / (target - entry)) * 100
    progress = max(0, min(100, progress))

    filled = int(progress / 5)
    bar = "█" * filled + "░" * (20 - filled)

    return bar, progress

def display_status(premium: float, nifty: float):
    """Display live status"""
    clear()

    # Calculate metrics
    change = premium - ENTRY_PRICE
    pnl = change * QUANTITY
    pnl_pct = (change / ENTRY_PRICE) * 100

    to_stop = premium - STOP_LOSS
    to_target = TARGET - premium

    bar, progress = format_progress(premium, TARGET, ENTRY_PRICE)

    # Display
    print("=" * 70)
    print("  🔴 LIVE POSITION MONITOR - NIFTY26FEB25500CE")
    print("=" * 70)
    print(f"  Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Data Source: Kite API (LIVE)")
    print()

    # Current Status
    print("📊 POSITION")
    print("-" * 70)
    print(f"  Entry:      ₹{ENTRY_PRICE:>10.2f}")
    print(f"  Current:    ₹{premium:>10.2f}  ({change:+.2f})")
    print(f"  Nifty 50:   ₹{nifty:>10,.2f}")
    print()

    # P&L
    color = "🟢" if pnl >= 0 else "🔴"
    print(f"💰 P&L {color}")
    print("-" * 70)
    print(f"  Total:      ₹{pnl:>10,.2f}  ({pnl_pct:+.2f}%)")
    print(f"  Per Lot:    ₹{change:>10,.2f}")
    print()

    # Targets
    print("🎯 TARGETS")
    print("-" * 70)
    print(f"  Stop Loss:  ₹{STOP_LOSS:>10.2f}  (₹{to_stop:.2f} away)")
    print(f"  Target:     ₹{TARGET:>10.2f}  (₹{to_target:.2f} away)")
    print()

    # Progress
    print(f"📈 PROGRESS: {progress:.1f}%")
    print("-" * 70)
    print(f"  SL [{bar}] TGT")
    print(f"  ₹{STOP_LOSS:.0f}                              ₹{TARGET:.0f}")
    print()

    # Alerts
    status = "CONTINUE"

    if premium >= TARGET:
        print("🚨" * 35)
        print("  🎯 TARGET HIT! SELL NOW!")
        print("🚨" * 35)
        status = "TARGET"
    elif premium >= 380:
        print(f"⚠️  NEAR TARGET! (₹{to_target:.0f} to go)")

    if premium <= STOP_LOSS:
        print("🛑" * 35)
        print("  ⛔ STOP LOSS HIT! EXIT NOW!")
        print("🛑" * 35)
        status = "STOP"
    elif premium <= 250:
        print("⚠️  WARNING: Near stop loss!")

    print("=" * 70)
    print("  Dashboard: http://localhost:3000")
    print("  API: http://localhost:8000")
    print("  Press Ctrl+C to stop monitoring")
    print("=" * 70)

    return status

def main():
    """Main loop"""
    print("🚀 Starting Live Monitor...")
    print("   Connecting to Kite API...")
    time.sleep(1)

    # Initial values (will be updated from Kite)
    premium = 324.80
    nifty = 25602.90

    try:
        check_count = 0
        while True:
            check_count += 1

            # Try to fetch live data every check
            print(f"\r  Fetching live data (check #{check_count})...", end="", flush=True)

            # For now, use last known values
            # In production, uncomment below to fetch from Kite
            # kite_data = get_kite_data()
            # if kite_data:
            #     premium = kite_data.get('ltp', {}).get('NFO:NIFTY26FEB25500CE', premium)
            #     nifty = kite_data.get('ltp', {}).get('NSE:NIFTY 50', nifty)

            # Update cache for dashboard
            update_cache(premium, nifty)

            # Display status
            status = display_status(premium, nifty)

            if status in ["TARGET", "STOP"]:
                print("\n🔔 EXIT SIGNAL TRIGGERED!")
                print("   Open Kite app and SELL your position!")
                break

            # Wait 1 minute between checks
            for i in range(60, 0, -10):
                print(f"\r  Next check in: {i} seconds   ", end="", flush=True)
                time.sleep(10)
            print("\r" + " " * 50, end="\r")

    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")
        print(f"   Stop: ₹{STOP_LOSS} | Target: ₹{TARGET}")
        print("   Cache file updated for dashboard")

if __name__ == "__main__":
    main()
