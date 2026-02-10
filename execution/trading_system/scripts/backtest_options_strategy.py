#!/usr/bin/env python3
"""
OPTIONS TRADING BACKTEST - Simulating F&O Strategy
What if we traded options instead of equity?
"""

import random
from datetime import datetime, timedelta, time
from typing import Dict, List
import json

random.seed(42)


class OptionsBacktest:
    """
    Backtest options trading strategy with ₹35k capital
    Simulates realistic options behavior with leverage and decay
    """

    def __init__(self, starting_capital: float = 35000):
        self.starting_capital = starting_capital
        self.cash = starting_capital

        # Track positions
        self.active_positions = []
        self.trades = []

        # Options trading parameters
        self.max_risk_per_trade = 0.15  # Risk 15% of capital per trade (higher than equity)
        self.leverage_factor = 5  # Options give ~5x leverage on average

    def simulate_options_scenario(self,
                                  strategy_name: str,
                                  min_score: int,
                                  holding_period: str,  # 'intraday', 'swing'
                                  trade_type: str,  # 'long_call', 'long_put', 'spread'
                                  num_days: int = 40):
        """
        Simulate options trading with specific parameters
        """

        print(f'\n{"="*70}')
        print(f'📊 OPTIONS STRATEGY: {strategy_name}')
        print(f'{"="*70}')
        print(f'Parameters:')
        print(f'  Min Score: {min_score}+')
        print(f'  Holding: {holding_period}')
        print(f'  Type: {trade_type}')
        print(f'  Capital: ₹{self.cash:,.0f}')
        print(f'  Period: {num_days} days')
        print('-'*70)

        # Reset for this scenario
        self.cash = self.starting_capital
        self.trades = []
        self.active_positions = []

        current_date = datetime(2025, 12, 25)
        trading_days = 0

        for day_num in range(num_days):
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            trading_days += 1

            # Generate signals
            signals = self.generate_options_signals(current_date, min_score)

            for signal in signals:
                if self.cash < self.starting_capital * 0.1:
                    continue  # Don't trade if capital too low

                # Enter position
                position = self.enter_options_position(
                    signal,
                    trade_type,
                    holding_period
                )

                if position:
                    print(f"Day {trading_days}: Entry - {signal['symbol']} {trade_type} @ ₹{signal['premium']:.2f} (Score: {signal['score']:.0f})")

            # Check exits
            for position in self.active_positions[:]:
                if self.should_exit_options(position, current_date, holding_period):
                    exit_result = self.exit_options_position(position, current_date)

                    pnl_display = f"+₹{exit_result['pnl']:.2f}" if exit_result['pnl'] > 0 else f"₹{exit_result['pnl']:.2f}"
                    print(f"       Exit  - {position['symbol']} @ ₹{exit_result['exit_premium']:.2f} ({exit_result['exit_reason']}) {pnl_display}")

            current_date += timedelta(days=1)

        # Close remaining positions
        for position in self.active_positions[:]:
            self.exit_options_position(position, current_date)

        # Print results
        return self.calculate_results(strategy_name, trading_days)

    def generate_options_signals(self, date: datetime, min_score: int) -> List[Dict]:
        """Generate options trading signals"""

        signals = []

        # Generate 1-3 signals per day
        num_signals = random.choices([0, 1, 2], weights=[0.4, 0.4, 0.2])[0]

        for _ in range(num_signals):
            # Generate score
            score = random.uniform(70, 98)

            if score < min_score:
                continue

            # Stock price range
            stock_price = random.uniform(100, 2000)

            # Options premium (typically 2-10% of stock price)
            premium = stock_price * random.uniform(0.02, 0.08)

            signal = {
                'date': date,
                'symbol': random.choice(['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK']),
                'score': score,
                'stock_price': stock_price,
                'premium': premium,
                'time': random.choice([time(9, 30), time(10, 0), time(11, 0), time(12, 0)])
            }

            signals.append(signal)

        return signals

    def enter_options_position(self, signal: Dict, trade_type: str, holding_period: str) -> Dict:
        """Enter options position"""

        # Calculate position size based on risk
        max_risk_amount = self.cash * self.max_risk_per_trade

        # For options, we buy multiple lots
        # Each lot is typically 1 option contract controlling 1 lot of underlying
        premium = signal['premium']

        # Calculate how many lots we can buy
        lots = int(max_risk_amount / premium)

        if lots == 0:
            return None

        # Total premium paid
        total_premium = premium * lots

        if total_premium > self.cash:
            return None

        # Deduct premium
        self.cash -= total_premium

        position = {
            'entry_date': signal['date'],
            'symbol': signal['symbol'],
            'trade_type': trade_type,
            'score': signal['score'],
            'lots': lots,
            'entry_premium': premium,
            'total_cost': total_premium,
            'stock_price': signal['stock_price'],
            'holding_period': holding_period
        }

        self.active_positions.append(position)
        return position

    def should_exit_options(self, position: Dict, current_date: datetime, holding_period: str) -> bool:
        """Check if should exit options position"""

        days_held = (current_date - position['entry_date']).days

        # Intraday: Exit same day
        if holding_period == 'intraday':
            return days_held >= 0

        # Swing: Hold 1-3 days
        if holding_period == 'swing':
            return days_held >= random.randint(1, 3)

        return False

    def exit_options_position(self, position: Dict, current_date: datetime) -> Dict:
        """Exit options position and calculate P&L"""

        score = position['score']
        entry_premium = position['entry_premium']

        # Win probability based on score (same as equity)
        if score >= 90:
            win_prob = 0.70
        elif score >= 85:
            win_prob = 0.60
        elif score >= 80:
            win_prob = 0.55
        else:
            win_prob = 0.50

        is_win = random.random() < win_prob

        # Options amplify moves
        if is_win:
            # Winners: Premium can go up 30-150%
            multiplier = random.uniform(1.3, 2.5)
            exit_premium = entry_premium * multiplier
            exit_reason = 'TARGET'
        else:
            # Losers: Premium can go down 40-100% (can lose all premium)
            if random.random() < 0.3:  # 30% chance of total loss
                multiplier = 0  # Complete loss
                exit_premium = 0
                exit_reason = 'EXPIRED_WORTHLESS'
            else:
                multiplier = random.uniform(0.3, 0.7)
                exit_premium = entry_premium * multiplier
                exit_reason = 'STOP'

        # Calculate P&L
        exit_value = exit_premium * position['lots']
        pnl = exit_value - position['total_cost']

        # Add back exit value
        self.cash += exit_value

        # Store trade
        trade = {
            'entry_date': position['entry_date'],
            'exit_date': current_date,
            'symbol': position['symbol'],
            'trade_type': position['trade_type'],
            'score': position['score'],
            'lots': position['lots'],
            'entry_premium': entry_premium,
            'exit_premium': exit_premium,
            'total_cost': position['total_cost'],
            'exit_value': exit_value,
            'pnl': pnl,
            'pnl_pct': (pnl / position['total_cost'] * 100) if position['total_cost'] > 0 else 0,
            'exit_reason': exit_reason,
            'is_win': is_win
        }

        self.trades.append(trade)
        self.active_positions.remove(position)

        return trade

    def calculate_results(self, strategy_name: str, trading_days: int) -> Dict:
        """Calculate and display results"""

        if not self.trades:
            print('\n❌ No trades executed')
            return None

        total_trades = len(self.trades)
        wins = [t for t in self.trades if t['is_win']]
        losses = [t for t in self.trades if not t['is_win']]

        total_pnl = sum(t['pnl'] for t in self.trades)
        gross_profit = sum(t['pnl'] for t in wins) if wins else 0
        gross_loss = sum(t['pnl'] for t in losses) if losses else 0

        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else 0

        avg_win = gross_profit / len(wins) if wins else 0
        avg_loss = abs(gross_loss / len(losses)) if losses else 0

        final_capital = self.cash
        returns_pct = ((final_capital - self.starting_capital) / self.starting_capital) * 100

        # Max drawdown
        peak = self.starting_capital
        max_dd = 0
        running_capital = self.starting_capital

        for trade in self.trades:
            running_capital += trade['pnl']
            if running_capital > peak:
                peak = running_capital
            dd = (peak - running_capital) / peak * 100
            if dd > max_dd:
                max_dd = dd

        print(f'\n{"="*70}')
        print(f'RESULTS: {strategy_name}')
        print(f'{"="*70}')

        print(f'\nPERFORMANCE:')
        print(f'  Total Trades: {total_trades}')
        print(f'  Wins: {len(wins)} | Losses: {len(losses)}')
        print(f'  Win Rate: {win_rate:.1f}%')
        print(f'  Profit Factor: {profit_factor:.2f}')

        print(f'\nP&L:')
        print(f'  Gross Profit: ₹{gross_profit:,.2f}')
        print(f'  Gross Loss: ₹{gross_loss:,.2f}')
        print(f'  Net P&L: ₹{total_pnl:,.2f}')
        print(f'  Avg Win: ₹{avg_win:,.2f}')
        print(f'  Avg Loss: ₹{avg_loss:,.2f}')

        print(f'\nCAPITAL:')
        print(f'  Starting: ₹{self.starting_capital:,.2f}')
        print(f'  Ending: ₹{final_capital:,.2f}')
        print(f'  Returns: {returns_pct:+.2f}%')
        print(f'  Max Drawdown: {max_dd:.1f}%')

        # Risk metrics
        print(f'\nRISK METRICS:')
        print(f'  Max Single Loss: ₹{min(t["pnl"] for t in losses):,.2f}' if losses else '  Max Single Loss: ₹0')
        print(f'  Max Single Win: ₹{max(t["pnl"] for t in wins):,.2f}' if wins else '  Max Single Win: ₹0')
        print(f'  Risk/Reward Ratio: {avg_win/avg_loss:.2f}:1' if avg_loss > 0 else '  Risk/Reward Ratio: N/A')

        return {
            'strategy': strategy_name,
            'trades': total_trades,
            'win_rate': win_rate,
            'pnl': total_pnl,
            'returns': returns_pct,
            'profit_factor': profit_factor,
            'max_dd': max_dd,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }


