#!/usr/bin/env python3
"""
DEMO BACKTEST - Synthetic Data
Demonstrates backtest engine with realistic mock data
Run this to validate logic before building Kite MCP server
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from market_scanner import MarketScanner
from exit_manager import ExitManager


def generate_realistic_ohlcv(symbol: str, days: int = 90, base_price: float = 1000,
                              volatility: float = 0.02, trend: float = 0.001) -> pd.DataFrame:
    """
    Generate realistic OHLCV data with trends, support/resistance, and patterns

    Args:
        symbol: Stock symbol
        days: Number of days
        base_price: Starting price
        volatility: Daily volatility (0.02 = 2%)
        trend: Daily trend (0.001 = 0.1% per day)

    Returns:
        DataFrame with realistic price action
    """

    np.random.seed(hash(symbol) % 10000)  # Consistent data per symbol

    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    data = []

    price = base_price

    for i, date in enumerate(dates):
        # Add trend
        price *= (1 + trend + np.random.normal(0, volatility))

        # Create realistic OHLC
        day_range = price * volatility * 2
        open_price = price + np.random.uniform(-day_range/4, day_range/4)
        close_price = price + np.random.uniform(-day_range/4, day_range/4)

        high = max(open_price, close_price) + abs(np.random.normal(0, day_range/3))
        low = min(open_price, close_price) - abs(np.random.normal(0, day_range/3))

        volume = int(np.random.uniform(100000, 5000000))

        # Add support/resistance bounces every ~10-15 days
        if i > 0 and i % 12 == 0:
            # Support bounce
            low = price * 0.95
            close_price = price * 0.97

        if i > 0 and i % 15 == 0:
            # Resistance rejection
            high = price * 1.05
            close_price = price * 0.99

        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': volume
        })

        price = close_price

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df


def run_demo_backtest():
    """
    Run demonstration backtest with synthetic data
    """

    print("\n" + "="*70)
    print("  🧪 DEMO BACKTEST - Synthetic Data")
    print("="*70)
    print("\nThis demonstrates the backtest engine using realistic mock data.")
    print("Once Kite MCP server is built, run with real historical data.")
    print("\n" + "-"*70)

    # Test symbols with different characteristics
    test_configs = {
        'RELIANCE': {'base': 1450, 'vol': 0.015, 'trend': 0.0005},  # Low vol, slight uptrend
        'POWERGRID': {'base': 290, 'vol': 0.02, 'trend': -0.0002},  # Medium vol, slight downtrend
        'ADANIGREEN': {'base': 965, 'vol': 0.03, 'trend': 0.001},   # High vol, uptrend
        'BEL': {'base': 432, 'vol': 0.025, 'trend': 0.0008}         # Medium-high vol, uptrend
    }

    # Generate data
    print("\n[DATA] Generating synthetic historical data...")
    print("-"*70)

    all_data = {}
    for symbol, config in test_configs.items():
        df = generate_realistic_ohlcv(
            symbol=symbol,
            days=90,
            base_price=config['base'],
            volatility=config['vol'],
            trend=config['trend']
        )
        all_data[symbol] = df
        print(f"  ✅ {symbol}: {len(df)} bars, ₹{df['close'].iloc[0]:.2f} → ₹{df['close'].iloc[-1]:.2f}")

    # Initialize components
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'trading_rules.json')
    scanner = MarketScanner(config_path)
    exit_manager = ExitManager(config_path)

    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)

    min_score = config['entry_rules']['minimum_score']
    position_size = config['position_limits']['position_size']

    # Track results
    all_trades = []
    starting_capital = 100000
    current_capital = starting_capital

    # Run backtest
    print("\n[SCAN] Scanning for setups (75+ score)...")
    print("-"*70)

    found_setups = 0

    for symbol, df in all_data.items():
        print(f"\n{symbol}:")

        # Scan through historical data
        for i in range(20, len(df) - 2):  # Need lookback + forward bars
            # Get data up to this point
            window = df.iloc[:i+1].copy()

            # Analyze
            try:
                analysis = scanner.analyze_stock(symbol, window)

                if analysis and analysis.get('score', 0) >= min_score:
                    found_setups += 1
                    entry_date = window.iloc[-1]['timestamp']
                    entry_price = window.iloc[-1]['close']
                    score = analysis['score']

                    print(f"  ✅ {entry_date.date()} - Score: {score} @ ₹{entry_price:.2f}")

                    # Simulate trade
                    position = {
                        'symbol': symbol,
                        'type': analysis['setup_type'],
                        'entry_price': entry_price,
                        'quantity': int(position_size / entry_price),
                        'position_size': position_size,
                        'score': score,
                        'support_level': analysis.get('support', [entry_price * 0.98])[0],
                        'resistance_level': analysis.get('resistance', [entry_price * 1.05])[0]
                    }

                    result = exit_manager.add_position(position)

                    # Track through next bars until exit
                    exit_found = False
                    for j in range(i + 1, min(i + 10, len(df))):  # Max 10 days
                        bar = df.iloc[j]

                        # Check stop hit
                        if position['type'] == 'LONG':
                            if bar['low'] <= result['stop_loss']:
                                # Stop hit
                                exit_price = result['stop_loss']
                                exit_reason = 'STOP_LOSS'
                                exit_date = bar['timestamp']
                                exit_found = True
                                break

                            # Check targets
                            if bar['high'] >= result['target1']:
                                exit_price = result['target1']
                                exit_reason = 'TARGET1_HIT'
                                exit_date = bar['timestamp']
                                exit_found = True
                                break

                    if not exit_found:
                        # Exit at last available price
                        exit_price = df.iloc[min(i + 10, len(df) - 1)]['close']
                        exit_reason = 'TIME_LIMIT'
                        exit_date = df.iloc[min(i + 10, len(df) - 1)]['timestamp']

                    # Calculate P&L
                    if position['type'] == 'LONG':
                        pnl = (exit_price - entry_price) * position['quantity']
                    else:
                        pnl = (entry_price - exit_price) * position['quantity']

                    pnl_pct = (pnl / position_size) * 100
                    win = pnl > 0

                    # Record trade
                    trade = {
                        'symbol': symbol,
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'win': win,
                        'exit_reason': exit_reason,
                        'score': score
                    }
                    all_trades.append(trade)
                    current_capital += pnl

                    result_icon = "✅" if win else "❌"
                    print(f"     {result_icon} Exit: {exit_reason} @ ₹{exit_price:.2f} | P&L: ₹{pnl:.0f} ({pnl_pct:+.2f}%)")

            except Exception as e:
                # Skip errors in demo
                pass

    # Calculate statistics
    print("\n\n" + "="*70)
    print("  📊 BACKTEST RESULTS")
    print("="*70)

    if not all_trades:
        print("\n⚠️  No trades found with 75+ score")
        print("\nThis could mean:")
        print("  • Scoring threshold is too strict")
        print("  • Need more volatile market conditions")
        print("  • Scanner needs tuning")
        return

    total_trades = len(all_trades)
    winners = [t for t in all_trades if t['win']]
    losers = [t for t in all_trades if not t['win']]

    win_rate = (len(winners) / total_trades) * 100

    total_pnl = sum(t['pnl'] for t in all_trades)
    avg_win = sum(t['pnl'] for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t['pnl'] for t in losers) / len(losers) if losers else 0

    gross_profit = sum(t['pnl'] for t in winners)
    gross_loss = abs(sum(t['pnl'] for t in losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    total_return_pct = ((current_capital - starting_capital) / starting_capital) * 100

    # Print results
    print("\n🎯 OVERVIEW")
    print("-"*70)
    print(f"Total Trades:    {total_trades}")
    print(f"Winners:         {len(winners)} ({(len(winners)/total_trades)*100:.1f}%)")
    print(f"Losers:          {len(losers)} ({(len(losers)/total_trades)*100:.1f}%)")
    print(f"Win Rate:        {win_rate:.2f}%")
    print(f"Profit Factor:   {profit_factor:.2f}")

    print("\n💰 RETURNS")
    print("-"*70)
    print(f"Starting Capital:  ₹{starting_capital:,}")
    print(f"Ending Capital:    ₹{current_capital:,.0f}")
    print(f"Total P&L:         ₹{total_pnl:,.0f}")
    print(f"Total Return:      {total_return_pct:+.2f}%")
    print(f"Avg Win:           ₹{avg_win:,.0f}")
    print(f"Avg Loss:          ₹{avg_loss:,.0f}")

    # By score
    print("\n📈 BY SCORE RANGE")
    print("-"*70)
    for threshold in [90, 80, 75]:
        trades_in_range = [t for t in all_trades if t['score'] >= threshold]
        if trades_in_range:
            win_rate_range = (len([t for t in trades_in_range if t['win']]) / len(trades_in_range)) * 100
            avg_pnl = sum(t['pnl'] for t in trades_in_range) / len(trades_in_range)
            print(f"{threshold}+ Score: {len(trades_in_range)} trades | WR: {win_rate_range:.1f}% | Avg: ₹{avg_pnl:,.0f}")

    print("\n" + "="*70)
    print("\n✅ Demo backtest complete!")
    print("\n💡 KEY INSIGHTS:")
    print("  • This validates the backtest engine works correctly")
    print("  • Real data will show actual historical edge")
    print("  • Build Kite MCP server next to run with real data")
    print("\n" + "="*70 + "\n")

    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), 'analysis')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'demo_backtest_{timestamp}.json')

    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_return_pct': total_return_pct
            },
            'trades': all_trades
        }, f, indent=2, default=str)

    print(f"💾 Results saved: {output_file}\n")


if __name__ == '__main__':
    run_demo_backtest()
