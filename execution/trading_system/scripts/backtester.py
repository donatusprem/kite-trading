#!/usr/bin/env python3
"""
BACKTESTING ENGINE - Trading System V3
Tests scanner + exit manager logic against historical data
Validates edge before live trading
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd

# Add scripts to path
sys.path.insert(0, os.path.dirname(__file__))

from market_scanner import MarketScanner
from exit_manager import ExitManager


class Backtester:
    """
    Backtest trading system against historical data
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.scanner = MarketScanner(config_path)
        self.exit_manager = ExitManager(config_path)

        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Backtest settings
        self.min_score = self.config['entry_rules']['minimum_score']
        self.position_size = self.config['position_limits']['position_size']

        # Results tracking
        self.all_trades = []
        self.equity_curve = []
        self.starting_capital = 100000  # ₹1 lakh for testing
        self.current_capital = self.starting_capital

    def fetch_historical_data_kite(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """
        Fetch historical data via Kite MCP
        Returns: DataFrame with OHLCV data
        """
        # TODO: Implement Kite MCP historical data fetch
        # For now, return structure that would come from Kite
        # This will be replaced with actual MCP call

        print(f"  [FETCH] Getting {days} days of data for {symbol}")

        # Placeholder - will use Kite historical bars
        # Example structure:
        # df = kite_client.get_historical_data(
        #     symbol=symbol,
        #     from_date=(datetime.now() - timedelta(days=days)),
        #     to_date=datetime.now(),
        #     interval='day'
        # )

        return None  # Will be implemented with Kite MCP

    def simulate_trade(self, entry_signal: Dict, historical_data: pd.DataFrame,
                       entry_idx: int) -> Dict:
        """
        Simulate a trade from entry to exit

        Args:
            entry_signal: Scanner output (score, setup, levels)
            historical_data: Full OHLCV data
            entry_idx: Index where entry occurs

        Returns:
            Trade result dictionary
        """

        # Extract entry details
        symbol = entry_signal['symbol']
        entry_price = historical_data.iloc[entry_idx]['close']
        entry_date = historical_data.iloc[entry_idx]['timestamp']

        # Create position
        position = {
            'symbol': symbol,
            'type': entry_signal['setup_type'],
            'entry_price': entry_price,
            'entry_date': entry_date,
            'quantity': int(self.position_size / entry_price),
            'position_size': self.position_size,
            'score': entry_signal['score'],
            'support_level': entry_signal.get('support_level'),
            'resistance_level': entry_signal.get('resistance_level'),
            'setup_details': entry_signal.get('setup_details', {})
        }

        # Add to exit manager (simulated)
        exit_result = self.exit_manager.add_position(position)

        # Track position through subsequent bars
        for i in range(entry_idx + 1, len(historical_data)):
            bar = historical_data.iloc[i]
            current_price = bar['close']

            # Check if stop hit during the day (use low/high)
            if position['type'] == 'LONG':
                if bar['low'] <= exit_result['stop_loss']:
                    # Stop hit
                    exit_price = exit_result['stop_loss']
                    exit_reason = 'STOP_LOSS'
                    exit_date = bar['timestamp']
                    break

                # Check targets
                if bar['high'] >= exit_result['target1'] and not exit_result.get('t1_hit'):
                    # Target 1 hit - partial exit (50%)
                    exit_result['t1_hit'] = True
                    exit_result['t1_price'] = exit_result['target1']
                    exit_result['t1_date'] = bar['timestamp']
                    # Move stop to breakeven
                    exit_result['stop_loss'] = entry_price

                if bar['high'] >= exit_result['target2']:
                    # Target 2 hit - full exit
                    exit_price = exit_result['target2']
                    exit_reason = 'TARGET2_HIT'
                    exit_date = bar['timestamp']
                    break

            else:  # SHORT
                if bar['high'] >= exit_result['stop_loss']:
                    exit_price = exit_result['stop_loss']
                    exit_reason = 'STOP_LOSS'
                    exit_date = bar['timestamp']
                    break

                if bar['low'] <= exit_result['target1'] and not exit_result.get('t1_hit'):
                    exit_result['t1_hit'] = True
                    exit_result['t1_price'] = exit_result['target1']
                    exit_result['t1_date'] = bar['timestamp']
                    exit_result['stop_loss'] = entry_price

                if bar['low'] <= exit_result['target2']:
                    exit_price = exit_result['target2']
                    exit_reason = 'TARGET2_HIT'
                    exit_date = bar['timestamp']
                    break

            # Max hold period check (48 hours = 2 trading days)
            if i - entry_idx >= 2:
                exit_price = current_price
                exit_reason = 'TIME_LIMIT'
                exit_date = bar['timestamp']
                break
        else:
            # End of data - force exit at last price
            exit_price = historical_data.iloc[-1]['close']
            exit_reason = 'END_OF_DATA'
            exit_date = historical_data.iloc[-1]['timestamp']

        # Calculate P&L
        if exit_result.get('t1_hit'):
            # Partial exit occurred
            qty_t1 = position['quantity'] // 2
            qty_remaining = position['quantity'] - qty_t1

            if position['type'] == 'LONG':
                pnl_t1 = (exit_result['t1_price'] - entry_price) * qty_t1
                pnl_t2 = (exit_price - entry_price) * qty_remaining
            else:
                pnl_t1 = (entry_price - exit_result['t1_price']) * qty_t1
                pnl_t2 = (entry_price - exit_price) * qty_remaining

            total_pnl = pnl_t1 + pnl_t2
        else:
            # Full position exit
            if position['type'] == 'LONG':
                total_pnl = (exit_price - entry_price) * position['quantity']
            else:
                total_pnl = (entry_price - exit_price) * position['quantity']

        pnl_pct = (total_pnl / self.position_size) * 100

        # Calculate R (risk multiple)
        risk = abs(entry_price - exit_result['stop_loss']) * position['quantity']
        r_multiple = total_pnl / risk if risk > 0 else 0

        # Hold period
        hold_days = (exit_date - entry_date).days if isinstance(exit_date, datetime) else 0

        # Build trade result
        trade_result = {
            'symbol': symbol,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'position_size': self.position_size,
            'pnl': total_pnl,
            'pnl_pct': pnl_pct,
            'r_multiple': r_multiple,
            'hold_days': hold_days,
            'exit_reason': exit_reason,
            'score': entry_signal['score'],
            'setup_type': entry_signal['setup_type'],
            'pattern': entry_signal.get('setup_details', {}).get('pattern', 'unknown'),
            'partial_exit': exit_result.get('t1_hit', False),
            'win': total_pnl > 0
        }

        return trade_result

    def run_backtest(self, symbols: List[str], days: int = 90,
                     score_threshold: int = None) -> Dict:
        """
        Run full backtest on symbol list

        Args:
            symbols: List of stock symbols to test
            days: Historical period to test
            score_threshold: Override minimum score (default from config)

        Returns:
            Performance statistics
        """

        if score_threshold is None:
            score_threshold = self.min_score

        print("\n" + "="*70)
        print("  BACKTESTING ENGINE - Trading System V3")
        print("="*70)
        print(f"\nSymbols: {len(symbols)}")
        print(f"Period: {days} days")
        print(f"Min Score: {score_threshold}")
        print(f"Position Size: ₹{self.position_size:,}")
        print(f"Starting Capital: ₹{self.starting_capital:,}")
        print("\n" + "-"*70)

        all_signals = []

        # Phase 1: Scan historical data for all signals
        print("\n[PHASE 1] Scanning historical data for setups...")
        print("-"*70)

        for symbol in symbols:
            print(f"\n[SCAN] {symbol}")

            # Fetch historical data
            hist_data = self.fetch_historical_data_kite(symbol, days)

            if hist_data is None:
                print(f"  ⚠️  No data available for {symbol}")
                continue

            # Run scanner on each bar (sliding window)
            for i in range(20, len(hist_data) - 2):  # Need lookback + forward bars
                # Get window of data up to this point
                window = hist_data.iloc[:i+1].copy()

                # Analyze this setup
                analysis = self.scanner.analyze_stock(symbol, window)

                if analysis and analysis.get('score', 0) >= score_threshold:
                    # Valid setup found
                    signal = {
                        'symbol': symbol,
                        'date': window.iloc[-1]['timestamp'],
                        'bar_index': i,
                        'score': analysis['score'],
                        'setup_type': analysis['setup_type'],
                        'support_level': analysis.get('support', [0])[0] if analysis.get('support') else None,
                        'resistance_level': analysis.get('resistance', [0])[0] if analysis.get('resistance') else None,
                        'setup_details': analysis.get('setup_details', {}),
                        'hist_data': hist_data  # Store for simulation
                    }
                    all_signals.append(signal)
                    print(f"  ✅ Found setup at {window.iloc[-1]['timestamp']} - Score: {analysis['score']}")

        print(f"\n[FOUND] {len(all_signals)} total setups matching criteria")
        print("-"*70)

        # Phase 2: Simulate trades
        print("\n[PHASE 2] Simulating trades with exit management...")
        print("-"*70)

        for idx, signal in enumerate(all_signals, 1):
            print(f"\n[TRADE {idx}/{len(all_signals)}] {signal['symbol']} - Score: {signal['score']}")

            # Simulate this trade
            trade_result = self.simulate_trade(
                entry_signal=signal,
                historical_data=signal['hist_data'],
                entry_idx=signal['bar_index']
            )

            self.all_trades.append(trade_result)

            # Update capital
            self.current_capital += trade_result['pnl']

            # Track equity curve
            self.equity_curve.append({
                'trade_num': idx,
                'capital': self.current_capital,
                'pnl': trade_result['pnl'],
                'pnl_pct': trade_result['pnl_pct']
            })

            # Print result
            result_emoji = "✅" if trade_result['win'] else "❌"
            print(f"  {result_emoji} Exit: {trade_result['exit_reason']}")
            print(f"     P&L: ₹{trade_result['pnl']:.2f} ({trade_result['pnl_pct']:.2f}%)")
            print(f"     R Multiple: {trade_result['r_multiple']:.2f}R")
            print(f"     Hold: {trade_result['hold_days']} days")

        print("\n" + "="*70)

        # Phase 3: Calculate statistics
        return self.calculate_statistics()

    def calculate_statistics(self) -> Dict:
        """
        Calculate comprehensive backtest statistics
        """

        if not self.all_trades:
            return {'error': 'No trades to analyze'}

        # Basic metrics
        total_trades = len(self.all_trades)
        winners = [t for t in self.all_trades if t['win']]
        losers = [t for t in self.all_trades if not t['win']]

        win_rate = (len(winners) / total_trades) * 100

        # P&L metrics
        total_pnl = sum(t['pnl'] for t in self.all_trades)
        avg_win = sum(t['pnl'] for t in winners) / len(winners) if winners else 0
        avg_loss = sum(t['pnl'] for t in losers) / len(losers) if losers else 0

        # Profit factor
        gross_profit = sum(t['pnl'] for t in winners)
        gross_loss = abs(sum(t['pnl'] for t in losers))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # R multiples
        avg_r = sum(t['r_multiple'] for t in self.all_trades) / total_trades
        expectancy = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)

        # Drawdown
        peak = self.starting_capital
        max_dd = 0
        for point in self.equity_curve:
            if point['capital'] > peak:
                peak = point['capital']
            dd = ((peak - point['capital']) / peak) * 100
            if dd > max_dd:
                max_dd = dd

        # By score range
        score_ranges = {
            '90-100': [t for t in self.all_trades if t['score'] >= 90],
            '80-89': [t for t in self.all_trades if 80 <= t['score'] < 90],
            '75-79': [t for t in self.all_trades if 75 <= t['score'] < 80]
        }

        score_stats = {}
        for range_name, trades in score_ranges.items():
            if trades:
                score_stats[range_name] = {
                    'count': len(trades),
                    'win_rate': (len([t for t in trades if t['win']]) / len(trades)) * 100,
                    'avg_r': sum(t['r_multiple'] for t in trades) / len(trades)
                }

        # By pattern
        patterns = {}
        for trade in self.all_trades:
            pattern = trade.get('pattern', 'unknown')
            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(trade)

        pattern_stats = {}
        for pattern, trades in patterns.items():
            pattern_stats[pattern] = {
                'count': len(trades),
                'win_rate': (len([t for t in trades if t['win']]) / len(trades)) * 100,
                'avg_pnl': sum(t['pnl'] for t in trades) / len(trades)
            }

        # Return statistics
        stats = {
            'overview': {
                'total_trades': total_trades,
                'winners': len(winners),
                'losers': len(losers),
                'win_rate': win_rate,
                'profit_factor': profit_factor
            },
            'returns': {
                'total_pnl': total_pnl,
                'total_return_pct': ((self.current_capital - self.starting_capital) / self.starting_capital) * 100,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'avg_r_multiple': avg_r,
                'expectancy': expectancy
            },
            'risk': {
                'max_drawdown_pct': max_dd,
                'largest_win': max(t['pnl'] for t in self.all_trades),
                'largest_loss': min(t['pnl'] for t in self.all_trades)
            },
            'by_score': score_stats,
            'by_pattern': pattern_stats,
            'equity_curve': self.equity_curve,
            'all_trades': self.all_trades
        }

        return stats

    def print_report(self, stats: Dict):
        """
        Print formatted backtest report
        """

        print("\n\n" + "="*70)
        print("  📊 BACKTEST RESULTS")
        print("="*70)

        # Overview
        print("\n🎯 OVERVIEW")
        print("-"*70)
        ov = stats['overview']
        print(f"Total Trades:    {ov['total_trades']}")
        print(f"Winners:         {ov['winners']} ({(ov['winners']/ov['total_trades'])*100:.1f}%)")
        print(f"Losers:          {ov['losers']} ({(ov['losers']/ov['total_trades'])*100:.1f}%)")
        print(f"Win Rate:        {ov['win_rate']:.2f}%")
        print(f"Profit Factor:   {ov['profit_factor']:.2f}")

        # Returns
        print("\n💰 RETURNS")
        print("-"*70)
        ret = stats['returns']
        print(f"Total P&L:       ₹{ret['total_pnl']:,.2f}")
        print(f"Total Return:    {ret['total_return_pct']:.2f}%")
        print(f"Avg Win:         ₹{ret['avg_win']:,.2f}")
        print(f"Avg Loss:        ₹{ret['avg_loss']:,.2f}")
        print(f"Avg R Multiple:  {ret['avg_r_multiple']:.2f}R")
        print(f"Expectancy:      ₹{ret['expectancy']:,.2f} per trade")

        # Risk
        print("\n⚠️  RISK METRICS")
        print("-"*70)
        risk = stats['risk']
        print(f"Max Drawdown:    {risk['max_drawdown_pct']:.2f}%")
        print(f"Largest Win:     ₹{risk['largest_win']:,.2f}")
        print(f"Largest Loss:    ₹{risk['largest_loss']:,.2f}")

        # By Score
        if stats['by_score']:
            print("\n📈 PERFORMANCE BY SCORE RANGE")
            print("-"*70)
            for score_range, data in sorted(stats['by_score'].items(), reverse=True):
                print(f"\n{score_range} Score:")
                print(f"  Trades:    {data['count']}")
                print(f"  Win Rate:  {data['win_rate']:.1f}%")
                print(f"  Avg R:     {data['avg_r']:.2f}R")

        # By Pattern
        if stats['by_pattern']:
            print("\n🎨 PERFORMANCE BY PATTERN")
            print("-"*70)
            for pattern, data in sorted(stats['by_pattern'].items(),
                                       key=lambda x: x[1]['win_rate'],
                                       reverse=True):
                print(f"\n{pattern}:")
                print(f"  Trades:    {data['count']}")
                print(f"  Win Rate:  {data['win_rate']:.1f}%")
                print(f"  Avg P&L:   ₹{data['avg_pnl']:,.2f}")

        print("\n" + "="*70)
        print("\n✅ Backtest complete!")
        print("\nResults saved to: analysis/backtest_results_*.json")
        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    """
    Run backtest from command line
    """

    # Configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'trading_rules.json')

    # Test symbols (same as live watchlist)
    test_symbols = [
        'ADANIGREEN',
        'ADANIPORTS',
        'APOLLOHOSP',
        'BAJFINANCE',
        'BEL',
        'HINDALCO',
        'INDUSINDBK',
        'NTPC',
        'ONGC',
        'POWERGRID',
        'RELIANCE',
        'SBIN',
        'TATAMOTORS',
        'TATAPOWER'
    ]

    # Create backtester
    backtester = Backtester(config_path)

    # Run backtest
    print("\n🚀 Starting backtest...")
    print("="*70)

    stats = backtester.run_backtest(
        symbols=test_symbols,
        days=90,  # Last 3 months
        score_threshold=75  # Same as live system
    )

    # Print report
    backtester.print_report(stats)

    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'analysis')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'backtest_results_{timestamp}.json')

    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {output_file}\n")
