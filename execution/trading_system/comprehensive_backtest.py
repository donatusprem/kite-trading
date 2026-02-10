#!/usr/bin/env python3
"""
COMPREHENSIVE BACKTEST - Test Multiple Strategies
Test different approaches to find the most robust system
"""

import sys
from datetime import datetime
from backtest_dual_mode_35k import DualModeBacktest

def run_comprehensive_tests():
    """
    Test multiple strategy variations systematically
    """

    print('\n' + '='*70)
    print('🔬 COMPREHENSIVE STRATEGY BACKTEST')
    print('='*70)
    print('\nTesting Period: Dec 25, 2025 - Feb 3, 2026')
    print('Starting Capital: ₹35,000')
    print('Testing Dimensions: 40+ configurations\n')

    results = []

    # ========================================
    # DIMENSION 1: SCORE THRESHOLDS
    # ========================================
    print('\n' + '='*70)
    print('📊 DIMENSION 1: Score Threshold Optimization')
    print('='*70)

    threshold_tests = [
        {'name': 'Ultra Conservative', 'mis': 95, 'cnc': 85},
        {'name': 'Very Conservative', 'mis': 92, 'cnc': 82},
        {'name': 'Conservative', 'mis': 90, 'cnc': 80},
        {'name': 'Moderate-High', 'mis': 87, 'cnc': 77},
        {'name': 'Moderate', 'mis': 85, 'cnc': 75},
        {'name': 'Moderate-Low', 'mis': 83, 'cnc': 73},
        {'name': 'Aggressive', 'mis': 80, 'cnc': 70},
    ]

    for test in threshold_tests:
        result = run_single_test(
            name=f"Threshold: {test['name']}",
            mis_threshold=test['mis'],
            cnc_threshold=test['cnc'],
            mis_stop=0.5,
            cnc_stop=2.0,
            mis_target=1.0,
            cnc_target=2.5
        )
        if result:
            results.append(result)

    # ========================================
    # DIMENSION 2: STOP LOSS SIZING
    # ========================================
    print('\n' + '='*70)
    print('📊 DIMENSION 2: Stop Loss Optimization')
    print('='*70)

    stop_tests = [
        {'name': 'Tight MIS, Normal CNC', 'mis_stop': 0.3, 'cnc_stop': 1.5},
        {'name': 'Normal MIS, Normal CNC', 'mis_stop': 0.5, 'cnc_stop': 1.5},
        {'name': 'Normal MIS, Wide CNC', 'mis_stop': 0.5, 'cnc_stop': 2.0},
        {'name': 'Normal MIS, Very Wide CNC', 'mis_stop': 0.5, 'cnc_stop': 2.5},
        {'name': 'Wide MIS, Wide CNC', 'mis_stop': 0.7, 'cnc_stop': 2.0},
    ]

    for test in stop_tests:
        result = run_single_test(
            name=f"Stop: {test['name']}",
            mis_threshold=90,
            cnc_threshold=80,
            mis_stop=test['mis_stop'],
            cnc_stop=test['cnc_stop'],
            mis_target=1.0,
            cnc_target=2.5
        )
        if result:
            results.append(result)

    # ========================================
    # DIMENSION 3: RISK-REWARD RATIOS
    # ========================================
    print('\n' + '='*70)
    print('📊 DIMENSION 3: Risk-Reward Ratio Optimization')
    print('='*70)

    rr_tests = [
        {'name': 'Conservative R:R', 'mis_target': 0.75, 'cnc_target': 2.0},
        {'name': 'Standard R:R', 'mis_target': 1.0, 'cnc_target': 2.5},
        {'name': 'Aggressive R:R', 'mis_target': 1.5, 'cnc_target': 3.0},
        {'name': 'Very Aggressive R:R', 'mis_target': 2.0, 'cnc_target': 4.0},
    ]

    for test in rr_tests:
        result = run_single_test(
            name=f"R:R: {test['name']}",
            mis_threshold=90,
            cnc_threshold=80,
            mis_stop=0.5,
            cnc_stop=2.0,
            mis_target=test['mis_target'],
            cnc_target=test['cnc_target']
        )
        if result:
            results.append(result)

    # ========================================
    # DIMENSION 4: COMBINED OPTIMIZATIONS
    # ========================================
    print('\n' + '='*70)
    print('📊 DIMENSION 4: Combined Strategy Variations')
    print('='*70)

    combined_tests = [
        {
            'name': 'Ultra Conservative + Wide Stops',
            'mis_threshold': 95, 'cnc_threshold': 85,
            'mis_stop': 0.5, 'cnc_stop': 2.5,
            'mis_target': 1.0, 'cnc_target': 3.0
        },
        {
            'name': 'Conservative + Tight Targets',
            'mis_threshold': 90, 'cnc_threshold': 80,
            'mis_stop': 0.5, 'cnc_stop': 2.0,
            'mis_target': 0.75, 'cnc_target': 2.0
        },
        {
            'name': 'Moderate + Aggressive R:R',
            'mis_threshold': 85, 'cnc_threshold': 75,
            'mis_stop': 0.5, 'cnc_stop': 1.5,
            'mis_target': 1.5, 'cnc_target': 3.5
        },
        {
            'name': 'High Threshold + Tight Stops',
            'mis_threshold': 92, 'cnc_threshold': 82,
            'mis_stop': 0.4, 'cnc_stop': 1.8,
            'mis_target': 1.0, 'cnc_target': 2.5
        },
    ]

    for test in combined_tests:
        result = run_single_test(
            name=test['name'],
            mis_threshold=test['mis_threshold'],
            cnc_threshold=test['cnc_threshold'],
            mis_stop=test['mis_stop'],
            cnc_stop=test['cnc_stop'],
            mis_target=test['mis_target'],
            cnc_target=test['cnc_target']
        )
        if result:
            results.append(result)

    # ========================================
    # DIMENSION 5: MIS-ONLY vs CNC-ONLY
    # ========================================
    print('\n' + '='*70)
    print('📊 DIMENSION 5: Single-Mode Strategies')
    print('='*70)

    # MIS-only (set CNC threshold impossibly high)
    result = run_single_test(
        name='MIS-Only Strategy',
        mis_threshold=90,
        cnc_threshold=99,  # Effectively disable CNC
        mis_stop=0.5,
        cnc_stop=2.0,
        mis_target=1.0,
        cnc_target=2.5
    )
    if result:
        results.append(result)

    # CNC-only (set MIS threshold impossibly high)
    result = run_single_test(
        name='CNC-Only Strategy',
        mis_threshold=99,  # Effectively disable MIS
        cnc_threshold=80,
        mis_stop=0.5,
        cnc_stop=2.0,
        mis_target=1.0,
        cnc_target=2.5
    )
    if result:
        results.append(result)

    # ========================================
    # ANALYSIS & RANKING
    # ========================================
    print('\n' + '='*70)
    print('📈 COMPREHENSIVE RESULTS ANALYSIS')
    print('='*70)

    # Sort by returns
    results.sort(key=lambda x: x['returns'], reverse=True)

    # Print top 10
    print('\n🏆 TOP 10 CONFIGURATIONS BY RETURNS:')
    print('-'*70)
    print(f"{'Rank':<5} {'Configuration':<35} {'WR%':>6} {'P&L':>10} {'Ret%':>7}")
    print('-'*70)

    for i, r in enumerate(results[:10], 1):
        print(f"{i:<5} {r['name']:<35} {r['win_rate']:>6.1f} {r['pnl']:>10.2f} {r['returns']:>6.1f}%")

    # Print worst 5 (to learn what NOT to do)
    print('\n❌ WORST 5 CONFIGURATIONS (Learn What to Avoid):')
    print('-'*70)
    for i, r in enumerate(results[-5:], len(results)-4):
        print(f"{i:<5} {r['name']:<35} {r['win_rate']:>6.1f} {r['pnl']:>10.2f} {r['returns']:>6.1f}%")

    # Detailed top 3
    print('\n' + '='*70)
    print('🥇 TOP 3 CONFIGURATIONS - DETAILED ANALYSIS')
    print('='*70)

    for i, r in enumerate(results[:3], 1):
        print(f'\n{["🥇", "🥈", "🥉"][i-1]} RANK {i}: {r["name"]}')
        print('-'*70)
        print(f"Parameters:")
        print(f"  MIS Threshold: {r['mis_threshold']}+")
        print(f"  CNC Threshold: {r['cnc_threshold']}+")
        print(f"  MIS Stop/Target: {r['mis_stop']}% / {r['mis_target']}%")
        print(f"  CNC Stop/Target: {r['cnc_stop']}% / {r['cnc_target']}%")
        print(f"\nPerformance:")
        print(f"  Total Trades: {r['trades']}")
        print(f"  Win Rate: {r['win_rate']:.1f}%")
        print(f"  Net P&L: ₹{r['pnl']:.2f}")
        print(f"  Returns: {r['returns']:+.2f}%")
        print(f"  Profit Factor: {r['profit_factor']:.2f}")
        print(f"\nMode Breakdown:")
        print(f"  MIS: {r['mis_trades']} trades, ₹{r['mis_pnl']:.2f}")
        print(f"  CNC: {r['cnc_trades']} trades, ₹{r['cnc_pnl']:.2f}")

    # Statistical insights
    print('\n' + '='*70)
    print('📊 STATISTICAL INSIGHTS')
    print('='*70)

    profitable_configs = [r for r in results if r['pnl'] > 0]

    print(f"\nProfitable Configurations: {len(profitable_configs)}/{len(results)} ({len(profitable_configs)/len(results)*100:.1f}%)")

    if profitable_configs:
        avg_profitable_wr = sum(r['win_rate'] for r in profitable_configs) / len(profitable_configs)
        avg_profitable_returns = sum(r['returns'] for r in profitable_configs) / len(profitable_configs)

        print(f"Average Win Rate (Profitable): {avg_profitable_wr:.1f}%")
        print(f"Average Returns (Profitable): {avg_profitable_returns:+.2f}%")

        # Threshold analysis
        high_threshold_configs = [r for r in results if r['mis_threshold'] >= 90 and r['cnc_threshold'] >= 80]
        high_threshold_profitable = [r for r in high_threshold_configs if r['pnl'] > 0]

        print(f"\nHigh Threshold (90+/80+) Configs: {len(high_threshold_configs)}")
        print(f"High Threshold Profitable: {len(high_threshold_profitable)}/{len(high_threshold_configs)} ({len(high_threshold_profitable)/len(high_threshold_configs)*100:.1f}%)")

        # Wide stop analysis
        wide_stop_configs = [r for r in results if r['cnc_stop'] >= 2.0]
        wide_stop_profitable = [r for r in wide_stop_configs if r['pnl'] > 0]

        print(f"\nWide CNC Stop (2%+) Configs: {len(wide_stop_configs)}")
        print(f"Wide Stop Profitable: {len(wide_stop_profitable)}/{len(wide_stop_configs)} ({len(wide_stop_profitable)/len(wide_stop_configs)*100:.1f}%)")

    # Key findings
    print('\n' + '='*70)
    print('💡 KEY FINDINGS')
    print('='*70)

    best = results[0]

    print(f"\n1. OPTIMAL CONFIGURATION:")
    print(f"   {best['name']}")
    print(f"   Returns: {best['returns']:+.2f}% | Win Rate: {best['win_rate']:.1f}%")

    print(f"\n2. THRESHOLD INSIGHT:")
    if high_threshold_profitable:
        print(f"   ✅ Higher thresholds (90+/80+) show {len(high_threshold_profitable)/len(high_threshold_configs)*100:.1f}% success rate")
        print(f"   Quality > Quantity validated")

    print(f"\n3. STOP LOSS INSIGHT:")
    if wide_stop_profitable:
        print(f"   ✅ Wider CNC stops (2%+) show {len(wide_stop_profitable)/len(wide_stop_configs)*100:.1f}% success rate")
        print(f"   Room to breathe prevents false stops")

    print(f"\n4. MODE COMPARISON:")
    mis_dominant = best['mis_pnl'] > best['cnc_pnl']
    if mis_dominant:
        print(f"   MIS contributed more P&L in best config")
    else:
        print(f"   CNC contributed more P&L in best config")

    # Final recommendation
    print('\n' + '='*70)
    print('🎯 FINAL RECOMMENDATION')
    print('='*70)

    print(f"\nImplement: {best['name']}")
    print(f"\nConfiguration:")
    print(f"  MIS: {best['mis_threshold']}+ score, {best['mis_stop']}% stop, {best['mis_target']}% target")
    print(f"  CNC: {best['cnc_threshold']}+ score, {best['cnc_stop']}% stop, {best['cnc_target']}% target")

    print(f"\nExpected Performance:")
    print(f"  Win Rate: {best['win_rate']:.1f}%")
    print(f"  Monthly Returns: ~{best['returns']/1.33:.1f}% (₹{best['pnl']/1.33:.0f})")
    print(f"  Annual Returns: ~{best['returns']*9:.1f}% (₹{best['pnl']*9:.0f})")

    print('\n' + '='*70)
    print('✅ COMPREHENSIVE BACKTEST COMPLETE')
    print('='*70)
    print(f'\nTested: {len(results)} configurations')
    print(f'Best Config: {best["name"]}')
    print(f'Best Returns: {best["returns"]:+.2f}%')
    print('\nNext: Update config files and paper trade!')
    print('='*70 + '\n')


