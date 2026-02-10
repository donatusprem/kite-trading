#!/usr/bin/env python3
"""
TRADE LOGGER - Complete trade and chart analysis logging
Logs every entry with timing, chart analysis, and all relevant data
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class TradeLogger:
    """
    Comprehensive trade logging with chart analysis timing
    """

    def __init__(self, journal_dir: str = '../journals'):
        self.journal_dir = journal_dir
        self.trades_file = os.path.join(journal_dir, 'trades_log.json')
        self.csv_file = os.path.join(journal_dir, 'trades_log.csv')

        # Create journal directory if needed
        os.makedirs(journal_dir, exist_ok=True)

        # Load existing trades
        self.trades = self._load_trades()

    def _load_trades(self) -> List[Dict]:
        """Load existing trade log"""
        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def log_analysis(self,
                    symbol: str,
                    analysis_data: Dict,
                    chart_data: Dict,
                    scanner_timestamp: datetime = None) -> str:
        """
        Log chart analysis when setup is detected

        Args:
            symbol: Stock symbol
            analysis_data: Technical analysis output from scanner
            chart_data: OHLCV data used for analysis
            scanner_timestamp: When scanner detected this setup

        Returns:
            Analysis ID for linking to trade entry
        """

        if scanner_timestamp is None:
            scanner_timestamp = datetime.now()

        analysis_id = f"{symbol}_{scanner_timestamp.strftime('%Y%m%d_%H%M%S')}"

        analysis_log = {
            'analysis_id': analysis_id,
            'symbol': symbol,
            'timestamp': scanner_timestamp.isoformat(),
            'timestamp_readable': scanner_timestamp.strftime('%Y-%m-%d %H:%M:%S'),

            # Chart data at analysis time
            'chart_snapshot': {
                'last_close': chart_data.get('close'),
                'last_high': chart_data.get('high'),
                'last_low': chart_data.get('low'),
                'last_volume': chart_data.get('volume'),
                'timestamp': chart_data.get('timestamp')
            },

            # Technical analysis
            'score': analysis_data.get('score', 0),
            'setup_type': analysis_data.get('setup_type', 'unknown'),

            # Support/Resistance
            'support_levels': analysis_data.get('support', []),
            'resistance_levels': analysis_data.get('resistance', []),
            'key_support': analysis_data.get('support', [None])[0],
            'key_resistance': analysis_data.get('resistance', [None])[0],

            # Fair Value Gaps
            'fvgs': analysis_data.get('fvgs', []),
            'bullish_fvgs': [fvg for fvg in analysis_data.get('fvgs', []) if fvg.get('type') == 'bullish'],
            'bearish_fvgs': [fvg for fvg in analysis_data.get('fvgs', []) if fvg.get('type') == 'bearish'],

            # Trend
            'trend': analysis_data.get('trend', {}),
            'trend_direction': analysis_data.get('trend', {}).get('direction', 'unknown'),
            'trend_strength': analysis_data.get('trend', {}).get('strength', 0),

            # Patterns detected
            'patterns': analysis_data.get('patterns', []),

            # Volume analysis
            'volume_analysis': analysis_data.get('volume', {}),

            # Complete analysis data (for reference)
            'full_analysis': analysis_data
        }

        # Save analysis log
        analysis_file = os.path.join(self.journal_dir, f'analysis_{analysis_id}.json')
        with open(analysis_file, 'w') as f:
            json.dump(analysis_log, f, indent=2)

        return analysis_id

    def log_entry(self,
                 symbol: str,
                 entry_price: float,
                 quantity: int,
                 position_size: float,
                 stop_loss: float,
                 target1: float,
                 target2: float,
                 setup_type: str,
                 score: int,
                 analysis_id: Optional[str] = None,
                 entry_reason: str = '',
                 chart_at_entry: Optional[Dict] = None,
                 timing_analysis: Optional[Dict] = None) -> str:
        """
        Log trade entry with complete context

        Args:
            symbol: Stock symbol
            entry_price: Entry execution price
            quantity: Number of shares
            position_size: Total position value
            stop_loss: Stop loss price
            target1: First target price
            target2: Second target price
            setup_type: Type of setup (e.g., 'pullback_long')
            score: Scanner score (0-100)
            analysis_id: Link to chart analysis log
            entry_reason: Why this trade was taken
            chart_at_entry: Current chart data at entry time
            timing_analysis: Timing analysis data

        Returns:
            Trade ID
        """

        entry_timestamp = datetime.now()
        trade_id = f"TRADE_{symbol}_{entry_timestamp.strftime('%Y%m%d_%H%M%S')}"

        # Calculate R:R
        risk = abs(entry_price - stop_loss)
        reward1 = abs(target1 - entry_price)
        reward2 = abs(target2 - entry_price)
        rr1 = reward1 / risk if risk > 0 else 0
        rr2 = reward2 / risk if risk > 0 else 0

        trade_log = {
            'trade_id': trade_id,
            'analysis_id': analysis_id,
            'status': 'OPEN',

            # Basic info
            'symbol': symbol,
            'entry_timestamp': entry_timestamp.isoformat(),
            'entry_timestamp_readable': entry_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'entry_time_of_day': entry_timestamp.strftime('%H:%M:%S'),

            # Entry details
            'entry_price': entry_price,
            'quantity': quantity,
            'position_size': position_size,
            'setup_type': setup_type,
            'score': score,
            'entry_reason': entry_reason,

            # Risk management
            'stop_loss': stop_loss,
            'target1': target1,
            'target2': target2,
            'risk_per_share': risk,
            'risk_amount': risk * quantity,
            'risk_percent': (risk / entry_price) * 100,
            'reward1_per_share': reward1,
            'reward2_per_share': reward2,
            'rr_ratio_t1': rr1,
            'rr_ratio_t2': rr2,

            # Timing analysis
            'timing_analysis': timing_analysis or {},

            # Chart at entry
            'chart_at_entry': chart_at_entry or {},

            # Exit tracking (populated later)
            'exit_timestamp': None,
            'exit_price': None,
            'exit_reason': None,
            'exit_type': None,  # 'stop', 'target1', 'target2', 'time', 'pattern_invalid'
            'pnl': None,
            'pnl_percent': None,
            'r_multiple': None,
            'hold_time_minutes': None,

            # Post-trade analysis (populated after exit)
            'was_optimal_entry': None,
            'entry_vs_analysis_delay_minutes': None,
            'lessons_learned': []
        }

        # If we have analysis timing, calculate delay
        if analysis_id and timing_analysis:
            analysis_time = timing_analysis.get('analysis_timestamp')
            if analysis_time:
                try:
                    analysis_dt = datetime.fromisoformat(analysis_time)
                    delay = (entry_timestamp - analysis_dt).total_seconds() / 60
                    trade_log['entry_vs_analysis_delay_minutes'] = round(delay, 2)
                except:
                    pass

        # Add to trades list
        self.trades.append(trade_log)

        # Save
        self._save_trades()

        print(f"\n✅ Trade logged: {trade_id}")
        print(f"   Symbol: {symbol} @ ₹{entry_price}")
        print(f"   Score: {score} | Setup: {setup_type}")
        print(f"   R:R: {rr1:.2f}:1 (T1) / {rr2:.2f}:1 (T2)")
        if trade_log['entry_vs_analysis_delay_minutes']:
            print(f"   Entry delay: {trade_log['entry_vs_analysis_delay_minutes']} minutes after analysis")

        return trade_id

    def log_exit(self,
                trade_id: str,
                exit_price: float,
                exit_reason: str,
                exit_type: str,
                chart_at_exit: Optional[Dict] = None,
                exit_analysis: Optional[Dict] = None):
        """
        Log trade exit

        Args:
            trade_id: Trade ID to update
            exit_price: Exit execution price
            exit_reason: Why exited
            exit_type: Type of exit ('stop', 'target1', 'target2', etc.)
            chart_at_exit: Chart data at exit
            exit_analysis: Post-exit analysis
        """

        exit_timestamp = datetime.now()

        # Find trade
        trade = next((t for t in self.trades if t['trade_id'] == trade_id), None)
        if not trade:
            print(f"❌ Trade {trade_id} not found!")
            return

        # Calculate P&L
        entry_price = trade['entry_price']
        quantity = trade['quantity']

        if trade['setup_type'].endswith('_long'):
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity

        pnl_percent = (pnl / trade['position_size']) * 100

        # Calculate R multiple
        risk_amount = trade['risk_amount']
        r_multiple = pnl / risk_amount if risk_amount > 0 else 0

        # Hold time
        entry_time = datetime.fromisoformat(trade['entry_timestamp'])
        hold_time = (exit_timestamp - entry_time).total_seconds() / 60

        # Update trade
        trade.update({
            'status': 'CLOSED',
            'exit_timestamp': exit_timestamp.isoformat(),
            'exit_timestamp_readable': exit_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'exit_time_of_day': exit_timestamp.strftime('%H:%M:%S'),
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'exit_type': exit_type,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'r_multiple': r_multiple,
            'hold_time_minutes': hold_time,
            'chart_at_exit': chart_at_exit or {},
            'exit_analysis': exit_analysis or {}
        })

        # Save
        self._save_trades()

        win_loss = "WIN ✅" if pnl > 0 else "LOSS ❌"
        print(f"\n{win_loss} Trade closed: {trade_id}")
        print(f"   Exit: {exit_type} | ₹{exit_price}")
        print(f"   P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)")
        print(f"   R: {r_multiple:+.2f}R")
        print(f"   Hold: {hold_time:.0f} minutes")

    def log_post_trade_analysis(self,
                                trade_id: str,
                                was_optimal_entry: bool,
                                lessons_learned: List[str],
                                additional_notes: str = ''):
        """
        Add post-trade analysis and lessons

        Args:
            trade_id: Trade to update
            was_optimal_entry: Whether entry timing was optimal
            lessons_learned: List of lessons from this trade
            additional_notes: Any additional observations
        """

        trade = next((t for t in self.trades if t['trade_id'] == trade_id), None)
        if not trade:
            print(f"❌ Trade {trade_id} not found!")
            return

        trade.update({
            'was_optimal_entry': was_optimal_entry,
            'lessons_learned': lessons_learned,
            'post_trade_notes': additional_notes
        })

        self._save_trades()

        print(f"\n📝 Post-trade analysis added for {trade_id}")
        print(f"   Optimal entry: {'Yes ✅' if was_optimal_entry else 'No ❌'}")
        print(f"   Lessons: {len(lessons_learned)}")

    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get specific trade"""
        return next((t for t in self.trades if t['trade_id'] == trade_id), None)

    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        return [t for t in self.trades if t['status'] == 'OPEN']

    def get_closed_trades(self) -> List[Dict]:
        """Get all closed trades"""
        return [t for t in self.trades if t['status'] == 'CLOSED']

    def get_performance_summary(self) -> Dict:
        """Get performance metrics"""

        closed = self.get_closed_trades()

        if not closed:
            return {'error': 'No closed trades yet'}

        wins = [t for t in closed if t['pnl'] > 0]
        losses = [t for t in closed if t['pnl'] <= 0]

        total_pnl = sum(t['pnl'] for t in closed)
        total_r = sum(t['r_multiple'] for t in closed)
        avg_hold_time = sum(t['hold_time_minutes'] for t in closed) / len(closed)

        return {
            'total_trades': len(closed),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(closed)) * 100,
            'total_pnl': total_pnl,
            'avg_pnl_per_trade': total_pnl / len(closed),
            'avg_r_multiple': total_r / len(closed),
            'avg_hold_time_minutes': avg_hold_time,
            'exit_types': {
                'stop': len([t for t in closed if t['exit_type'] == 'stop']),
                'target1': len([t for t in closed if t['exit_type'] == 'target1']),
                'target2': len([t for t in closed if t['exit_type'] == 'target2']),
                'time': len([t for t in closed if t['exit_type'] == 'time']),
                'pattern_invalid': len([t for t in closed if t['exit_type'] == 'pattern_invalid'])
            }
        }

    def export_to_csv(self):
        """Export trades to CSV for analysis"""

        if not self.trades:
            print("No trades to export")
            return

        # Flatten trades for CSV
        rows = []
        for trade in self.trades:
            row = {
                'trade_id': trade['trade_id'],
                'symbol': trade['symbol'],
                'entry_date': trade.get('entry_timestamp_readable', ''),
                'entry_time': trade.get('entry_time_of_day', ''),
                'exit_date': trade.get('exit_timestamp_readable', ''),
                'exit_time': trade.get('exit_time_of_day', ''),
                'status': trade['status'],
                'score': trade['score'],
                'setup_type': trade['setup_type'],
                'entry_price': trade['entry_price'],
                'exit_price': trade.get('exit_price', ''),
                'quantity': trade['quantity'],
                'position_size': trade['position_size'],
                'stop_loss': trade['stop_loss'],
                'target1': trade['target1'],
                'target2': trade['target2'],
                'rr_t1': trade['rr_ratio_t1'],
                'rr_t2': trade['rr_ratio_t2'],
                'exit_type': trade.get('exit_type', ''),
                'exit_reason': trade.get('exit_reason', ''),
                'pnl': trade.get('pnl', ''),
                'pnl_percent': trade.get('pnl_percent', ''),
                'r_multiple': trade.get('r_multiple', ''),
                'hold_time_min': trade.get('hold_time_minutes', ''),
                'entry_delay_min': trade.get('entry_vs_analysis_delay_minutes', ''),
                'optimal_entry': trade.get('was_optimal_entry', '')
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(self.csv_file, index=False)

        print(f"\n✅ Exported {len(rows)} trades to {self.csv_file}")

    def print_summary(self):
        """Print formatted summary"""

        summary = self.get_performance_summary()

        if 'error' in summary:
            print("\n⚠️  No closed trades yet to analyze")
            return

        print("\n" + "="*60)
        print("📊 TRADING PERFORMANCE SUMMARY")
        print("="*60)

        print(f"\nTotal Trades: {summary['total_trades']}")
        print(f"Wins: {summary['wins']} ({summary['win_rate']:.1f}%)")
        print(f"Losses: {summary['losses']}")

        print(f"\nTotal P&L: ₹{summary['total_pnl']:,.2f}")
        print(f"Avg P&L per Trade: ₹{summary['avg_pnl_per_trade']:.2f}")
        print(f"Avg R Multiple: {summary['avg_r_multiple']:.2f}R")

        print(f"\nAvg Hold Time: {summary['avg_hold_time_minutes']:.0f} minutes")

        print("\nExit Types:")
        for exit_type, count in summary['exit_types'].items():
            print(f"  {exit_type}: {count}")

        print("\n" + "="*60)

    def _save_trades(self):
        """Save trades to JSON and CSV"""

        # Save JSON
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades, f, indent=2)

        # Update CSV
        self.export_to_csv()


