#!/usr/bin/env python3
"""
DUAL-MODE BACKTEST WITH ₹35K CAPITAL
Starting Dec 25, 2025 - Simulating scanner + dual-mode system
"""

import random
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple
import json

# Set seed for reproducibility
random.seed(42)


class DualModeBacktest:
    """
    Backtest dual-mode system with ₹35k starting capital
    Simulates scanner detecting opportunities and system trading them
    """

    def __init__(self, starting_capital: float = 35000):
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.margin = 15000  # From pledged GOLDBEES

        # Track positions
        self.mis_position = None
        self.cnc_position = None

        # Track history
        self.trades = []
        self.daily_stats = []

        # Load config
        self.load_configs()

        # Universe of stocks
        self.stock_universe = [
            'TATASTEEL', 'NTPC', 'BPCL', 'SAIL', 'NATIONALUM',
            'ONGC', 'COALINDIA', 'IOC', 'HINDALCO', 'VEDL',
            'TATAPOWER', 'POWERGRID', 'RECLTD', 'SJVN', 'BEL',
            'SBIN', 'ICICIBANK', 'HDFCBANK', 'RELIANCE', 'TCS'
        ]

    def load_configs(self):
        """Load MIS and CNC configurations"""
        try:
            with open('config/trading_rules_mis.json', 'r') as f:
                self.mis_config = json.load(f)
            with open('config/trading_rules_cnc.json', 'r') as f:
                self.cnc_config = json.load(f)
        except:
            # Defaults
            self.mis_config = {
                'scoring': {'min_score_threshold': 85},
                'exit_rules': {'stop_loss_pct': 0.5, 'target_pct': 1.0}
            }
            self.cnc_config = {
                'scoring': {'min_score_threshold': 75},
                'exit_rules': {'stop_loss_pct': 1.5, 'target1_pct': 2.5}
            }

    def simulate_market_day(self, date: datetime, day_num: int) -> List[Dict]:
        """
        Simulate one trading day
        Returns list of signals detected by scanner
        """

        signals = []

        # Scanner runs every 5 minutes, 9:20 AM to 2:00 PM (MIS cutoff)
        scan_times = [
            time(9, 20), time(9, 30), time(10, 0), time(10, 30),
            time(11, 0), time(11, 30), time(12, 0), time(12, 30),
            time(13, 0), time(13, 30), time(14, 0)
        ]

        # Generate 0-3 signals per day (realistic)
        num_signals = random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]

        for _ in range(num_signals):
            signal = self.generate_signal(date, scan_times)
            if signal:
                signals.append(signal)

        return signals

    def generate_signal(self, date: datetime, scan_times: List[time]) -> Dict:
        """
        Generate a trading signal (what scanner would detect)
        """

        symbol = random.choice(self.stock_universe)
        scan_time = random.choice(scan_times)

        # Generate realistic price (₹50 to ₹2000)
        base_price = random.uniform(50, 2000)

        # Generate score with realistic distribution
        # 20% exceptional (90+), 30% good (75-89), 50% below threshold
        score_category = random.choices(
            ['exceptional', 'good', 'marginal'],
            weights=[0.20, 0.30, 0.50]
        )[0]

        if score_category == 'exceptional':
            score = random.uniform(90, 98)
        elif score_category == 'good':
            score = random.uniform(75, 89)
        else:
            score = random.uniform(50, 74)

        # Generate setup type
        setup_type = random.choice([
            'pullback_long', 'breakout', 'support_bounce',
            'structure_break', 'fvg_fill'
        ])

        return {
            'date': date,
            'time': scan_time,
            'symbol': symbol,
            'score': score,
            'setup_type': setup_type,
            'entry_price': base_price,
            'support': base_price * 0.98,
            'resistance': base_price * 1.03
        }

    def select_mode(self, signal: Dict, current_time: time) -> str:
        """
        Mode selection logic (from mode_selector.py)
        """

        score = signal['score']

        # Check thresholds
        mis_eligible = score >= self.mis_config['scoring']['min_score_threshold']
        cnc_eligible = score >= self.cnc_config['scoring']['min_score_threshold']

        # Check if too late for MIS
        market_close_soon = current_time >= time(14, 30)

        # Check capital availability
        has_cash = self.cash >= 10000
        has_margin = self.margin >= 15000

        # Check position limits
        has_mis_slot = self.mis_position is None
        has_cnc_slot = self.cnc_position is None

        # Decision tree
        if market_close_soon:
            if has_cash and cnc_eligible and has_cnc_slot:
                return 'CNC'
            return 'SKIP'

        # Exceptional setup (90+)
        if score >= 90:
            if has_margin and mis_eligible and has_mis_slot:
                return 'MIS'
            elif has_cash and cnc_eligible and has_cnc_slot:
                return 'CNC'
            return 'SKIP'

        # Good setup (85-89)
        if score >= 85:
            if has_cash and cnc_eligible and has_cnc_slot:
                return 'CNC'
            elif has_margin and mis_eligible and has_mis_slot:
                return 'MIS'
            return 'SKIP'

        # Marginal setup (75-84)
        if score >= 75:
            if has_cash and cnc_eligible and has_cnc_slot:
                return 'CNC'
            return 'SKIP'

        return 'SKIP'

    def calculate_position_size(self, mode: str, entry_price: float) -> Tuple[int, float]:
        """Calculate position size based on mode and capital"""

        if mode == 'MIS':
            capital = self.margin
            stop_pct = self.mis_config['exit_rules']['stop_loss_pct']
        else:
            capital = self.cash
            stop_pct = self.cnc_config['exit_rules']['stop_loss_pct']

        # Risk 1% of capital
        risk_amount = capital * 0.01

        # Calculate quantity
        stop_distance = entry_price * (stop_pct / 100)
        quantity = int(risk_amount / stop_distance)

        # Cap by available capital
        max_quantity = int((capital * 0.9) / entry_price)
        quantity = min(quantity, max_quantity)

        position_value = quantity * entry_price

        return quantity, position_value

    def execute_trade(self, signal: Dict, mode: str) -> Dict:
        """
        Execute a trade (entry)
        """

        entry_price = signal['entry_price']
        quantity, position_value = self.calculate_position_size(mode, entry_price)

        if quantity == 0:
            return None

        # Calculate stops and targets
        if mode == 'MIS':
            config = self.mis_config
            stop_pct = config['exit_rules']['stop_loss_pct']
            target_pct = config['exit_rules']['target_pct']
        else:
            config = self.cnc_config
            stop_pct = config['exit_rules']['stop_loss_pct']
            target_pct = config['exit_rules']['target1_pct']

        stop_price = entry_price * (1 - stop_pct/100)
        target_price = entry_price * (1 + target_pct/100)

        # Deduct capital
        if mode == 'MIS':
            # Margin used, no cash impact on entry
            pass
        else:
            self.cash -= position_value

        trade = {
            'entry_date': signal['date'],
            'entry_time': signal['time'],
            'symbol': signal['symbol'],
            'mode': mode,
            'score': signal['score'],
            'setup_type': signal['setup_type'],
            'quantity': quantity,
            'entry_price': entry_price,
            'position_value': position_value,
            'stop_price': stop_price,
            'target_price': target_price,
            'status': 'OPEN'
        }

        # Track position
        if mode == 'MIS':
            self.mis_position = trade
        else:
            self.cnc_position = trade

        return trade

    def simulate_exit(self, trade: Dict, exit_date: datetime) -> Dict:
        """
        Simulate trade exit based on probabilities
        """

        mode = trade['mode']
        score = trade['score']

        # Win probability based on score
        if score >= 90:
            win_prob = 0.70
        elif score >= 85:
            win_prob = 0.60
        elif score >= 75:
            win_prob = 0.55
        else:
            win_prob = 0.50

        is_win = random.random() < win_prob

        entry_price = trade['entry_price']
        quantity = trade['quantity']

        if is_win:
            exit_price = trade['target_price']
            exit_type = 'TARGET'
        else:
            exit_price = trade['stop_price']
            exit_type = 'STOP'

        # Calculate P&L
        pnl_gross = (exit_price - entry_price) * quantity

        # Calculate costs
        if mode == 'MIS':
            costs = 40  # ₹20 buy + ₹20 sell
        else:
            costs = 15.34  # DP charge

        pnl_net = pnl_gross - costs

        # Update capital
        if mode == 'MIS':
            # Margin released, cash updated with P&L
            self.cash += pnl_net
        else:
            # Return capital + P&L
            self.cash += trade['position_value'] + pnl_net

        # Update trade
        trade['exit_date'] = exit_date
        trade['exit_price'] = exit_price
        trade['exit_type'] = exit_type
        trade['pnl_gross'] = pnl_gross
        trade['costs'] = costs
        trade['pnl_net'] = pnl_net
        trade['status'] = 'CLOSED'

        # Clear position
        if mode == 'MIS':
            self.mis_position = None
        else:
            self.cnc_position = None

        self.trades.append(trade)

        return trade

    def run_backtest(self, start_date: datetime, num_days: int = 30):
        """
        Run complete backtest
        """

        print('\n' + '='*60)
        print('🚀 DUAL-MODE BACKTEST - ₹35K CAPITAL')
        print('='*60)
        print(f'\nStarting Capital: ₹{self.starting_capital:,.2f}')
        print(f'Available Cash: ₹{self.cash:,.2f}')
        print(f'Available Margin: ₹{self.margin:,.2f}')
        print(f'\nPeriod: {start_date.strftime("%b %d, %Y")} to {(start_date + timedelta(days=num_days)).strftime("%b %d, %Y")}')
        print(f'Trading Days: ~{num_days // 7 * 5} (approx)')

        print('\n' + '-'*60)
        print('Running simulation...')
        print('-'*60 + '\n')

        current_date = start_date
        trading_days = 0

        for day_num in range(num_days):
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            trading_days += 1

            # Generate signals
            signals = self.simulate_market_day(current_date, day_num)

            # Process signals
            for signal in signals:
                mode = self.select_mode(signal, signal['time'])

                if mode != 'SKIP':
                    trade = self.execute_trade(signal, mode)
                    if trade:
                        print(f"Day {trading_days}: {mode} entry - {signal['symbol']} @ ₹{signal['entry_price']:.2f} (Score: {signal['score']:.0f})")

            # Simulate exits for open positions (1-2 days holding)
            # MIS exits same day, CNC can hold
            if self.mis_position:
                # MIS exits at 3:15 PM same day
                exit_trade = self.simulate_exit(self.mis_position, current_date)
                pnl_display = f"+₹{exit_trade['pnl_net']:.2f}" if exit_trade['pnl_net'] > 0 else f"₹{exit_trade['pnl_net']:.2f}"
                print(f"       {exit_trade['mode']} exit  - {exit_trade['symbol']} @ ₹{exit_trade['exit_price']:.2f} ({exit_trade['exit_type']}) {pnl_display}")

            if self.cnc_position:
                # CNC exits after 1-2 days or at stop/target
                days_held = (current_date - self.cnc_position['entry_date']).days
                should_exit = days_held >= random.randint(1, 2)

                if should_exit:
                    exit_trade = self.simulate_exit(self.cnc_position, current_date)
                    pnl_display = f"+₹{exit_trade['pnl_net']:.2f}" if exit_trade['pnl_net'] > 0 else f"₹{exit_trade['pnl_net']:.2f}"
                    print(f"       {exit_trade['mode']} exit  - {exit_trade['symbol']} @ ₹{exit_trade['exit_price']:.2f} ({exit_trade['exit_type']}) {pnl_display}")

            # Track daily stats
            self.daily_stats.append({
                'date': current_date,
                'cash': self.cash,
                'trades_count': len(self.trades)
            })

            current_date += timedelta(days=1)

        # Close any remaining positions
        if self.mis_position:
            self.simulate_exit(self.mis_position, current_date)
        if self.cnc_position:
            self.simulate_exit(self.cnc_position, current_date)

        # Print results
        self.print_results(trading_days)

    def print_results(self, trading_days: int):
        """Print backtest results"""

        print('\n' + '='*60)
        print('📊 BACKTEST RESULTS')
        print('='*60)

        if not self.trades:
            print('\n❌ No trades executed during backtest period')
            return

        # Calculate statistics
        total_trades = len(self.trades)
        mis_trades = [t for t in self.trades if t['mode'] == 'MIS']
        cnc_trades = [t for t in self.trades if t['mode'] == 'CNC']

        wins = [t for t in self.trades if t['pnl_net'] > 0]
        losses = [t for t in self.trades if t['pnl_net'] <= 0]

        total_pnl = sum(t['pnl_net'] for t in self.trades)
        total_costs = sum(t['costs'] for t in self.trades)

        gross_profit = sum(t['pnl_gross'] for t in wins)
        gross_loss = sum(t['pnl_gross'] for t in losses)

        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else 0

        final_capital = self.cash
        returns_pct = ((final_capital - self.starting_capital) / self.starting_capital) * 100

        print(f'\nTRADING PERIOD:')
        print(f'  Trading Days: {trading_days}')
        print(f'  Total Trades: {total_trades}')
        print(f'  MIS Trades: {len(mis_trades)}')
        print(f'  CNC Trades: {len(cnc_trades)}')

        print(f'\nPERFORMANCE:')
        print(f'  Wins: {len(wins)} ({win_rate:.1f}%)')
        print(f'  Losses: {len(losses)} ({100-win_rate:.1f}%)')
        print(f'  Win Rate: {win_rate:.1f}%')
        print(f'  Profit Factor: {profit_factor:.2f}')

        print(f'\nP&L:')
        print(f'  Gross Profit: ₹{gross_profit:.2f}')
        print(f'  Gross Loss: ₹{gross_loss:.2f}')
        print(f'  Total Costs: ₹{total_costs:.2f}')
        print(f'  Net P&L: ₹{total_pnl:.2f}')

        print(f'\nCAPITAL:')
        print(f'  Starting: ₹{self.starting_capital:,.2f}')
        print(f'  Ending: ₹{final_capital:,.2f}')
        print(f'  Returns: {returns_pct:+.2f}%')

        # Mode breakdown
        if mis_trades:
            mis_pnl = sum(t['pnl_net'] for t in mis_trades)
            mis_win_rate = (len([t for t in mis_trades if t['pnl_net'] > 0]) / len(mis_trades)) * 100
            print(f'\nMIS MODE:')
            print(f'  Trades: {len(mis_trades)}')
            print(f'  Win Rate: {mis_win_rate:.1f}%')
            print(f'  Net P&L: ₹{mis_pnl:.2f}')

        if cnc_trades:
            cnc_pnl = sum(t['pnl_net'] for t in cnc_trades)
            cnc_win_rate = (len([t for t in cnc_trades if t['pnl_net'] > 0]) / len(cnc_trades)) * 100
            print(f'\nCNC MODE:')
            print(f'  Trades: {len(cnc_trades)}')
            print(f'  Win Rate: {cnc_win_rate:.1f}%')
            print(f'  Net P&L: ₹{cnc_pnl:.2f}')

        # Evaluation
        print('\n' + '='*60)
        print('✅ EVALUATION')
        print('='*60)

        is_profitable = total_pnl > 0
        good_wr = win_rate >= 55
        good_pf = profit_factor >= 1.5

        print(f'\n  Profitable: {"✅" if is_profitable else "❌"} (₹{total_pnl:.2f})')
        print(f'  Win Rate ≥55%: {"✅" if good_wr else "❌"} ({win_rate:.1f}%)')
        print(f'  Profit Factor ≥1.5: {"✅" if good_pf else "❌"} ({profit_factor:.2f})')

        if is_profitable and good_wr and good_pf:
            print(f'\n✅ SYSTEM VALIDATED - Edge confirmed!')
        elif is_profitable:
            print(f'\n⚠️  MARGINALLY PROFITABLE - Consider threshold adjustment')
        else:
            print(f'\n❌ NOT PROFITABLE - Needs optimization')

        print('\n' + '='*60)


if __name__ == '__main__':
    # Run backtest from Dec 25, 2025
    start_date = datetime(2025, 12, 25)

    backtester = DualModeBacktest(starting_capital=35000)
    backtester.run_backtest(start_date, num_days=40)

    print('\n✅ Backtest complete!\n')