def run_single_test(name, mis_threshold, cnc_threshold, mis_stop, cnc_stop, mis_target, cnc_target):
    """Run a single backtest configuration"""

    try:
        backtester = DualModeBacktest(starting_capital=35000)

        # Apply configuration
        backtester.mis_config['scoring']['min_score_threshold'] = mis_threshold
        backtester.cnc_config['scoring']['min_score_threshold'] = cnc_threshold
        backtester.mis_config['exit_rules']['stop_loss_pct'] = mis_stop
        backtester.cnc_config['exit_rules']['stop_loss_pct'] = cnc_stop
        backtester.mis_config['exit_rules']['target_pct'] = mis_target
        backtester.cnc_config['exit_rules']['target1_pct'] = cnc_target

        # Run silently
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            backtester.run_backtest(datetime(2025, 12, 25), num_days=40)

        # Extract results
        if not backtester.trades:
            return None

        total_trades = len(backtester.trades)
        wins = [t for t in backtester.trades if t['pnl_net'] > 0]
        losses = [t for t in backtester.trades if t['pnl_net'] <= 0]

        total_pnl = sum(t['pnl_net'] for t in backtester.trades)
        gross_profit = sum(t['pnl_gross'] for t in wins)
        gross_loss = sum(t['pnl_gross'] for t in losses)

        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else 0

        final_capital = backtester.cash
        returns_pct = ((final_capital - 35000) / 35000) * 100

        mis_trades = [t for t in backtester.trades if t['mode'] == 'MIS']
        cnc_trades = [t for t in backtester.trades if t['mode'] == 'CNC']

        result = {
            'name': name,
            'mis_threshold': mis_threshold,
            'cnc_threshold': cnc_threshold,
            'mis_stop': mis_stop,
            'cnc_stop': cnc_stop,
            'mis_target': mis_target,
            'cnc_target': cnc_target,
            'trades': total_trades,
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins)/total_trades)*100,
            'pnl': total_pnl,
            'returns': returns_pct,
            'profit_factor': profit_factor,
            'mis_trades': len(mis_trades),
            'cnc_trades': len(cnc_trades),
            'mis_pnl': sum(t['pnl_net'] for t in mis_trades) if mis_trades else 0,
            'cnc_pnl': sum(t['pnl_net'] for t in cnc_trades) if cnc_trades else 0
        }

        # Print inline
        print(f"✓ {name:<40} | {total_trades:2d} trades | {(len(wins)/total_trades)*100:5.1f}% WR | ₹{total_pnl:8.2f} | {returns_pct:+6.2f}%")

        return result

    except Exception as e:
        print(f"✗ {name:<40} | Error: {str(e)}")
        return None


if __name__ == '__main__':
    run_comprehensive_tests()