if __name__ == '__main__':
    """Demo usage"""

    print("\n" + "="*60)
    print("TRADE LOGGER - Demo")
    print("="*60)

    logger = TradeLogger('../journals_demo')

    # Example: Log analysis
    print("\n1️⃣ Logging chart analysis...")

    analysis_id = logger.log_analysis(
        symbol='RELIANCE',
        scanner_timestamp=datetime(2026, 2, 5, 9, 45, 0),
        analysis_data={
            'score': 95,
            'setup_type': 'pullback_long',
            'support': [1445.50, 1430.20],
            'resistance': [1465.80, 1480.00],
            'fvgs': [
                {'type': 'bullish', 'top': 1448, 'bottom': 1442, 'filled': 0.6}
            ],
            'trend': {'direction': 'bullish', 'strength': 0.75},
            'patterns': ['hammer', 'support_bounce']
        },
        chart_data={
            'timestamp': '2026-02-05 09:45:00',
            'close': 1446.80,
            'high': 1449.30,
            'low': 1444.50,
            'volume': 1235400
        }
    )

    # Example: Log entry (2 minutes later)
    print("\n2️⃣ Logging trade entry...")

    trade_id = logger.log_entry(
        symbol='RELIANCE',
        entry_price=1447.50,
        quantity=14,
        position_size=20265,
        stop_loss=1445.00,
        target1=1452.50,
        target2=1460.00,
        setup_type='pullback_long',
        score=95,
        analysis_id=analysis_id,
        entry_reason='Pullback to support + bullish FVG + score 95',
        timing_analysis={
            'analysis_timestamp': '2026-02-05T09:45:00',
            'entry_timestamp': '2026-02-05T09:47:00',
            'delay_minutes': 2,
            'price_at_analysis': 1446.80,
            'price_at_entry': 1447.50,
            'slippage': 0.70
        },
        chart_at_entry={
            'current_price': 1447.50,
            'current_volume': 1245600,
            'trend_still_valid': True
        }
    )

    # Example: Log exit
    print("\n3️⃣ Logging trade exit...")

    logger.log_exit(
        trade_id=trade_id,
        exit_price=1452.50,
        exit_reason='Target 1 hit',
        exit_type='target1',
        chart_at_exit={
            'exit_price': 1452.50,
            'volume_at_exit': 1356000,
            'resistance_tested': True
        }
    )

    # Example: Post-trade analysis
    print("\n4️⃣ Adding post-trade analysis...")

    logger.log_post_trade_analysis(
        trade_id=trade_id,
        was_optimal_entry=True,
        lessons_learned=[
            'Entry within 2 minutes of signal = good execution',
            'Support bounce worked as expected',
            'FVG fill added conviction',
            'Target 1 at resistance was correct placement'
        ],
        additional_notes='Perfect textbook setup - score 95 was accurate'
    )

    # Print summary
    logger.print_summary()

    print("\n✅ Demo complete! Check '../journals_demo/' for saved files\n")
