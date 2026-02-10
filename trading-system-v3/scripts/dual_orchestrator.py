#!/usr/bin/env python3
"""
DUAL ORCHESTRATOR - Manages both MIS and CNC trading modes
Coordinates mode selection, position management, and automated exits
Prevents manual intervention through strict automation
"""

import json
from datetime import datetime, time
from typing import Dict, List, Optional
from pathlib import Path

from mode_selector import ModeSelector
from cost_tracker import CostTracker
from trade_logger import TradeLogger


class DualOrchestrator:
    """
    Orchestrates trading across both MIS (intraday) and CNC (delivery) modes
    Ensures strict adherence to mode-specific rules with zero manual intervention
    """

    def __init__(self,
                 config_path: str = '../config/trading_rules.json',
                 journals_path: str = '../journals'):
        """Initialize dual mode orchestrator"""

        self.config_path = Path(config_path)
        self.journals_path = Path(journals_path)
        self.journals_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.load_config()

        # Initialize components
        self.mode_selector = ModeSelector(config_path)
        self.cost_tracker = CostTracker(str(self.journals_path / 'cost_tracking.json'))
        self.trade_logger = TradeLogger(str(self.journals_path))

        # Track active positions
        self.active_positions = {
            'MIS': [],
            'CNC': []
        }

        # Session state
        self.session_stats = {
            'trades_today': 0,
            'mis_trades': 0,
            'cnc_trades': 0,
            'daily_pnl': 0.0,
            'mis_pnl': 0.0,
            'cnc_pnl': 0.0,
            'skipped_signals': 0,
            'manual_intervention_attempts': 0
        }

    def load_config(self):
        """Load trading configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config not found, using defaults")
            self.config = self._default_config()

        # Extract key limits
        self.max_mis_trades_daily = self.config.get('daily_limits', {}).get('max_mis_trades', 2)
        self.max_cnc_trades_daily = self.config.get('daily_limits', {}).get('max_cnc_trades', 3)
        self.max_daily_loss = self.config.get('risk_management', {}).get('max_drawdown_daily', 1000)

    def _default_config(self) -> Dict:
        """Default configuration if file not found"""
        return {
            'daily_limits': {
                'max_mis_trades': 2,
                'max_cnc_trades': 3,
                'max_total_trades': 4
            },
            'risk_management': {
                'max_drawdown_daily': 1000,
                'max_position_loss': 300
            },
            'position_limits': {
                'max_positions': 2,
                'mis_max_positions': 1,
                'cnc_max_positions': 1
            }
        }

    def process_signal(self,
                      symbol: str,
                      signal_score: float,
                      setup_type: str,
                      analysis_data: Dict,
                      chart_data: Dict,
                      current_price: float,
                      support: float,
                      resistance: float) -> Dict:
        """
        Process a trading signal through the dual-mode system

        Args:
            symbol: Stock symbol
            signal_score: Scanner score (0-100)
            setup_type: Type of setup
            analysis_data: Complete scanner analysis
            chart_data: OHLCV data
            current_price: Current price
            support: Support level
            resistance: Resistance level

        Returns:
            Dict with decision and execution details
        """

        timestamp = datetime.now()

        print(f"\n{'='*60}")
        print(f"🔍 PROCESSING SIGNAL: {symbol}")
        print(f"{'='*60}")
        print(f"Score: {signal_score}/100")
        print(f"Setup: {setup_type}")
        print(f"Price: ₹{current_price:.2f}")
        print(f"Support: ₹{support:.2f} | Resistance: ₹{resistance:.2f}")

        # Step 1: Check daily limits
        if not self._check_daily_limits():
            return {
                'action': 'SKIP',
                'reason': 'Daily limits reached',
                'details': self.session_stats
            }

        # Step 2: Get available capital
        capital_status = self._get_capital_status()
        print(f"\nCapital Status:")
        print(f"  Cash: ₹{capital_status['cash']:.2f}")
        print(f"  Margin: ₹{capital_status['margin']:.2f}")

        # Step 3: Mode selection
        mode_decision = self.mode_selector.select_mode(
            signal_score=signal_score,
            current_time=timestamp.time(),
            available_cash=capital_status['cash'],
            available_margin=capital_status['margin'],
            symbol=symbol,
            setup_type=setup_type
        )

        print(f"\n📊 Mode Decision: {mode_decision['mode']}")
        print(f"Reason: {mode_decision['reason']}")
        print(f"Confidence: {mode_decision['confidence']}%")

        if mode_decision['mode'] == 'SKIP':
            self.session_stats['skipped_signals'] += 1
            return {
                'action': 'SKIP',
                'reason': mode_decision['reason'],
                'mode_decision': mode_decision
            }

        # Step 4: Check position limits for chosen mode
        mode = mode_decision['mode']
        if not self._check_mode_position_limit(mode):
            return {
                'action': 'SKIP',
                'reason': f'{mode} position limit reached',
                'mode_decision': mode_decision
            }

        # Step 5: Get mode-specific rules
        mode_rules = self.mode_selector.get_mode_rules(mode)

        # Step 6: Calculate position size
        position_params = self._calculate_position_size(
            mode=mode,
            capital=capital_status['cash'] if mode == 'CNC' else capital_status['margin'],
            current_price=current_price,
            stop_loss_pct=mode_rules['stop_loss_pct']
        )

        # Step 7: Calculate stops and targets
        levels = self._calculate_trade_levels(
            mode=mode,
            mode_rules=mode_rules,
            current_price=current_price,
            support=support,
            resistance=resistance
        )

        # Step 8: Cost viability check
        expected_profit = (levels['target1'] - current_price) * position_params['quantity']
        cost_analysis = self.cost_tracker.should_trade_considering_costs(
            expected_profit=expected_profit,
            position_size=position_params['value'],
            product_type=mode_rules['product_type']
        )

        print(f"\n💰 Cost Analysis:")
        print(f"  Expected Profit: ₹{expected_profit:.2f}")
        print(f"  Estimated Costs: ₹{cost_analysis['estimated_costs']:.2f}")
        print(f"  Net Profit: ₹{cost_analysis['expected_net_profit']:.2f}")
        print(f"  Viable: {'✅' if cost_analysis['should_trade'] else '❌'}")

        if not cost_analysis['should_trade']:
            return {
                'action': 'SKIP',
                'reason': cost_analysis['reason'],
                'cost_analysis': cost_analysis
            }

        # Step 9: Log analysis
        analysis_id = self.trade_logger.log_analysis(
            symbol=symbol,
            analysis_data=analysis_data,
            chart_data=chart_data,
            scanner_timestamp=timestamp
        )

        # Step 10: Prepare trade alert
        trade_alert = {
            'action': 'ALERT_FOR_APPROVAL',
            'timestamp': timestamp.isoformat(),
            'symbol': symbol,
            'mode': mode,
            'score': signal_score,
            'setup_type': setup_type,
            'entry_price': current_price,
            'quantity': position_params['quantity'],
            'position_size': position_params['value'],
            'stop_loss': levels['stop_loss'],
            'target1': levels['target1'],
            'target2': levels.get('target2'),
            'risk_per_trade': position_params['risk_amount'],
            'expected_profit': expected_profit,
            'net_profit_after_costs': cost_analysis['expected_net_profit'],
            'mode_rules': mode_rules,
            'mode_decision': mode_decision,
            'cost_analysis': cost_analysis,
            'analysis_id': analysis_id,
            'auto_execute': False  # Requires approval
        }

        print(f"\n{'='*60}")
        print(f"✅ TRADE ALERT GENERATED")
        print(f"{'='*60}")
        print(f"Mode: {mode}")
        print(f"Position: {position_params['quantity']} shares @ ₹{current_price:.2f}")
        print(f"Value: ₹{position_params['value']:.2f}")
        print(f"Stop: ₹{levels['stop_loss']:.2f} (-{mode_rules['stop_loss_pct']}%)")
        print(f"Target: ₹{levels['target1']:.2f} (+{mode_rules.get('target_pct', mode_rules.get('target1_pct'))}%)")
        print(f"Risk: ₹{position_params['risk_amount']:.2f}")
        print(f"Reward: ₹{expected_profit:.2f} (net: ₹{cost_analysis['expected_net_profit']:.2f})")
        print(f"\n⏳ AWAITING APPROVAL...")

        return trade_alert

    def execute_trade(self, trade_alert: Dict, approved: bool = False) -> Dict:
        """
        Execute approved trade

        Args:
            trade_alert: Trade alert from process_signal
            approved: User approval status

        Returns:
            Execution result
        """

        if not approved:
            return {
                'status': 'REJECTED',
                'reason': 'User did not approve trade'
            }

        mode = trade_alert['mode']
        symbol = trade_alert['symbol']

        # Log entry
        trade_id = self.trade_logger.log_entry(
            symbol=symbol,
            entry_price=trade_alert['entry_price'],
            quantity=trade_alert['quantity'],
            position_size=trade_alert['position_size'],
            stop_loss=trade_alert['stop_loss'],
            target1=trade_alert['target1'],
            target2=trade_alert.get('target2'),
            setup_type=trade_alert['setup_type'],
            score=trade_alert['score'],
            product_type=trade_alert['mode_rules']['product_type'],
            analysis_id=trade_alert['analysis_id'],
            timing_analysis={
                'analysis_timestamp': datetime.fromisoformat(trade_alert['timestamp']),
                'entry_timestamp': datetime.now(),
                'delay_minutes': (datetime.now() - datetime.fromisoformat(trade_alert['timestamp'])).seconds / 60
            }
        )

        # Log costs
        self.cost_tracker.log_trade(
            symbol=symbol,
            trade_type='buy',
            product_type=trade_alert['mode_rules']['product_type'],
            quantity=trade_alert['quantity'],
            price=trade_alert['entry_price']
        )

        # Track position
        position = {
            'trade_id': trade_id,
            'symbol': symbol,
            'mode': mode,
            'quantity': trade_alert['quantity'],
            'entry_price': trade_alert['entry_price'],
            'entry_time': datetime.now(),
            'stop_loss': trade_alert['stop_loss'],
            'target1': trade_alert['target1'],
            'target2': trade_alert.get('target2'),
            'mode_rules': trade_alert['mode_rules'],
            'status': 'OPEN'
        }

        self.active_positions[mode].append(position)

        # Update stats
        self.session_stats['trades_today'] += 1
        if mode == 'MIS':
            self.session_stats['mis_trades'] += 1
        else:
            self.session_stats['cnc_trades'] += 1

        print(f"\n{'='*60}")
        print(f"✅ TRADE EXECUTED: {symbol}")
        print(f"{'='*60}")
        print(f"Trade ID: {trade_id}")
        print(f"Mode: {mode}")
        print(f"Position: {position['quantity']} @ ₹{position['entry_price']:.2f}")
        print(f"Status: MONITORING")

        return {
            'status': 'EXECUTED',
            'trade_id': trade_id,
            'position': position,
            'message': f'{mode} position opened for {symbol}'
        }

    def monitor_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Monitor all active positions and generate exit signals

        Args:
            current_prices: Dict of {symbol: price}

        Returns:
            List of exit actions required
        """

        current_time = datetime.now().time()
        exit_actions = []

        # Check MIS positions
        for position in self.active_positions['MIS']:
            if position['status'] != 'OPEN':
                continue

            symbol = position['symbol']
            current_price = current_prices.get(symbol)

            if current_price is None:
                continue

            # Force close at 3:15 PM (no exceptions!)
            if current_time >= time(15, 15):
                exit_actions.append({
                    'position': position,
                    'exit_type': 'FORCE_CLOSE',
                    'exit_price': current_price,
                    'reason': 'MIS auto-close at 3:15 PM',
                    'priority': 'CRITICAL'
                })
                continue

            # Check stop loss
            if current_price <= position['stop_loss']:
                exit_actions.append({
                    'position': position,
                    'exit_type': 'STOP_LOSS',
                    'exit_price': current_price,
                    'reason': 'Stop loss hit',
                    'priority': 'HIGH'
                })
                continue

            # Check target
            if current_price >= position['target1']:
                exit_actions.append({
                    'position': position,
                    'exit_type': 'TARGET',
                    'exit_price': current_price,
                    'reason': 'Target 1 reached',
                    'priority': 'NORMAL'
                })

        # Check CNC positions
        for position in self.active_positions['CNC']:
            if position['status'] != 'OPEN':
                continue

            symbol = position['symbol']
            current_price = current_prices.get(symbol)

            if current_price is None:
                continue

            # Check stop loss
            if current_price <= position['stop_loss']:
                exit_actions.append({
                    'position': position,
                    'exit_type': 'STOP_LOSS',
                    'exit_price': current_price,
                    'reason': 'Stop loss hit',
                    'priority': 'HIGH'
                })
                continue

            # Check targets
            if current_price >= position['target1']:
                exit_actions.append({
                    'position': position,
                    'exit_type': 'TARGET1',
                    'exit_price': current_price,
                    'reason': 'Target 1 reached',
                    'priority': 'NORMAL'
                })

            elif position.get('target2') and current_price >= position['target2']:
                exit_actions.append({
                    'position': position,
                    'exit_type': 'TARGET2',
                    'exit_price': current_price,
                    'reason': 'Target 2 reached',
                    'priority': 'NORMAL'
                })

        return exit_actions

    def execute_exit(self, exit_action: Dict) -> Dict:
        """
        Execute position exit

        Args:
            exit_action: Exit action from monitor_positions

        Returns:
            Exit result
        """

        position = exit_action['position']
        exit_price = exit_action['exit_price']
        exit_type = exit_action['exit_type']

        # Calculate P&L
        pnl = (exit_price - position['entry_price']) * position['quantity']

        # Log costs
        is_auto_squareoff = (exit_type == 'FORCE_CLOSE' and
                            exit_action.get('priority') == 'CRITICAL')

        self.cost_tracker.log_trade(
            symbol=position['symbol'],
            trade_type='sell',
            product_type=position['mode_rules']['product_type'],
            quantity=position['quantity'],
            price=exit_price,
            is_auto_squareoff=is_auto_squareoff
        )

        # Log exit
        self.trade_logger.log_exit(
            trade_id=position['trade_id'],
            exit_price=exit_price,
            exit_reason=exit_action['reason'],
            exit_type=exit_type
        )

        # Update position status
        position['status'] = 'CLOSED'
        position['exit_price'] = exit_price
        position['exit_time'] = datetime.now()
        position['pnl'] = pnl

        # Update stats
        self.session_stats['daily_pnl'] += pnl
        if position['mode'] == 'MIS':
            self.session_stats['mis_pnl'] += pnl
        else:
            self.session_stats['cnc_pnl'] += pnl

        print(f"\n{'='*60}")
        print(f"🔒 POSITION CLOSED: {position['symbol']}")
        print(f"{'='*60}")
        print(f"Mode: {position['mode']}")
        print(f"Exit Type: {exit_type}")
        print(f"Entry: ₹{position['entry_price']:.2f} → Exit: ₹{exit_price:.2f}")
        print(f"P&L: ₹{pnl:.2f} ({'✅ PROFIT' if pnl > 0 else '❌ LOSS'})")

        return {
            'status': 'CLOSED',
            'position': position,
            'pnl': pnl,
            'exit_type': exit_type
        }

    def _check_daily_limits(self) -> bool:
        """Check if daily trading limits reached"""
        if self.session_stats['trades_today'] >= self.max_mis_trades_daily + self.max_cnc_trades_daily:
            return False
        if abs(self.session_stats['daily_pnl']) >= self.max_daily_loss:
            return False
        return True

    def _check_mode_position_limit(self, mode: str) -> bool:
        """Check if mode-specific position limit reached"""
        active_count = len([p for p in self.active_positions[mode] if p['status'] == 'OPEN'])
        return active_count < 1  # One position at a time per mode

    def _get_capital_status(self) -> Dict:
        """Get current capital availability (mock for now)"""
        # TODO: Connect to actual Kite account balance
        return {
            'cash': 10000,  # Mock: ₹10k cash
            'margin': 15000  # Mock: ₹15k margin from GOLDBEES
        }

    def _calculate_position_size(self, mode: str, capital: float,
                                 current_price: float, stop_loss_pct: float) -> Dict:
        """Calculate position size based on capital and risk"""

        # Risk 1% of capital per trade
        risk_amount = capital * 0.01

        # Calculate quantity based on stop loss
        stop_distance = current_price * (stop_loss_pct / 100)
        quantity = int(risk_amount / stop_distance)

        # Ensure we don't exceed capital
        max_quantity = int((capital * 0.9) / current_price)  # Use 90% of capital
        quantity = min(quantity, max_quantity)

        position_value = quantity * current_price

        return {
            'quantity': quantity,
            'value': position_value,
            'risk_amount': risk_amount
        }

    def _calculate_trade_levels(self, mode: str, mode_rules: Dict,
                                current_price: float, support: float,
                                resistance: float) -> Dict:
        """Calculate stop loss and target levels"""

        levels = {}

        # Stop loss
        stop_pct = mode_rules['stop_loss_pct']
        levels['stop_loss'] = current_price * (1 - stop_pct/100)

        # Targets
        if mode == 'MIS':
            target_pct = mode_rules['target_pct']
            levels['target1'] = current_price * (1 + target_pct/100)

        else:  # CNC
            target1_pct = mode_rules['target1_pct']
            target2_pct = mode_rules['target2_pct']
            levels['target1'] = current_price * (1 + target1_pct/100)
            levels['target2'] = current_price * (1 + target2_pct/100)

        return levels

    def get_session_summary(self) -> Dict:
        """Get session statistics summary"""
        return {
            'session_stats': self.session_stats,
            'active_positions': {
                'MIS': len([p for p in self.active_positions['MIS'] if p['status'] == 'OPEN']),
                'CNC': len([p for p in self.active_positions['CNC'] if p['status'] == 'OPEN'])
            },
            'costs': self.cost_tracker.get_cost_summary(),
            'mode_selection': self.mode_selector.get_decision_stats()
        }

    def print_session_summary(self):
        """Print formatted session summary"""
        summary = self.get_session_summary()

        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)

        print(f"\nTrades Today: {summary['session_stats']['trades_today']}")
        print(f"  MIS: {summary['session_stats']['mis_trades']}")
        print(f"  CNC: {summary['session_stats']['cnc_trades']}")
        print(f"  Skipped: {summary['session_stats']['skipped_signals']}")

        print(f"\nP&L:")
        print(f"  Total: ₹{summary['session_stats']['daily_pnl']:.2f}")
        print(f"  MIS: ₹{summary['session_stats']['mis_pnl']:.2f}")
        print(f"  CNC: ₹{summary['session_stats']['cnc_pnl']:.2f}")

        print(f"\nActive Positions:")
        print(f"  MIS: {summary['active_positions']['MIS']}")
        print(f"  CNC: {summary['active_positions']['CNC']}")

        print("\n" + "="*60)


if __name__ == '__main__':
    """Demo and testing"""

    print("\n" + "="*60)
    print("DUAL ORCHESTRATOR - Demo")
    print("="*60)

    orchestrator = DualOrchestrator()

    # Mock signal
    signal = {
        'symbol': 'RELIANCE',
        'signal_score': 88,
        'setup_type': 'pullback_long',
        'analysis_data': {'score': 88, 'confidence': 'high'},
        'chart_data': {'ohlcv': 'mock'},
        'current_price': 1447.50,
        'support': 1440.00,
        'resistance': 1465.00
    }

    # Process signal
    result = orchestrator.process_signal(**signal)

    print("\n" + "="*60)
    print(f"Result Action: {result['action']}")

    if result['action'] == 'ALERT_FOR_APPROVAL':
        print(f"Mode: {result['mode']}")
        print(f"Position: ₹{result['position_size']:.2f}")

    orchestrator.print_session_summary()

    print("\n✅ Demo complete!\n")
