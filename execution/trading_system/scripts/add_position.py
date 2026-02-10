#!/usr/bin/env python3
"""
Quick script to add POWERGRID test position to exit manager
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from exit_manager import ExitManager

# Initialize exit manager
config_path = os.path.join(os.path.dirname(__file__), 'config', 'trading_rules.json')
manager = ExitManager(config_path)

# Position details (update entry_price with actual fill price)
position = {
    'symbol': 'POWERGRID',
    'type': 'LONG',
    'entry_price': 288.80,  # UPDATE THIS with actual fill price
    'quantity': 69,
    'position_size': 19927,
    'score': 95,
    'support_level': 287.70,
    'resistance_level': 291.00,
    'setup_details': {
        'setup_type': 'PULLBACK LONG',
        'entry_reason': 'Near support, 95/100 score, excellent R:R',
        'pattern': 'Support bounce',
        'trend': 'Intraday pullback'
    }
}

# Add position
result = manager.add_position(position)

print("\n" + "="*70)
print("  ✅ POSITION ADDED TO EXIT MANAGER")
print("="*70)
print(f"\nSymbol:      {result['symbol']}")
print(f"Entry:       ₹{result['entry_price']:.2f}")
print(f"Quantity:    {result['quantity']} shares")
print(f"Stop Loss:   ₹{result['stop_loss']:.2f}")
print(f"Target 1:    ₹{result['target1']:.2f}")
print(f"Target 2:    ₹{result['target2']:.2f}")
print(f"\nRisk:        ₹{abs(result['entry_price'] - result['stop_loss']) * result['quantity']:.2f}")
print(f"Reward (T2): ₹{abs(result['target2'] - result['entry_price']) * result['quantity']:.2f}")
print("\n" + "="*70)
print("\n✅ System now monitoring exits automatically!")
print("   • Stop loss at support")
print("   • Partial exit at T1")
print("   • Trailing stop enabled")
print("   • All logged to journals/")
print("\n" + "="*70 + "\n")
