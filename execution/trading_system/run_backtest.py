#!/usr/bin/env python3
"""
BACKTEST RUNNER - Uses Real Kite Historical Data
Validates trading system edge before live trading
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from backtester import Backtester


def fetch_historical_data_for_symbol(symbol: str, days: int = 90) -> pd.DataFrame:
    """
    Fetch real historical data from Kite MCP

    This function is called BY THE USER (Claude in Cowork mode)
    who has access to Kite MCP tools

    The user should call: mcp__kite__get_stock_bars and pass results here

    Args:
        symbol: Stock symbol
        days: Days of history

    Returns:
        DataFrame with OHLCV data
    """

    print(f"\n📊 To fetch data for {symbol}, please run:")
    print(f"    mcp__kite__get_stock_bars(")
    print(f"        symbol='{symbol}',")
    print(f"        days={days},")
    print(f"        timeframe='1Day'")
    print(f"    )")
    print("\n    Then pass the result to: convert_kite_response_to_df(response)")

    return None


def convert_kite_response_to_df(response_text: str, symbol: str) -> pd.DataFrame:
    """
    Convert Kite MCP response to DataFrame

    Args:
        response_text: String response from Kite MCP tool
        symbol: Stock symbol

    Returns:
        Clean DataFrame ready for backtesting
    """

    # Parse the Kite response
    # Expected format from get_stock_bars:
    #
    # Symbol: RELIANCE
    # Timeframe: 1Day
    #
    # Timestamp           | Open    | High    | Low     | Close   | Volume
    # 2024-11-05 09:15:00 | 1234.50 | 1245.00 | 1230.00 | 1240.00 | 1234567
    # ...

    lines = response_text.strip().split('\n')

    # Find the data section (after the header line with |)
    data_start = 0
    for i, line in enumerate(lines):
        if '|' in line and 'Timestamp' in line:
            data_start = i + 1
            break

    # Parse data rows
    data = []
    for line in lines[data_start:]:
        if '|' not in line or line.strip() == '':
            continue

        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 6:
            try:
                data.append({
                    'timestamp': pd.to_datetime(parts[0]),
                    'open': float(parts[1]),
                    'high': float(parts[2]),
                    'low': float(parts[3]),
                    'close': float(parts[4]),
                    'volume': int(float(parts[5]))
                })
            except (ValueError, IndexError):
                continue

    if not data:
        print(f"⚠️  No data parsed for {symbol}")
        return None

    df = pd.DataFrame(data)
    df = df.set_index('timestamp').sort_index()

    print(f"✅ Parsed {len(df)} bars for {symbol}")
    print(f"   Period: {df.index[0].date()} to {df.index[-1].date()}")

    return df


def prepare_backtest_data(symbols: List[str], days: int = 90) -> Dict[str, pd.DataFrame]:
    """
    Prepare all historical data for backtesting

    Args:
        symbols: List of symbols to fetch
        days: Days of history

    Returns:
        Dict mapping symbol to DataFrame
    """

    print("\n" + "="*70)
    print("  📦 PREPARING BACKTEST DATA")
    print("="*70)
    print(f"\nSymbols to fetch: {len(symbols)}")
    print(f"Historical period: {days} days")
    print("\n" + "-"*70)

    print("\n⚠️  MANUAL DATA FETCH REQUIRED")
    print("-"*70)
    print("\nTo run this backtest, you (Claude in Cowork mode) need to:")
    print("\n1. For each symbol below, call mcp__kite__get_stock_bars")
    print("2. Store the DataFrames in a dict")
    print("3. Pass to backtester.run_backtest_with_data()")
    print("\nSymbols to fetch:")
    for sym in symbols:
        print(f"  • {sym}")

    print("\n" + "="*70)

    # This function serves as a guide
    # The actual implementation requires MCP tool calls in Cowork mode

    return {}


if __name__ == '__main__':
    """
    Backtest runner - requires Kite MCP data fetch first
    """

    print("\n" + "="*70)
    print("  🧪 BACKTEST SETUP")
    print("="*70)

    # Watchlist symbols
    SYMBOLS = [
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

    DAYS = 90  # 3 months of data

    print(f"\nThis backtest will validate the trading system using:")
    print(f"  • {len(SYMBOLS)} symbols")
    print(f"  • {DAYS} days of historical data")
    print(f"  • Same scanner logic (0-100 scoring)")
    print(f"  • Same exit management (stops, targets, trailing)")
    print(f"  • Entry threshold: 75+ score")
    print(f"  • Position size: ₹20,000")
    print("\n" + "="*70)

    # Guide user on next steps
    print("\n\n📋 NEXT STEPS:")
    print("-"*70)
    print("\n1. I (Claude) need to fetch historical data using Kite MCP tools")
    print("2. For each symbol, call: mcp__kite__get_stock_bars(symbol, days=90)")
    print("3. Convert responses to DataFrames")
    print("4. Run backtester.run_backtest_with_data(data_dict)")
    print("5. Analyze results to validate edge")
    print("\n" + "="*70)

    print("\n💡 TIP: This validates whether the 75+ scoring actually produces")
    print("   a positive edge before risking real capital!")
    print("\n" + "="*70 + "\n")

    # Return the symbols list for easy access
    print("SYMBOLS TO FETCH:")
    print(json.dumps(SYMBOLS, indent=2))
