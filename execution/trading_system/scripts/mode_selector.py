#!/usr/bin/env python3
"""
MODE SELECTOR - Intelligent MIS vs CNC Decision Engine
Chooses optimal trading mode based on score, timing, and capital availability
"""

import json
from datetime import datetime, time
from typing import Dict, Optional, Literal
from pathlib import Path


class ModeSelector:
    """
    Decides whether to trade in MIS (intraday) or CNC (delivery) mode
    Based on signal quality, time of day, and capital availability
    """

    # Score thresholds
    CNC_MIN_SCORE = 75  # Minimum for delivery trades
    MIS_MIN_SCORE = 85  # Stricter for intraday
    EXCEPTIONAL_SCORE = 90  # Prefer intraday for exceptional setups

    # Timing thresholds
    MARKET_OPEN = time(9, 15)
    INTRADAY_CUTOFF = time(14, 30)  # After 2:30 PM, no new MIS trades
    MARKET_CLOSE = time(15, 30)

    # Capital requirements
    CNC_MIN_CASH = 10000  # ₹10k minimum for delivery
    MIS_MIN_MARGIN = 15000  # ₹15k minimum margin for intraday

    def __init__(self, config_path: str = '../config/trading_rules.json'):
        """Initialize mode selector with configuration"""
        self.config_path = Path(config_path)
        self.load_config()

        # Track mode decisions for analysis
        self.decisions = []

    def load_config(self):
        """Load configuration if available"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

            # Override defaults if specified in config
            mode_config = self.config.get('mode_selection', {})
            self.CNC_MIN_SCORE = mode_config.get('cnc_min_score', self.CNC_MIN_SCORE)
            self.MIS_MIN_SCORE = mode_config.get('mis_min_score', self.MIS_MIN_SCORE)
            self.EXCEPTIONAL_SCORE = mode_config.get('exceptional_score', self.EXCEPTIONAL_SCORE)

        except FileNotFoundError:
            print(f"⚠️  Config not found at {self.config_path}, using defaults")
            self.config = {}

    def select_mode(self,
                   signal_score: float,
                   current_time: Optional[time] = None,
                   available_cash: float = 0,
                   available_margin: float = 0,
                   symbol: str = '',
                   setup_type: str = '') -> Dict:
        """
        Main decision function: Choose between MIS, CNC, or SKIP

        Args:
            signal_score: Scanner score (0-100)
            current_time: Current market time (uses now() if None)
            available_cash: Cash balance for CNC trades
            available_margin: Margin available for MIS trades
            symbol: Stock symbol (for logging)
            setup_type: Type of setup detected (for logging)

        Returns:
            Dict with:
                - mode: 'MIS', 'CNC', or 'SKIP'
                - reason: Why this mode was chosen
                - confidence: Confidence in decision (0-100)
                - alternate_mode: What would have been chosen if capital allowed
        """

        if current_time is None:
            current_time = datetime.now().time()

        # Initialize decision dict
        decision = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'setup_type': setup_type,
            'signal_score': signal_score,
            'available_cash': available_cash,
            'available_margin': available_margin,
            'current_time': current_time.strftime('%H:%M:%S'),
            'mode': 'SKIP',
            'reason': '',
            'confidence': 0,
            'alternate_mode': None,
            'checks': {
                'market_open': self._is_market_open(current_time),
                'market_close_soon': self._is_market_close_soon(current_time),
                'cnc_eligible': signal_score >= self.CNC_MIN_SCORE,
                'mis_eligible': signal_score >= self.MIS_MIN_SCORE,
                'has_cash': available_cash >= self.CNC_MIN_CASH,
                'has_margin': available_margin >= self.MIS_MIN_MARGIN,
                'exceptional_setup': signal_score >= self.EXCEPTIONAL_SCORE
            }
        }

        # Check if market is open
        if not decision['checks']['market_open']:
            decision['reason'] = 'Market not open'
            self._log_decision(decision)
            return decision

        # Apply decision tree
        mode_result = self._apply_decision_tree(decision['checks'], current_time)
        decision.update(mode_result)

        # Log decision
        self._log_decision(decision)

        return decision

    def _apply_decision_tree(self, checks: Dict, current_time: time) -> Dict:
        """
        Apply the decision tree logic
        Returns mode, reason, confidence
        """

        # RULE 1: Market closing soon (after 2:30 PM)
        if checks['market_close_soon']:
            if checks['has_cash'] and checks['cnc_eligible']:
                return {
                    'mode': 'CNC',
                    'reason': 'Too late for intraday - market closing soon',
                    'confidence': 80,
                    'alternate_mode': None
                }
            else:
                return {
                    'mode': 'SKIP',
                    'reason': 'Too late for intraday, insufficient cash for CNC',
                    'confidence': 100,
                    'alternate_mode': 'CNC' if checks['cnc_eligible'] else None
                }

        # RULE 2: Exceptional setup (90+ score)
        # Prefer intraday for quick profit, fallback to CNC
        if checks['exceptional_setup']:
            if checks['has_margin'] and checks['mis_eligible']:
                return {
                    'mode': 'MIS',
                    'reason': 'Exceptional setup (90+) - intraday for quick profit',
                    'confidence': 95,
                    'alternate_mode': 'CNC' if checks['has_cash'] and checks['cnc_eligible'] else None
                }
            elif checks['has_cash'] and checks['cnc_eligible']:
                return {
                    'mode': 'CNC',
                    'reason': 'Exceptional setup but no margin - using CNC',
                    'confidence': 85,
                    'alternate_mode': 'MIS'
                }
            else:
                return {
                    'mode': 'SKIP',
                    'reason': 'Exceptional setup but no capital available',
                    'confidence': 100,
                    'alternate_mode': 'MIS' if checks['mis_eligible'] else 'CNC'
                }

        # RULE 3: Good setup (85-89 score)
        # Prefer delivery for lower risk, fallback to intraday
        if checks['mis_eligible']:  # Score >= 85
            if checks['has_cash'] and checks['cnc_eligible']:
                return {
                    'mode': 'CNC',
                    'reason': 'Good setup (85-89) - prefer delivery for lower risk',
                    'confidence': 80,
                    'alternate_mode': 'MIS' if checks['has_margin'] else None
                }
            elif checks['has_margin'] and checks['mis_eligible']:
                return {
                    'mode': 'MIS',
                    'reason': 'Good setup but no cash - using intraday margin',
                    'confidence': 70,
                    'alternate_mode': 'CNC'
                }
            else:
                return {
                    'mode': 'SKIP',
                    'reason': 'Good setup (85+) but no capital available',
                    'confidence': 100,
                    'alternate_mode': 'CNC' if checks['has_cash'] >= self.CNC_MIN_CASH * 0.5 else 'MIS'
                }

        # RULE 4: Marginal setup (75-84 score)
        # CNC only - too risky for intraday
        if checks['cnc_eligible']:  # Score >= 75
            if checks['has_cash']:
                return {
                    'mode': 'CNC',
                    'reason': 'Marginal setup (75-84) - CNC only, too risky for intraday',
                    'confidence': 60,
                    'alternate_mode': None
                }
            else:
                return {
                    'mode': 'SKIP',
                    'reason': 'Marginal setup - needs cash for CNC (MIS too risky)',
                    'confidence': 100,
                    'alternate_mode': 'CNC'
                }

        # RULE 5: Below threshold (< 75)
        return {
            'mode': 'SKIP',
            'reason': f'Score too low ({checks["cnc_eligible"]}) - below CNC threshold (75)',
            'confidence': 100,
            'alternate_mode': None
        }

    def _is_market_open(self, current_time: time) -> bool:
        """Check if market is open"""
        return self.MARKET_OPEN <= current_time <= self.MARKET_CLOSE

    def _is_market_close_soon(self, current_time: time) -> bool:
        """Check if too late for intraday trades"""
        return current_time >= self.INTRADAY_CUTOFF

    def get_mode_rules(self, mode: str) -> Dict:
        """
        Get trading rules for specified mode

        Returns:
            Dict with stop loss, targets, timeouts, etc.
        """

        if mode == 'MIS':
            return {
                'product_type': 'MIS',
                'max_hold_time': time(15, 15),  # 3:15 PM sharp
                'stop_loss_pct': 0.5,  # 0.5% max loss
                'target_pct': 1.0,     # 1% target
                'partial_exits': False,  # Full exit only
                'trailing_stop': False,  # Too fast
                'force_close': True,  # ALWAYS close by 3:15
                'position_size_multiplier': 1.5,  # Can use more due to margin
                'max_positions': 1,  # One at a time
                'description': 'Intraday margin trading - quick scalps'
            }

        elif mode == 'CNC':
            return {
                'product_type': 'CNC',
                'max_hold_time_hours': 48,  # Can hold 2 days
                'stop_loss_pct': 1.5,  # 1.5% max loss
                'target1_pct': 2.5,    # 2.5% first target
                'target2_pct': 4.0,    # 4% second target
                'partial_exits': False,  # Full exit (minimize DP charges)
                'trailing_stop': True,   # Use trailing after T1
                'force_close': False,  # Can hold overnight
                'position_size_multiplier': 1.0,  # Full cash usage
                'max_positions': 1,  # One at a time with limited capital
                'description': 'Delivery trading - hold for structure plays'
            }

        else:
            return {}

    def _log_decision(self, decision: Dict):
        """Log decision for analysis"""
        self.decisions.append(decision)

        # Keep last 100 decisions in memory
        if len(self.decisions) > 100:
            self.decisions = self.decisions[-100:]

    def get_decision_stats(self) -> Dict:
        """Get statistics on mode selection decisions"""

        if not self.decisions:
            return {'message': 'No decisions logged yet'}

        total = len(self.decisions)
        mis_count = sum(1 for d in self.decisions if d['mode'] == 'MIS')
        cnc_count = sum(1 for d in self.decisions if d['mode'] == 'CNC')
        skip_count = sum(1 for d in self.decisions if d['mode'] == 'SKIP')

        return {
            'total_decisions': total,
            'mode_breakdown': {
                'MIS': {'count': mis_count, 'pct': (mis_count/total)*100},
                'CNC': {'count': cnc_count, 'pct': (cnc_count/total)*100},
                'SKIP': {'count': skip_count, 'pct': (skip_count/total)*100}
            },
            'avg_confidence': sum(d['confidence'] for d in self.decisions) / total,
            'capital_blocked_count': sum(1 for d in self.decisions
                                        if 'no capital' in d['reason'].lower() or
                                           'insufficient' in d['reason'].lower())
        }

    def print_decision_summary(self):
        """Print formatted decision statistics"""
        stats = self.get_decision_stats()

        if 'message' in stats:
            print(stats['message'])
            return

        print("\n" + "="*60)
        print("📊 MODE SELECTION STATISTICS")
        print("="*60)
        print(f"\nTotal Decisions: {stats['total_decisions']}")
        print(f"Average Confidence: {stats['avg_confidence']:.1f}%")
        print(f"Capital Blocked: {stats['capital_blocked_count']} times")

        print("\n" + "-"*60)
        print("MODE BREAKDOWN:")
        print("-"*60)
        for mode, data in stats['mode_breakdown'].items():
            print(f"{mode:4s}: {data['count']:3d} ({data['pct']:5.1f}%)")

        print("\n" + "="*60)


if __name__ == '__main__':
    """
    Demo and testing
    """

    print("\n" + "="*60)
    print("MODE SELECTOR - Demo & Testing")
    print("="*60)

    selector = ModeSelector()

    # Test scenarios
    scenarios = [
        {
            'name': 'Exceptional setup, morning, both capital available',
            'score': 95,
            'time': time(10, 30),
            'cash': 15000,
            'margin': 20000,
            'expected': 'MIS'
        },
        {
            'name': 'Exceptional setup, only cash available',
            'score': 92,
            'time': time(11, 0),
            'cash': 12000,
            'margin': 5000,
            'expected': 'CNC'
        },
        {
            'name': 'Good setup (87), prefer CNC',
            'score': 87,
            'time': time(12, 0),
            'cash': 11000,
            'margin': 16000,
            'expected': 'CNC'
        },
        {
            'name': 'Good setup (85), only margin available',
            'score': 85,
            'time': time(13, 0),
            'cash': 3000,
            'margin': 15000,
            'expected': 'MIS'
        },
        {
            'name': 'Good setup but after 2:30 PM',
            'score': 88,
            'time': time(14, 45),
            'cash': 10000,
            'margin': 15000,
            'expected': 'CNC'
        },
        {
            'name': 'Marginal setup (78)',
            'score': 78,
            'time': time(11, 30),
            'cash': 10000,
            'margin': 15000,
            'expected': 'CNC'
        },
        {
            'name': 'Below threshold (72)',
            'score': 72,
            'time': time(10, 0),
            'cash': 10000,
            'margin': 15000,
            'expected': 'SKIP'
        },
        {
            'name': 'Exceptional but no capital',
            'score': 94,
            'time': time(10, 0),
            'cash': 2000,
            'margin': 3000,
            'expected': 'SKIP'
        }
    ]

    print("\n" + "="*60)
    print("TESTING DECISION SCENARIOS")
    print("="*60)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario['name']} ---")
        print(f"Score: {scenario['score']}, Time: {scenario['time'].strftime('%H:%M')}")
        print(f"Cash: ₹{scenario['cash']}, Margin: ₹{scenario['margin']}")

        decision = selector.select_mode(
            signal_score=scenario['score'],
            current_time=scenario['time'],
            available_cash=scenario['cash'],
            available_margin=scenario['margin'],
            symbol='TEST',
            setup_type='demo'
        )

        result_icon = "✅" if decision['mode'] == scenario['expected'] else "❌"
        print(f"\n{result_icon} Decision: {decision['mode']} (Expected: {scenario['expected']})")
        print(f"Confidence: {decision['confidence']}%")
        print(f"Reason: {decision['reason']}")

        if decision['alternate_mode']:
            print(f"Alternate: {decision['alternate_mode']}")

        # Show rules if mode selected
        if decision['mode'] != 'SKIP':
            rules = selector.get_mode_rules(decision['mode'])
            print(f"\nRules for {decision['mode']}:")
            print(f"  Stop Loss: {rules['stop_loss_pct']}%")
            print(f"  Target: {rules.get('target_pct', rules.get('target1_pct'))}%")
            print(f"  Force Close: {rules['force_close']}")

    # Print stats
    selector.print_decision_summary()

    print("\n✅ Demo complete!\n")
