#!/usr/bin/env python3
"""
Real-time Position Monitor for NIFTY26FEB25500CE
Checks every 5 minutes and alerts on key levels
"""

import time
import os
from datetime import datetime

# Your trade parameters
ENTRY_PRICE = 315.95
STOP_LOSS = 221.17
TARGET = 394.94
QUANTITY = 65

# Alert thresholds
ALERT_NEAR_TARGET = 380.00  # Alert when 90% to target
ALERT_NEAR_STOP = 240.00    # Alert when 20% from stop

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def get_position():
    """Fetch current position from Kite"""
    # This will be replaced with actual Kite API call
    # For now, returns mock data
    import subprocess
    result = subprocess.run(
        ['python3', '-c', '''
import json
# Mock Kite API call - replace with real call
position = {
    "premium": 359.80,
    "nifty": 25633,
    "timestamp": "2026-02-06 11:18:00"
}
print(json.dumps(position))
        '''],
        capture_output=True,
        text=True
    )
    return eval(result.stdout.strip())

def calculate_pnl(current_price):
    """Calculate P&L"""
    change = current_price - ENTRY_PRICE
    pnl = change * QUANTITY
    pnl_pct = (change / ENTRY_PRICE) * 100
    return pnl, pnl_pct, change

def distance_to_targets(current_price):
    """Calculate distance to stop and target"""
    to_stop = current_price - STOP_LOSS
    to_target = TARGET - current_price

    progress = ((current_price - ENTRY_PRICE) / (TARGET - ENTRY_PRICE)) * 100

    return to_stop, to_target, progress

def get_status_emoji(progress):
    """Get status emoji based on progress"""
    if progress < 0:
        return "⚠️"
    elif progress < 25:
        return "🟡"
    elif progress < 50:
        return "🟢"
    elif progress < 75:
        return "💚"
    else:
        return "🔥"

def format_progress_bar(progress):
    """Create visual progress bar"""
    filled = int(progress / 5)
    empty = 20 - filled
    return "█" * filled + "░" * empty

def check_alerts(current_price, to_stop, to_target):
    """Check if any alerts should trigger"""
    alerts = []

    if current_price >= ALERT_NEAR_TARGET:
        alerts.append("🎯 NEAR TARGET! Only ₹{:.2f} away!".format(to_target))

    if current_price >= TARGET:
        alerts.append("🚨🚨🚨 TARGET HIT! SELL NOW at ₹{:.2f} 🚨🚨🚨".format(current_price))

    if current_price <= ALERT_NEAR_STOP:
        alerts.append("⚠️ WARNING: Getting close to stop loss!")

    if current_price <= STOP_LOSS:
        alerts.append("🛑🛑🛑 STOP LOSS HIT! EXIT NOW at ₹{:.2f} 🛑🛑🛑".format(current_price))

    return alerts

def display_dashboard(data):
    """Display beautiful dashboard"""
    current_price = data['premium']
    nifty = data['nifty']
    timestamp = data['timestamp']

    pnl, pnl_pct, change = calculate_pnl(current_price)
    to_stop, to_target, progress = distance_to_targets(current_price)
    status_emoji = get_status_emoji(progress)
    progress_bar = format_progress_bar(progress)
    alerts = check_alerts(current_price, to_stop, to_target)

    clear_screen()

    print("=" * 70)
    print(f"  LIVE POSITION MONITOR - NIFTY26FEB25500CE {status_emoji}")
    print("=" * 70)
    print(f"Last Update: {timestamp}")
    print()

    print("📊 CURRENT STATUS")
    print("-" * 70)
    print(f"  Entry Price:    ₹{ENTRY_PRICE:>10.2f}")
    print(f"  Current Price:  ₹{current_price:>10.2f}  ({change:+.2f})")
    print(f"  Nifty 50:       ₹{nifty:>10,.2f}")
    print()

    print("💰 PROFIT/LOSS")
    print("-" * 70)
    pnl_color = "+" if pnl >= 0 else ""
    print(f"  Total P&L:      ₹{pnl_color}{pnl:>10,.2f}  ({pnl_pct:+.2f}%)")
    print(f"  Per Lot:        ₹{pnl_color}{pnl/QUANTITY:>10,.2f}")
    print()

    print("🎯 TARGETS")
    print("-" * 70)
    print(f"  Stop Loss:      ₹{STOP_LOSS:>10.2f}  (₹{to_stop:.2f} away)")
    print(f"  Target:         ₹{TARGET:>10.2f}  (₹{to_target:.2f} away)")
    print()

    print(f"📈 PROGRESS TO TARGET: {progress:.1f}%")
    print("-" * 70)
    print(f"  [{progress_bar}] {progress:.1f}%")
    print()

    if alerts:
        print("🔔 ALERTS")
        print("-" * 70)
        for alert in alerts:
            print(f"  {alert}")
        print()

    print("=" * 70)
    print("Monitoring... Press Ctrl+C to stop")
    print("=" * 70)

def main():
    """Main monitoring loop"""
    print("🚀 Starting Position Monitor...")
    print("Will check every 5 minutes")
    print()

    try:
        while True:
            try:
                data = get_position()
                display_dashboard(data)

                # Check if target or stop hit
                if data['premium'] >= TARGET:
                    print("\n🎉 TARGET HIT! Time to exit! 🎉")
                    print("Open Kite and SELL your position NOW!")
                    # You could add sound alert here
                    break

                if data['premium'] <= STOP_LOSS:
                    print("\n🛑 STOP LOSS HIT! Exit immediately! 🛑")
                    print("Open Kite and SELL your position NOW!")
                    break

                # Wait 5 minutes (300 seconds)
                time.sleep(300)

            except Exception as e:
                print(f"\n❌ Error fetching data: {e}")
                print("Retrying in 30 seconds...")
                time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
        print("Stay disciplined! Follow your exit rules!")

if __name__ == "__main__":
    main()
