#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - HYBRID ORCHESTRATOR
Coordinates scanning, entry, exits, and learning in hybrid mode
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Import our modules
sys.path.insert(0, os.path.dirname(__file__))
from market_scanner import MarketScanner, TechnicalAnalyzer
from exit_manager import ExitManager


class TradingOrchestrator:
    """Main system orchestrator - coordinates all trading activities"""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.base_path = os.path.dirname(os.path.dirname(config_path))
        self.scanner = MarketScanner(config_path)
        self.exit_manager = ExitManager(config_path)
        self.analyzer = TechnicalAnalyzer(config_path)

        # State tracking
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        self.paused = False

        print("\n" + "="*70)
        print("  TRADING SYSTEM V3 - HYBRID MODE")
        print("  Real-Time Technical Structure Trading")
        print("="*70)
        print(f"\nMode: {'AUTO-EXECUTE' if self.config['auto_execute'] else 'MANUAL APPROVAL'}")
        print(f"Max Positions: {self.config['position_limits']['max_positions']}")
        print(f"Position Size: ₹{self.config['position_limits']['position_size']:,}")
        print(f"Min Score: {self.config['entry_rules']['minimum_score']}/100")
        print(f"Risk/Reward: {self.config['exit_rules']['risk_reward_minimum']}:1 minimum")
        print("="*70 + "\n")

    def check_trading_limits(self) -> bool:
        """Check if we can take new trades based on risk management rules"""

        # Check max daily trades
        if self.daily_trades >= self.config['position_limits']['max_daily_trades']:
            self.log_event('LIMIT_HIT', 'Max daily trades reached')
            return False

        # Check max open positions
        open_positions = len(self.exit_manager.get_open_positions())
        if open_positions >= self.config['position_limits']['max_positions']:
            self.log_event('LIMIT_HIT', 'Max open positions reached')
            return False

        # Check consecutive losses pause
        if self.consecutive_losses >= self.config['risk_management']['consecutive_losses_pause']:
            if not self.paused:
                self.paused = True
                self.log_event('PAUSE', f'Paused after {self.consecutive_losses} consecutive losses')
            return False

        # Check max daily loss
        max_loss_pct = self.config['risk_management']['max_daily_loss_percent'] / 100
        starting_capital = self.config['position_limits']['position_size'] * self.config['position_limits']['max_positions']
        max_loss_amount = starting_capital * max_loss_pct

        if self.daily_pnl < -max_loss_amount:
            self.log_event('LIMIT_HIT', f'Max daily loss reached: ₹{self.daily_pnl:.2f}')
            return False

        return True

    def evaluate_opportunity(self, opportunity: Dict) -> Dict:
        """Evaluate if opportunity meets all entry criteria"""

        evaluation = {
            'approved': False,
            'reasons': [],
            'action': None
        }

        # Check score threshold
        if opportunity['score'] < self.config['entry_rules']['minimum_score']:
            evaluation['reasons'].append(f"Score too low: {opportunity['score']}/100")
            return evaluation

        # Check setup type
        if opportunity['setup_type'] == 'SKIP':
            evaluation['reasons'].append("No clear setup identified")
            return evaluation

        # Check if already holding this stock
        open_symbols = [p['symbol'] for p in self.exit_manager.get_open_positions()]
        if opportunity['symbol'] in open_symbols:
            evaluation['reasons'].append("Already holding position")
            return evaluation

        # Check max trades per stock per day
        # (Would need to track this in production)

        # Check trading limits
        if not self.check_trading_limits():
            evaluation['reasons'].append("Trading limits reached")
            return evaluation

        # All checks passed
        evaluation['approved'] = True
        evaluation['action'] = 'ENTER' if self.config['auto_execute'] else 'ALERT'
        evaluation['reasons'].append("All entry criteria met")

        return evaluation

    def execute_entry(self, opportunity: Dict) -> Optional[Dict]:
        """Execute entry (or alert for approval in hybrid mode)"""

        evaluation = self.evaluate_opportunity(opportunity)

        if not evaluation['approved']:
            self.log_event('ENTRY_REJECTED', f"{opportunity['symbol']} - {', '.join(evaluation['reasons'])}")
            return None

        # In hybrid mode, generate alert for user approval
        if not self.config['auto_execute']:
            self.generate_entry_alert(opportunity)
            return None

        # Auto-execute mode (if enabled)
        position = self.prepare_position(opportunity)

        # In production, would execute via Kite API here
        # For now, just add to exit manager
        self.exit_manager.add_position(position)

        self.daily_trades += 1
        self.log_event('ENTRY_EXECUTED', f"{opportunity['symbol']} @ ₹{position['entry_price']:.2f}")

        return position

    def prepare_position(self, opportunity: Dict) -> Dict:
        """Prepare position details for entry"""

        position_size = self.config['position_limits']['position_size']
        entry_price = opportunity['current_price']

        # Calculate quantity
        quantity = int(position_size / entry_price)

        position = {
            'symbol': opportunity['symbol'],
            'type': opportunity['setup_type'],
            'entry_price': entry_price,
            'quantity': quantity,
            'position_size': position_size,
            'score': opportunity['score'],
            'setup_details': opportunity,
            'support_level': opportunity['sr_levels']['support'][0] if opportunity['sr_levels']['support'] else None,
            'resistance_level': opportunity['sr_levels']['resistance'][0] if opportunity['sr_levels']['resistance'] else None,
        }

        return position

    def generate_entry_alert(self, opportunity: Dict):
        """Generate alert for user approval"""

        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ENTRY_OPPORTUNITY',
            'symbol': opportunity['symbol'],
            'score': opportunity['score'],
            'setup_type': opportunity['setup_type'],
            'current_price': opportunity['current_price'],
            'entry_strategy': opportunity['entry_strategy'],
            'support': opportunity['sr_levels']['support'],
            'resistance': opportunity['sr_levels']['resistance'],
            'patterns': opportunity['patterns'],
            'trend': opportunity['trend'],
        }

        # Save alert
        alert_file = os.path.join(self.base_path, 'alerts', 'pending_entries.json')

        if os.path.exists(alert_file):
            with open(alert_file, 'r') as f:
                alerts = json.load(f)
        else:
            alerts = []

        alerts.append(alert)

        with open(alert_file, 'w') as f:
            json.dump(alerts, f, indent=2)

        # Display notification
        self.display_notification(alert)

        self.log_event('ALERT_GENERATED', f"{opportunity['symbol']} - Score: {opportunity['score']}/100")

    def display_notification(self, alert: Dict):
        """Display desktop notification (console for now)"""

        print("\n" + "🔔 " + "="*65)
        print(f"  ENTRY OPPORTUNITY - {alert['symbol']}")
        print("="*68)
        print(f"  Score: {alert['score']}/100 ⭐")
        print(f"  Setup: {alert['setup_type']}")
        print(f"  Price: ₹{alert['current_price']:.2f}")
        print(f"  Strategy: {alert['entry_strategy']}")
        print(f"  Trend: {alert['trend']['direction']} ({alert['trend']['strength']})")
        if alert['patterns']:
            print(f"  Patterns: {', '.join(alert['patterns'])}")
        print("-"*68)
        print(f"  Support: {[f'₹{s:.2f}' for s in alert['support'][:2]]}")
        print(f"  Resistance: {[f'₹{r:.2f}' for r in alert['resistance'][:2]]}")
        print("="*68)
        print("  Review in: /trading-system-v3/alerts/pending_entries.json")
        print("="*68 + "\n")

    def monitor_positions(self):
        """Monitor and update all open positions"""

        positions = self.exit_manager.get_open_positions()

        if not positions:
            return

        print(f"\n[MONITOR] Checking {len(positions)} open positions...")

        for position in positions:
            symbol = position['symbol']

            # Fetch current data (in production, would use Kite API)
            # For now, simulate with last known data
            current_data = {
                'current_price': position.get('current_price', position['entry_price']),
                'trend': position.get('setup_details', {}).get('trend', {})
            }

            # Update position
            updated = self.exit_manager.update_position_price(
                symbol,
                current_data['current_price'],
                current_data
            )

            if updated:
                # Check if should exit
                exit_reason = self.exit_manager.should_exit_position(symbol)

                if exit_reason:
                    self.execute_exit(symbol, updated['current_price'], exit_reason)

    def execute_exit(self, symbol: str, exit_price: float, exit_reason: str):
        """Execute exit for a position"""

        closed_trade = self.exit_manager.close_position(symbol, exit_price, exit_reason)

        if closed_trade:
            self.daily_pnl += closed_trade['final_pnl_amount']

            # Update consecutive losses
            if closed_trade['winner']:
                self.consecutive_losses = 0
                self.paused = False
            else:
                self.consecutive_losses += 1

            # Log exit
            status = "✅ WIN" if closed_trade['winner'] else "❌ LOSS"
            print(f"\n[EXIT] {status} - {symbol} @ ₹{exit_price:.2f}")
            print(f"       Reason: {exit_reason}")
            print(f"       P&L: {closed_trade['final_pnl_percent']:.2f}% (₹{closed_trade['final_pnl_amount']:.2f})")

            self.log_event('EXIT_EXECUTED', {
                'symbol': symbol,
                'reason': exit_reason,
                'pnl': closed_trade['final_pnl_amount'],
                'winner': closed_trade['winner']
            })

    def log_event(self, event_type: str, details):
        """Log system event"""

        timestamp = datetime.now().strftime('%Y%m%d')
        journal_file = os.path.join(self.base_path, 'journals', f'journal_{timestamp}.jsonl')

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'system_event',
            'event': event_type,
            'details': details
        }

        with open(journal_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def run_trading_cycle(self):
        """Run one complete trading cycle"""

        # 1. Monitor existing positions
        self.monitor_positions()

        # 2. Scan for new opportunities (if limits allow)
        if self.check_trading_limits():
            opportunities = self.scanner.scan_market()

            if opportunities:
                print(f"\n[OPPORTUNITIES] Found {len(opportunities)} potential setups")

                # Process top opportunities
                for opp in opportunities[:3]:  # Top 3
                    self.execute_entry(opp)
        else:
            print(f"\n[PAUSED] Trading limits reached or risk management pause active")

        # 3. Display current status
        self.display_status()

    def display_status(self):
        """Display current system status"""

        summary = self.exit_manager.get_position_summary()

        print(f"\n{'='*70}")
        print(f"STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Open Positions: {summary['total_positions']}/{self.config['position_limits']['max_positions']}")
        print(f"Daily Trades: {self.daily_trades}/{self.config['position_limits']['max_daily_trades']}")
        print(f"Daily P&L: ₹{self.daily_pnl:.2f}")
        print(f"Consecutive Losses: {self.consecutive_losses}")
        print(f"Status: {'🟢 ACTIVE' if not self.paused else '🔴 PAUSED'}")
        print(f"{'='*70}\n")

    def run_continuous(self):
        """Run system continuously"""

        scan_interval = self.config['scanning']['scan_interval_minutes'] * 60

        print(f"[START] System running in {'AUTO' if self.config['auto_execute'] else 'HYBRID'} mode")
        print(f"[CONFIG] Scan interval: {self.config['scanning']['scan_interval_minutes']} minutes\n")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                self.run_trading_cycle()

                print(f"\n[WAIT] Next cycle in {self.config['scanning']['scan_interval_minutes']} minutes...")
                print("-"*70 + "\n")

                time.sleep(scan_interval)

        except KeyboardInterrupt:
            print("\n\n[STOP] System stopped by user")
            self.display_status()
            print("="*70 + "\n")


def main():
    """Main entry point"""

    config_path = "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3/config/trading_rules.json"

    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    orchestrator = TradingOrchestrator(config_path)
    orchestrator.run_continuous()


if __name__ == "__main__":
    main()