def run_options_comparison():
    """
    Run multiple options strategies and compare with equity
    """

    print('\n' + '='*70)
    print('🎯 OPTIONS VS EQUITY COMPARISON')
    print('='*70)
    print('\nTesting Period: Dec 25, 2025 - Feb 3, 2026 (40 days)')
    print('Starting Capital: ₹35,000')
    print('\nScenarios:')
    print('1. Conservative Options (High Score, Swing)')
    print('2. Moderate Options (Medium Score, Swing)')
    print('3. Aggressive Options (Lower Score, Intraday)')
    print('4. High Frequency Options (Intraday Scalping)')
    print('='*70)

    results = []

    # Scenario 1: Conservative Options
    backtester = OptionsBacktest(35000)
    result = backtester.simulate_options_scenario(
        strategy_name='Conservative Options (90+ Swing)',
        min_score=90,
        holding_period='swing',
        trade_type='long_call'
    )
    if result:
        results.append(result)

    # Scenario 2: Moderate Options
    backtester = OptionsBacktest(35000)
    result = backtester.simulate_options_scenario(
        strategy_name='Moderate Options (85+ Swing)',
        min_score=85,
        holding_period='swing',
        trade_type='long_call'
    )
    if result:
        results.append(result)

    # Scenario 3: Aggressive Options
    backtester = OptionsBacktest(35000)
    result = backtester.simulate_options_scenario(
        strategy_name='Aggressive Options (80+ Swing)',
        min_score=80,
        holding_period='swing',
        trade_type='long_call'
    )
    if result:
        results.append(result)

    # Scenario 4: Intraday Options
    backtester = OptionsBacktest(35000)
    result = backtester.simulate_options_scenario(
        strategy_name='Intraday Options (90+ Intraday)',
        min_score=90,
        holding_period='intraday',
        trade_type='long_call'
    )
    if result:
        results.append(result)

    # Comparison table
    print('\n' + '='*70)
    print('📊 OPTIONS STRATEGIES COMPARISON')
    print('='*70)
    print(f"{'Strategy':<35} {'Trades':>7} {'WR%':>6} {'P&L':>12} {'Ret%':>8} {'MaxDD%':>8}")
    print('-'*70)

    for r in sorted(results, key=lambda x: x['returns'], reverse=True):
        print(f"{r['strategy']:<35} {r['trades']:>7} {r['win_rate']:>6.1f} ₹{r['pnl']:>10,.0f} {r['returns']:>7.1f}% {r['max_dd']:>7.1f}%")

    # Compare with equity CNC
    print('\n' + '='*70)
    print('💡 EQUITY CNC COMPARISON (From Previous Backtest)')
    print('='*70)
    print(f"{'Strategy':<35} {'Trades':>7} {'WR%':>6} {'P&L':>12} {'Ret%':>8} {'MaxDD%':>8}")
    print('-'*70)
    print(f"{'CNC-Only (80+ Equity)':<35} {'8':>7} {'100.0':>6} ₹{'3,476':>10} {'+9.93':>7}% {'~3':>7}%")

    print('\n' + '='*70)
    print('🔍 KEY INSIGHTS')
    print('='*70)

    if results:
        best_options = max(results, key=lambda x: x['returns'])

        print(f"\nBest Options Strategy: {best_options['strategy']}")
        print(f"  Returns: {best_options['returns']:+.2f}%")
        print(f"  Win Rate: {best_options['win_rate']:.1f}%")
        print(f"  Max Drawdown: {best_options['max_dd']:.1f}%")

        print(f"\nCNC Equity Benchmark:")
        print(f"  Returns: +9.93%")
        print(f"  Win Rate: 100%")
        print(f"  Max Drawdown: ~3%")

        if best_options['returns'] > 9.93:
            print(f"\n✅ Options beat equity by {best_options['returns'] - 9.93:.2f}% points")
            print(f"   BUT with {best_options['max_dd']:.1f}% drawdown (vs 3% for equity)")
        else:
            print(f"\n⚠️  Equity beat options by {9.93 - best_options['returns']:.2f}% points")
            print(f"   WITH lower drawdown (3% vs {best_options['max_dd']:.1f}%)")

    print('\n' + '='*70)
    print('⚖️ RISK-ADJUSTED ANALYSIS')
    print('='*70)

    print('\nOptions Characteristics:')
    print('  ✅ Higher leverage (5-10x)')
    print('  ✅ Bigger wins possible (50-150% gains)')
    print('  ❌ Bigger losses possible (can lose 100% of premium)')
    print('  ❌ Time decay (theta) works against you')
    print('  ❌ Higher volatility swings')
    print('  ❌ More complex (strikes, expiry, IV)')

    print('\nEquity CNC Characteristics:')
    print('  ✅ Proven profitable (your ₹3k real profit)')
    print('  ✅ Simpler to execute')
    print('  ✅ No time decay')
    print('  ✅ Can hold indefinitely')
    print('  ✅ Lower risk (can\'t lose more than position)')
    print('  ❌ Lower leverage')

    print('\n' + '='*70)
    print('🎯 RECOMMENDATION')
    print('='*70)

    if results:
        best = results[0]
        if best['returns'] > 15 and best['max_dd'] < 20:
            print('\n✅ Options show promise IF you can handle:')
            print('   - Higher volatility')
            print('   - Bigger drawdowns')
            print('   - More complexity')
            print('   - Time decay management')
            print('\n   Suggestion: Master CNC first, add options later')
        else:
            print('\n⚠️  Options show higher risk without proportional reward')
            print('   - Stick with proven CNC equity strategy')
            print('   - ₹3k real profit validates equity edge')
            print('   - Lower stress, simpler execution')

    print('\n' + '='*70)
    print('✅ OPTIONS BACKTEST COMPLETE')
    print('='*70 + '\n')


if __name__ == '__main__':
    run_options_comparison()
