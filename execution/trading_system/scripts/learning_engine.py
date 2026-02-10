#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - LEARNING ENGINE
Analyzes performance and adapts scoring/strategy over time
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


class LearningEngine:
    """Captures trading knowledge and evolves system intelligence"""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.base_path = os.path.dirname(os.path.dirname(config_path))
        self.knowledge_file = os.path.join(self.base_path, 'models', 'learned_patterns.json')
        self.load_knowledge()

    def load_knowledge(self):
        """Load accumulated trading knowledge"""
        if os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, 'r') as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = {
                'pattern_success_rates': {},
                'setup_type_performance': {},
                'optimal_entry_times': {},
                'scoring_adjustments': {},
                'market_conditions': {},
                'lessons_learned': []
            }

    def save_knowledge(self):
        """Save knowledge to disk"""
        with open(self.knowledge_file, 'w') as f:
            json.dump(self.knowledge, f, indent=2)

    def analyze_closed_trades(self, days: int = 7) -> Dict:
        """Analyze closed trades over specified period"""

        cutoff_date = datetime.now() - timedelta(days=days)
        all_trades = []

        # Load trades from analysis folder
        analysis_path = os.path.join(self.base_path, 'analysis')

        for filename in os.listdir(analysis_path):
            if filename.startswith('closed_trades_'):
                filepath = os.path.join(analysis_path, filename)
                with open(filepath, 'r') as f:
                    trades = json.load(f)
                    all_trades.extend(trades)

        # Filter by date
        recent_trades = [
            t for t in all_trades
            if datetime.fromisoformat(t['entry_time']) > cutoff_date
        ]

        if not recent_trades:
            return {'error': 'No trades in specified period'}

        # Calculate metrics
        winners = [t for t in recent_trades if t['winner']]
        losers = [t for t in recent_trades if not t['winner']]

        total_pnl = sum([t['final_pnl_amount'] for t in recent_trades])
        avg_win = sum([t['final_pnl_amount'] for t in winners]) / len(winners) if winners else 0
        avg_loss = sum([t['final_pnl_amount'] for t in losers]) / len(losers) if losers else 0

        profit_factor = abs(sum([t['final_pnl_amount'] for t in winners]) /
                           sum([t['final_pnl_amount'] for t in losers])) if losers else float('inf')

        analysis = {
            'period_days': days,
            'total_trades': len(recent_trades),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': len(winners) / len(recent_trades) * 100,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': recent_trades
        }

        return analysis

    def analyze_pattern_performance(self, analysis: Dict):
        """Analyze which patterns perform best"""

        pattern_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_pnl': 0})

        for trade in analysis['trades']:
            patterns = trade['setup_details'].get('patterns', [])

            for pattern in patterns:
                if trade['winner']:
                    pattern_stats[pattern]['wins'] += 1
                else:
                    pattern_stats[pattern]['losses'] += 1

                pattern_stats[pattern]['total_pnl'] += trade['final_pnl_amount']

        # Calculate success rates
        pattern_performance = {}

        for pattern, stats in pattern_stats.items():
            total = stats['wins'] + stats['losses']
            pattern_performance[pattern] = {
                'win_rate': stats['wins'] / total * 100 if total > 0 else 0,
                'trades': total,
                'total_pnl': stats['total_pnl'],
                'avg_pnl': stats['total_pnl'] / total if total > 0 else 0
            }

        # Update knowledge
        self.knowledge['pattern_success_rates'] = pattern_performance
        self.save_knowledge()

        return pattern_performance

    def analyze_setup_types(self, analysis: Dict):
        """Analyze LONG vs SHORT performance"""

        setup_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_pnl': 0})

        for trade in analysis['trades']:
            setup_type = trade['type']

            if trade['winner']:
                setup_stats[setup_type]['wins'] += 1
            else:
                setup_stats[setup_type]['losses'] += 1

            setup_stats[setup_type]['total_pnl'] += trade['final_pnl_amount']

        # Calculate performance
        setup_performance = {}

        for setup_type, stats in setup_stats.items():
            total = stats['wins'] + stats['losses']
            setup_performance[setup_type] = {
                'win_rate': stats['wins'] / total * 100 if total > 0 else 0,
                'trades': total,
                'total_pnl': stats['total_pnl'],
                'avg_pnl': stats['total_pnl'] / total if total > 0 else 0
            }

        # Update knowledge
        self.knowledge['setup_type_performance'] = setup_performance
        self.save_knowledge()

        return setup_performance

    def identify_improvements(self, analysis: Dict) -> List[Dict]:
        """Identify areas for improvement based on data"""

        improvements = []

        # Check win rate
        if analysis['win_rate'] < 60:
            improvements.append({
                'area': 'Entry Quality',
                'issue': f"Win rate at {analysis['win_rate']:.1f}% (target: >60%)",
                'suggestion': 'Increase minimum score threshold or refine entry criteria'
            })

        # Check profit factor
        if analysis['profit_factor'] < 2:
            improvements.append({
                'area': 'Risk Management',
                'issue': f"Profit factor at {analysis['profit_factor']:.2f} (target: >2.0)",
                'suggestion': 'Let winners run longer or cut losses faster'
            })

        # Check average loss vs average win
        if abs(analysis['avg_loss']) > analysis['avg_win'] * 0.5:
            improvements.append({
                'area': 'Position Sizing',
                'issue': 'Average losses too large relative to wins',
                'suggestion': 'Tighten stops or reduce position size on lower-score setups'
            })

        # Analyze pattern performance
        pattern_perf = self.knowledge.get('pattern_success_rates', {})

        losing_patterns = [
            p for p, stats in pattern_perf.items()
            if stats['win_rate'] < 50 and stats['trades'] >= 5
        ]

        if losing_patterns:
            improvements.append({
                'area': 'Pattern Selection',
                'issue': f"Patterns with <50% win rate: {', '.join(losing_patterns)}",
                'suggestion': 'Reduce scoring weight for these patterns or avoid entirely'
            })

        return improvements

    def generate_daily_review(self):
        """Generate daily performance review"""

        # Analyze last 7 days
        analysis = self.analyze_closed_trades(days=7)

        if 'error' in analysis:
            print(f"\n[REVIEW] {analysis['error']}")
            return

        # Analyze patterns and setups
        pattern_perf = self.analyze_pattern_performance(analysis)
        setup_perf = self.analyze_setup_types(analysis)
        improvements = self.identify_improvements(analysis)

        # Generate report
        report = {
            'date': datetime.now().isoformat(),
            'period': '7 days',
            'overall_performance': {
                'total_trades': analysis['total_trades'],
                'win_rate': analysis['win_rate'],
                'profit_factor': analysis['profit_factor'],
                'total_pnl': analysis['total_pnl']
            },
            'pattern_performance': pattern_perf,
            'setup_performance': setup_perf,
            'improvements': improvements
        }

        # Save report
        report_file = os.path.join(
            self.base_path,
            'analysis',
            f"review_{datetime.now().strftime('%Y%m%d')}.json"
        )

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Display report
        self.display_review(report)

        return report

    def display_review(self, report: Dict):
        """Display performance review"""

        print("\n" + "="*70)
        print(f"  PERFORMANCE REVIEW - {report['period'].upper()}")
        print("="*70)

        perf = report['overall_performance']
        print(f"\nOverall Performance:")
        print(f"  Trades: {perf['total_trades']}")
        print(f"  Win Rate: {perf['win_rate']:.1f}%")
        print(f"  Profit Factor: {perf['profit_factor']:.2f}")
        print(f"  Total P&L: ₹{perf['total_pnl']:.2f}")

        print(f"\nPattern Performance:")
        for pattern, stats in report['pattern_performance'].items():
            print(f"  {pattern}: {stats['win_rate']:.1f}% ({stats['trades']} trades)")

        print(f"\nSetup Type Performance:")
        for setup, stats in report['setup_performance'].items():
            print(f"  {setup}: {stats['win_rate']:.1f}% | Avg P&L: ₹{stats['avg_pnl']:.2f}")

        if report['improvements']:
            print(f"\n📊 Areas for Improvement:")
            for i, imp in enumerate(report['improvements'], 1):
                print(f"\n  {i}. {imp['area']}")
                print(f"     Issue: {imp['issue']}")
                print(f"     → {imp['suggestion']}")

        print("\n" + "="*70 + "\n")

    def capture_lesson(self, lesson: str, category: str = 'general'):
        """Capture a trading lesson learned"""

        lesson_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'lesson': lesson
        }

        self.knowledge['lessons_learned'].append(lesson_entry)
        self.save_knowledge()

        print(f"\n[LESSON CAPTURED] {category}: {lesson}")

    def suggest_scoring_adjustments(self) -> Dict:
        """Suggest adjustments to scoring weights based on performance"""

        pattern_perf = self.knowledge.get('pattern_success_rates', {})
        setup_perf = self.knowledge.get('setup_type_performance', {})

        suggestions = {
            'pattern_weights': {},
            'setup_filters': {},
            'threshold_adjustments': {}
        }

        # Adjust pattern weights
        for pattern, stats in pattern_perf.items():
            if stats['trades'] >= 10:  # Sufficient sample size
                if stats['win_rate'] > 70:
                    suggestions['pattern_weights'][pattern] = {
                        'action': 'INCREASE',
                        'current_impact': 'medium',
                        'suggested_impact': 'high',
                        'reason': f"{stats['win_rate']:.0f}% win rate"
                    }
                elif stats['win_rate'] < 40:
                    suggestions['pattern_weights'][pattern] = {
                        'action': 'DECREASE',
                        'current_impact': 'medium',
                        'suggested_impact': 'low',
                        'reason': f"Only {stats['win_rate']:.0f}% win rate"
                    }

        return suggestions


def main():
    """Test learning engine"""

    config_path = "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3/config/trading_rules.json"
    engine = LearningEngine(config_path)

    print("\n" + "="*70)
    print("  LEARNING ENGINE - PERFORMANCE ANALYSIS")
    print("="*70 + "\n")

    # Generate daily review
    engine.generate_daily_review()

    # Display current knowledge
    print("\nCurrent Knowledge Base:")
    print(f"  Patterns Analyzed: {len(engine.knowledge.get('pattern_success_rates', {}))}")
    print(f"  Lessons Captured: {len(engine.knowledge.get('lessons_learned', []))}")


if __name__ == "__main__":
    main()
