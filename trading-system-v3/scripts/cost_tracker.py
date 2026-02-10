#!/usr/bin/env python3
"""
COST TRACKER - Real-time trading cost monitoring
Tracks all Zerodha charges and ensures profitability after costs
"""

import json
from datetime import datetime
from typing import Dict, List


class CostTracker:
    """
    Track all trading costs in real-time
    Based on actual Zerodha charge structure
    """

    # Zerodha charges (as of your trading data)
    DP_CHARGE_PER_SELL = 15.34  # Per delivery sell transaction
    AUTO_SQUAREOFF_MIS = 59      # MIS auto square-off
    AUTO_SQUAREOFF_NRML = 118    # NRML/CNC auto square-off
    PLEDGE_CHARGE = 35.40        # Per pledge/unpledge
    BROKERAGE_INTRADAY_MAX = 20  # Max ₹20 per trade or 0.03% of turnover

    def __init__(self, journal_path: str = '../journals/cost_tracking.json'):
        self.journal_path = journal_path
        self.session_costs = {
            'dp_charges': 0.0,
            'brokerage': 0.0,
            'auto_squareoff': 0.0,
            'pledge_charges': 0.0,
            'other': 0.0,
            'total': 0.0
        }
        self.trade_count = 0
        self.transactions = []

        # Load existing journal if available
        try:
            with open(journal_path, 'r') as f:
                data = json.load(f)
                self.session_costs = data.get('session_costs', self.session_costs)
                self.trade_count = data.get('trade_count', 0)
                self.transactions = data.get('transactions', [])
        except FileNotFoundError:
            pass

    def calculate_trade_cost(self,
                            trade_type: str,
                            product_type: str,
                            value: float,
                            quantity: int,
                            is_auto_squareoff: bool = False) -> Dict:
        """
        Calculate costs for a trade

        Args:
            trade_type: 'buy' or 'sell'
            product_type: 'CNC' (delivery), 'MIS' (intraday), 'NRML' (F&O)
            value: Trade value (price × quantity)
            quantity: Number of shares
            is_auto_squareoff: Whether this was forced auto square-off

        Returns:
            Dict with cost breakdown
        """

        costs = {
            'brokerage': 0.0,
            'dp_charge': 0.0,
            'auto_squareoff': 0.0,
            'total': 0.0
        }

        # DP charges - ONLY on delivery sells
        if trade_type == 'sell' and product_type == 'CNC':
            costs['dp_charge'] = self.DP_CHARGE_PER_SELL

        # Brokerage - ONLY on intraday (MIS)
        # Zerodha: ₹0 for delivery, ₹20 or 0.03% for intraday
        if product_type == 'MIS':
            brokerage = min(20, value * 0.0003)  # ₹20 or 0.03%, whichever is lower
            costs['brokerage'] = round(brokerage, 2)

        # Auto square-off penalty
        if is_auto_squareoff:
            if product_type == 'MIS':
                costs['auto_squareoff'] = self.AUTO_SQUAREOFF_MIS
            else:
                costs['auto_squareoff'] = self.AUTO_SQUAREOFF_NRML

        costs['total'] = sum(costs.values())

        return costs

    def log_trade(self,
                  symbol: str,
                  trade_type: str,
                  product_type: str,
                  quantity: int,
                  price: float,
                  is_auto_squareoff: bool = False,
                  timestamp: datetime = None) -> Dict:
        """
        Log a trade and calculate its costs

        Returns:
            Cost breakdown for this trade
        """

        if timestamp is None:
            timestamp = datetime.now()

        value = quantity * price
        costs = self.calculate_trade_cost(
            trade_type=trade_type,
            product_type=product_type,
            value=value,
            quantity=quantity,
            is_auto_squareoff=is_auto_squareoff
        )

        # Update session totals
        self.session_costs['dp_charges'] += costs['dp_charge']
        self.session_costs['brokerage'] += costs['brokerage']
        self.session_costs['auto_squareoff'] += costs['auto_squareoff']
        self.session_costs['total'] = sum([
            self.session_costs['dp_charges'],
            self.session_costs['brokerage'],
            self.session_costs['auto_squareoff'],
            self.session_costs['pledge_charges'],
            self.session_costs['other']
        ])
        self.trade_count += 1

        # Record transaction
        transaction = {
            'timestamp': timestamp.isoformat(),
            'symbol': symbol,
            'type': trade_type,
            'product': product_type,
            'quantity': quantity,
            'price': price,
            'value': value,
            'costs': costs,
            'auto_squareoff': is_auto_squareoff
        }
        self.transactions.append(transaction)

        # Save to journal
        self._save_journal()

        return costs

    def log_pledge(self, value: float):
        """Log pledge charges"""
        self.session_costs['pledge_charges'] += self.PLEDGE_CHARGE
        self.session_costs['total'] += self.PLEDGE_CHARGE
        self._save_journal()

    def estimate_roundtrip_cost(self,
                                position_size: float,
                                product_type: str = 'CNC') -> float:
        """
        Estimate total cost for a complete round-trip (buy + sell)

        Args:
            position_size: Position value in rupees
            product_type: 'CNC' or 'MIS'

        Returns:
            Estimated total cost
        """

        # Buy costs
        buy_cost = 0
        if product_type == 'MIS':
            buy_cost = min(20, position_size * 0.0003)

        # Sell costs
        sell_cost = 0
        if product_type == 'MIS':
            sell_cost = min(20, position_size * 0.0003)
        else:  # CNC
            sell_cost = self.DP_CHARGE_PER_SELL

        total = buy_cost + sell_cost

        return round(total, 2)

    def minimum_profit_needed(self,
                             position_size: float,
                             product_type: str = 'CNC') -> Dict:
        """
        Calculate minimum profit needed to break even after costs

        Returns:
            Dict with absolute amount and percentage
        """

        cost = self.estimate_roundtrip_cost(position_size, product_type)

        return {
            'cost_amount': cost,
            'breakeven_amount': cost,
            'breakeven_percent': (cost / position_size) * 100
        }

    def should_trade_considering_costs(self,
                                      expected_profit: float,
                                      position_size: float,
                                      product_type: str = 'CNC') -> Dict:
        """
        Evaluate if a trade is worth taking considering costs

        Args:
            expected_profit: Expected profit in rupees
            position_size: Position size in rupees
            product_type: Product type

        Returns:
            Dict with recommendation and analysis
        """

        costs = self.estimate_roundtrip_cost(position_size, product_type)
        net_profit = expected_profit - costs
        profit_after_costs_pct = (net_profit / position_size) * 100

        recommendation = {
            'should_trade': net_profit > 0,
            'expected_gross_profit': expected_profit,
            'estimated_costs': costs,
            'expected_net_profit': net_profit,
            'profit_after_costs_pct': profit_after_costs_pct,
            'reason': ''
        }

        if net_profit <= 0:
            recommendation['reason'] = f"Expected profit (₹{expected_profit:.2f}) does not cover costs (₹{costs:.2f})"
        elif net_profit < 10:
            recommendation['should_trade'] = False
            recommendation['reason'] = f"Net profit too small (₹{net_profit:.2f}) - not worth the risk"
        else:
            recommendation['reason'] = f"Viable trade: ₹{net_profit:.2f} net profit after ₹{costs:.2f} costs"

        return recommendation

    def get_cost_summary(self) -> Dict:
        """Get comprehensive cost summary"""

        avg_cost_per_trade = (self.session_costs['total'] / self.trade_count) if self.trade_count > 0 else 0

        return {
            'session_costs': self.session_costs,
            'trade_count': self.trade_count,
            'avg_cost_per_trade': round(avg_cost_per_trade, 2),
            'breakdown_pct': {
                'dp_charges': (self.session_costs['dp_charges'] / self.session_costs['total'] * 100) if self.session_costs['total'] > 0 else 0,
                'brokerage': (self.session_costs['brokerage'] / self.session_costs['total'] * 100) if self.session_costs['total'] > 0 else 0,
                'auto_squareoff': (self.session_costs['auto_squareoff'] / self.session_costs['total'] * 100) if self.session_costs['total'] > 0 else 0,
            }
        }

    def print_summary(self):
        """Print formatted cost summary"""

        summary = self.get_cost_summary()

        print("\n" + "="*60)
        print("💸 COST TRACKING SUMMARY")
        print("="*60)
        print(f"\nTotal Trades: {self.trade_count}")
        print(f"Total Costs: ₹{self.session_costs['total']:.2f}")
        print(f"Avg Cost/Trade: ₹{summary['avg_cost_per_trade']:.2f}")

        print("\n" + "-"*60)
        print("COST BREAKDOWN:")
        print("-"*60)
        print(f"DP Charges:       ₹{self.session_costs['dp_charges']:.2f} ({summary['breakdown_pct']['dp_charges']:.1f}%)")
        print(f"Brokerage:        ₹{self.session_costs['brokerage']:.2f} ({summary['breakdown_pct']['brokerage']:.1f}%)")
        print(f"Auto Square-off:  ₹{self.session_costs['auto_squareoff']:.2f} ({summary['breakdown_pct']['auto_squareoff']:.1f}%)")
        print(f"Pledge Charges:   ₹{self.session_costs['pledge_charges']:.2f}")
        print(f"Other:            ₹{self.session_costs['other']:.2f}")

        print("\n" + "="*60)

        # Warnings
        if self.session_costs['auto_squareoff'] > 0:
            print("\n⚠️  AUTO SQUARE-OFF CHARGES DETECTED!")
            print("   Action: Implement 3:15 PM position closer")
            print("   Potential savings: ₹" + str(self.session_costs['auto_squareoff']))

        if self.session_costs['dp_charges'] > self.session_costs['brokerage'] * 2:
            print("\n⚠️  DP CHARGES DOMINATING!")
            print("   Action: Use single exit strategy, avoid partial exits")
            print("   Current DP charges: ₹" + str(self.session_costs['dp_charges']))

    def _save_journal(self):
        """Save cost tracking data to journal"""

        data = {
            'last_updated': datetime.now().isoformat(),
            'session_costs': self.session_costs,
            'trade_count': self.trade_count,
            'transactions': self.transactions
        }

        import os
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)

        with open(self.journal_path, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == '__main__':
    """
    Demo usage and testing
    """

    print("\n" + "="*60)
    print("COST TRACKER - Demo & Testing")
    print("="*60)

    tracker = CostTracker('../journals/cost_tracking_demo.json')

    # Example: Delivery round-trip (₹20k position)
    print("\n📊 Example 1: Delivery Round-trip (₹20,000 position)")
    print("-"*60)

    # Buy
    buy_cost = tracker.log_trade(
        symbol='RELIANCE',
        trade_type='buy',
        product_type='CNC',
        quantity=14,
        price=1428.57
    )
    print(f"Buy costs: ₹{buy_cost['total']:.2f}")

    # Sell
    sell_cost = tracker.log_trade(
        symbol='RELIANCE',
        trade_type='sell',
        product_type='CNC',
        quantity=14,
        price=1450.00
    )
    print(f"Sell costs: ₹{sell_cost['total']:.2f} (includes DP charge)")

    roundtrip_cost = buy_cost['total'] + sell_cost['total']
    print(f"\nTotal round-trip cost: ₹{roundtrip_cost:.2f}")
    print(f"Break-even needed: {(roundtrip_cost / 20000 * 100):.3f}%")

    # Example: Intraday trade
    print("\n\n📊 Example 2: Intraday Trade (₹20,000 position)")
    print("-"*60)

    intraday_cost = tracker.estimate_roundtrip_cost(20000, 'MIS')
    print(f"Estimated intraday round-trip cost: ₹{intraday_cost:.2f}")

    # Example: Minimum profit analysis
    print("\n\n📊 Example 3: Minimum Profit Analysis")
    print("-"*60)

    breakeven = tracker.minimum_profit_needed(20000, 'CNC')
    print(f"Minimum profit needed: ₹{breakeven['breakeven_amount']:.2f}")
    print(f"As percentage: {breakeven['breakeven_percent']:.3f}%")

    # Example: Should we take this trade?
    print("\n\n📊 Example 4: Trade Viability Check")
    print("-"*60)

    # Good trade: 1% expected profit (₹200)
    good_trade = tracker.should_trade_considering_costs(
        expected_profit=200,
        position_size=20000,
        product_type='CNC'
    )
    print(f"\nTrade 1: Expected ₹200 profit on ₹20k position")
    print(f"Recommendation: {'✅ TAKE' if good_trade['should_trade'] else '❌ SKIP'}")
    print(f"Net profit after costs: ₹{good_trade['expected_net_profit']:.2f}")
    print(f"Reason: {good_trade['reason']}")

    # Bad trade: ₹10 expected profit
    bad_trade = tracker.should_trade_considering_costs(
        expected_profit=10,
        position_size=20000,
        product_type='CNC'
    )
    print(f"\nTrade 2: Expected ₹10 profit on ₹20k position")
    print(f"Recommendation: {'✅ TAKE' if bad_trade['should_trade'] else '❌ SKIP'}")
    print(f"Net profit after costs: ₹{bad_trade['expected_net_profit']:.2f}")
    print(f"Reason: {bad_trade['reason']}")

    # Print summary
    tracker.print_summary()

    print("\n✅ Demo complete! Check '../journals/cost_tracking_demo.json' for saved data\n")
