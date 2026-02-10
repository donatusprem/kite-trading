#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - EXIT MANAGER
Dynamic exit management based on technical structure
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class ExitManager:
    """Manages exits based on technical analysis and risk management"""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.base_path = os.path.dirname(os.path.dirname(config_path))
        self.positions_file = os.path.join(self.base_path, 'data', 'open_positions.json')
        self.load_positions()

    def load_positions(self):
        """Load open positions from file"""
        if os.path.exists(self.positions_file):
            with open(self.positions_file, 'r') as f:
                self.positions = json.load(f)
        else:
            self.positions = []

    def save_positions(self):
        """Save positions to file"""
        with open(self.positions_file, 'w') as f:
            json.dump(self.positions, f, indent=2)

    def add_position(self, position: Dict):
        """Add a new position with calculated exit levels"""

        entry_price = position['entry_price']
        position_type = position['type']  # LONG or SHORT
        stop_loss_pct = self.config['risk_management']['max_loss_per_trade_percent'] / 100

        # Calculate initial stop loss
        if position_type == 'LONG':
            stop_loss = entry_price * (1 - stop_loss_pct)
            # Use support level if available and tighter than % stop
            if 'support_level' in position and position['support_level'] > stop_loss:
                stop_loss = position['support_level']
        else:  # SHORT
            stop_loss = entry_price * (1 + stop_loss_pct)
            # Use resistance level if available
            if 'resistance_level' in position and position['resistance_level'] < stop_loss:
                stop_loss = position['resistance_level']

        # Calculate targets based on risk:reward
        risk = abs(entry_price - stop_loss)
        min_rr = self.config['exit_rules']['risk_reward_minimum']

        if position_type == 'LONG':
            target1 = entry_price + (risk * min_rr)
            target2 = entry_price + (risk * min_rr * 2)
        else:  # SHORT
            target1 = entry_price - (risk * min_rr)
            target2 = entry_price - (risk * min_rr * 2)

        # Add exit parameters
        position.update({
            'stop_loss': stop_loss,
            'target1': target1,
            'target2': target2,
            'trailing_stop': None,
            'breakeven_moved': False,
            'partial_exit_done': False,
            'entry_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'exit_reasons': []
        })

        self.positions.append(position)
        self.save_positions()

        # Log position entry
        self.log_position_event(position, 'ENTRY')

        return position

    def update_position_price(self, symbol: str, current_price: float, current_data: Dict):
        """Update position with current price and check exit conditions"""

        position = None
        for p in self.positions:
            if p['symbol'] == symbol:
                position = p
                break

        if not position:
            return None

        position['current_price'] = current_price
        position['last_update'] = datetime.now().isoformat()

        # Calculate current P&L
        entry_price = position['entry_price']
        quantity = position.get('quantity', 1)

        if position['type'] == 'LONG':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            pnl_amount = (current_price - entry_price) * quantity
        else:  # SHORT
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
            pnl_amount = (entry_price - current_price) * quantity

        position['pnl_percent'] = pnl_pct
        position['pnl_amount'] = pnl_amount

        # Check exit conditions
        exit_signals = self.check_exit_conditions(position, current_data)

        if exit_signals:
            position['exit_reasons'].extend(exit_signals)

        # Update trailing stop if enabled
        if self.config['exit_rules']['use_trailing_stops']:
            self.update_trailing_stop(position, current_price)

        # Check for partial exit at target1
        if not position['partial_exit_done'] and self.should_partial_exit(position, current_price):
            position['partial_exit_done'] = True
            position['exit_reasons'].append('PARTIAL_EXIT_TARGET1')
            self.log_position_event(position, 'PARTIAL_EXIT')

        # Move stop to breakeven after target1
        if position['partial_exit_done'] and not position['breakeven_moved']:
            if self.config['exit_rules']['breakeven_after_target1']:
                position['stop_loss'] = entry_price
                position['breakeven_moved'] = True
                position['exit_reasons'].append('STOP_TO_BREAKEVEN')
                self.log_position_event(position, 'BREAKEVEN_MOVE')

        self.save_positions()

        return position

    def check_exit_conditions(self, position: Dict, current_data: Dict) -> List[str]:
        """Check all exit conditions and return triggered signals"""

        exit_signals = []
        current_price = position['current_price']
        position_type = position['type']

        # 1. Stop loss hit
        if position_type == 'LONG':
            if current_price <= position['stop_loss']:
                exit_signals.append('STOP_LOSS_HIT')
        else:  # SHORT
            if current_price >= position['stop_loss']:
                exit_signals.append('STOP_LOSS_HIT')

        # 2. Target2 hit (full exit)
        if position_type == 'LONG':
            if current_price >= position['target2']:
                exit_signals.append('TARGET2_HIT')
        else:  # SHORT
            if current_price <= position['target2']:
                exit_signals.append('TARGET2_HIT')

        # 3. Pattern invalidation
        if self.config['exit_rules']['pattern_invalidation_exit']:
            if self.pattern_invalidated(position, current_data):
                exit_signals.append('PATTERN_INVALIDATION')

        # 4. Max hold time exceeded
        entry_time = datetime.fromisoformat(position['entry_time'])
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600
        max_hold = self.config['exit_rules']['max_hold_time_hours']

        if hours_held > max_hold:
            exit_signals.append('MAX_HOLD_TIME')

        # 5. Trend reversal
        if current_data.get('trend', {}).get('direction'):
            expected_trend = 'uptrend' if position_type == 'LONG' else 'downtrend'
            if current_data['trend']['direction'] != expected_trend:
                exit_signals.append('TREND_REVERSAL')

        return exit_signals

    def should_partial_exit(self, position: Dict, current_price: float) -> bool:
        """Check if position should take partial profit at target1"""

        if position_type == 'LONG':
            return current_price >= position['target1']
        else:  # SHORT
            return current_price <= position['target1']

    def update_trailing_stop(self, position: Dict, current_price: float):
        """Update trailing stop based on price movement"""

        position_type = position['type']
        entry_price = position['entry_price']

        # Only trail after reaching target1
        if not position['partial_exit_done']:
            return

        # Calculate trailing stop distance (e.g., 2% of entry price)
        trail_distance = entry_price * 0.02

        if position_type == 'LONG':
            # Trail stop up as price rises
            potential_stop = current_price - trail_distance

            if position['trailing_stop'] is None:
                position['trailing_stop'] = potential_stop
            elif potential_stop > position['trailing_stop']:
                old_stop = position['trailing_stop']
                position['trailing_stop'] = potential_stop
                position['stop_loss'] = potential_stop
                print(f"[TRAIL] {position['symbol']} stop moved from {old_stop:.2f} to {potential_stop:.2f}")

        else:  # SHORT
            # Trail stop down as price falls
            potential_stop = current_price + trail_distance

            if position['trailing_stop'] is None:
                position['trailing_stop'] = potential_stop
            elif potential_stop < position['trailing_stop']:
                old_stop = position['trailing_stop']
                position['trailing_stop'] = potential_stop
                position['stop_loss'] = potential_stop
                print(f"[TRAIL] {position['symbol']} stop moved from {old_stop:.2f} to {potential_stop:.2f}")

    def pattern_invalidated(self, position: Dict, current_data: Dict) -> bool:
        """Check if the entry pattern has been invalidated"""

        # Example: If entered on bullish engulfing, invalidated if price breaks below entry candle low
        position_type = position['type']
        current_price = current_data.get('current_price', position['current_price'])

        if 'pattern_invalidation_level' in position:
            if position_type == 'LONG':
                return current_price < position['pattern_invalidation_level']
            else:  # SHORT
                return current_price > position['pattern_invalidation_level']

        return False

    def should_exit_position(self, symbol: str) -> Optional[str]:
        """Determine if position should be exited and return reason"""

        position = None
        for p in self.positions:
            if p['symbol'] == symbol:
                position = p
                break

        if not position:
            return None

        exit_reasons = position.get('exit_reasons', [])

        # Priority order of exits
        priority_exits = [
            'STOP_LOSS_HIT',
            'TARGET2_HIT',
            'PATTERN_INVALIDATION',
            'TREND_REVERSAL',
            'MAX_HOLD_TIME'
        ]

        for reason in priority_exits:
            if reason in exit_reasons:
                return reason

        return None

    def close_position(self, symbol: str, exit_price: float, exit_reason: str):
        """Close a position and log results"""

        position = None
        index = None

        for i, p in enumerate(self.positions):
            if p['symbol'] == symbol:
                position = p
                index = i
                break

        if not position:
            return None

        # Calculate final P&L
        entry_price = position['entry_price']
        quantity = position.get('quantity', 1)

        if position['type'] == 'LONG':
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            pnl_amount = (exit_price - entry_price) * quantity
        else:  # SHORT
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
            pnl_amount = (entry_price - exit_price) * quantity

        # Create exit record
        exit_record = {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now().isoformat(),
            'exit_reason': exit_reason,
            'final_pnl_percent': pnl_pct,
            'final_pnl_amount': pnl_amount,
            'winner': pnl_amount > 0
        }

        # Log exit
        self.log_position_event(exit_record, 'EXIT')

        # Save to closed trades
        self.save_closed_trade(exit_record)

        # Remove from open positions
        self.positions.pop(index)
        self.save_positions()

        return exit_record

    def log_position_event(self, position: Dict, event_type: str):
        """Log position event to journal"""

        timestamp = datetime.now().strftime('%Y%m%d')
        journal_file = os.path.join(self.base_path, 'journals', f'journal_{timestamp}.jsonl')

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': f'position_{event_type.lower()}',
            'symbol': position['symbol'],
            'event': event_type,
            'price': position.get('current_price', position.get('entry_price')),
            'pnl_percent': position.get('pnl_percent', 0),
            'details': position
        }

        with open(journal_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def save_closed_trade(self, trade: Dict):
        """Save closed trade to analysis folder"""

        timestamp = datetime.now().strftime('%Y%m%d')
        trades_file = os.path.join(self.base_path, 'analysis', f'closed_trades_{timestamp}.json')

        # Load existing trades
        if os.path.exists(trades_file):
            with open(trades_file, 'r') as f:
                trades = json.load(f)
        else:
            trades = []

        trades.append(trade)

        with open(trades_file, 'w') as f:
            json.dump(trades, f, indent=2)

    def get_open_positions(self) -> List[Dict]:
        """Return all open positions"""
        return self.positions

    def get_position_summary(self) -> Dict:
        """Get summary of all open positions"""

        total_pnl = sum([p.get('pnl_amount', 0) for p in self.positions])
        winning = len([p for p in self.positions if p.get('pnl_amount', 0) > 0])
        losing = len([p for p in self.positions if p.get('pnl_amount', 0) < 0])

        return {
            'total_positions': len(self.positions),
            'winning_positions': winning,
            'losing_positions': losing,
            'total_pnl': total_pnl,
            'symbols': [p['symbol'] for p in self.positions]
        }


def main():
    """Test the exit manager"""

    config_path = "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3/config/trading_rules.json"
    manager = ExitManager(config_path)

    # Display open positions
    positions = manager.get_open_positions()

    if positions:
        print("\n" + "="*60)
        print("OPEN POSITIONS")
        print("="*60 + "\n")

        for p in positions:
            print(f"Symbol: {p['symbol']}")
            print(f"Type: {p['type']}")
            print(f"Entry: ₹{p['entry_price']:.2f}")
            print(f"Current: ₹{p.get('current_price', 'N/A')}")
            print(f"Stop: ₹{p['stop_loss']:.2f}")
            print(f"Target1: ₹{p['target1']:.2f}")
            print(f"Target2: ₹{p['target2']:.2f}")
            print(f"P&L: {p.get('pnl_percent', 0):.2f}%")
            print(f"Exit Signals: {', '.join(p.get('exit_reasons', ['None']))}")
            print("-" * 60)
    else:
        print("\nNo open positions")

    # Display summary
    summary = manager.get_position_summary()
    print("\nSUMMARY:")
    print(f"Total Positions: {summary['total_positions']}")
    print(f"Total P&L: ₹{summary['total_pnl']:.2f}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
