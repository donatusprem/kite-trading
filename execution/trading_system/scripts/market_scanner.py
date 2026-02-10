#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - MARKET SCANNER
Real-time technical analysis and opportunity detection
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time

# Will need: pip install requests pandas numpy ta --break-system-packages
try:
    import requests
    import pandas as pd
    import numpy as np
    import ta
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests pandas numpy ta --break-system-packages")
    import requests
    import pandas as pd
    import numpy as np
    import ta

class TechnicalAnalyzer:
    """Advanced technical analysis for structure-based trading"""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.base_path = os.path.dirname(os.path.dirname(config_path))

    def detect_support_resistance(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """Identify key support and resistance levels"""
        highs = df['high'].rolling(window=lookback, center=True).max()
        lows = df['low'].rolling(window=lookback, center=True).min()

        # Find pivots
        resistance_levels = []
        support_levels = []

        for i in range(lookback, len(df) - lookback):
            if df['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])
            if df['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(df['low'].iloc[i])

        # Cluster nearby levels
        def cluster_levels(levels, threshold=0.02):
            if not levels:
                return []
            levels = sorted(levels)
            clustered = []
            current_cluster = [levels[0]]

            for level in levels[1:]:
                if (level - current_cluster[-1]) / current_cluster[-1] < threshold:
                    current_cluster.append(level)
                else:
                    clustered.append(sum(current_cluster) / len(current_cluster))
                    current_cluster = [level]
            clustered.append(sum(current_cluster) / len(current_cluster))
            return clustered

        return {
            'resistance': cluster_levels(resistance_levels)[-3:],  # Top 3
            'support': cluster_levels(support_levels)[-3:],  # Bottom 3
            'current_price': df['close'].iloc[-1]
        }

    def identify_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """Find Fair Value Gaps (FVG) - price imbalances"""
        fvgs = []

        for i in range(2, len(df)):
            # Bullish FVG: candle[i-2] high < candle[i] low
            if df['high'].iloc[i-2] < df['low'].iloc[i]:
                fvgs.append({
                    'type': 'bullish',
                    'top': df['low'].iloc[i],
                    'bottom': df['high'].iloc[i-2],
                    'index': i,
                    'filled': False
                })

            # Bearish FVG: candle[i-2] low > candle[i] high
            if df['low'].iloc[i-2] > df['high'].iloc[i]:
                fvgs.append({
                    'type': 'bearish',
                    'top': df['low'].iloc[i-2],
                    'bottom': df['high'].iloc[i],
                    'index': i,
                    'filled': False
                })

        # Check if recent FVGs are still unfilled
        current_price = df['close'].iloc[-1]
        for fvg in fvgs[-10:]:  # Check last 10 FVGs
            if fvg['type'] == 'bullish':
                fvg['filled'] = current_price < fvg['bottom']
            else:
                fvg['filled'] = current_price > fvg['top']

        return [fvg for fvg in fvgs[-10:] if not fvg['filled']]

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Determine trend direction and strength"""
        # Calculate EMAs
        df['ema_20'] = ta.trend.ema_indicator(df['close'], window=20)
        df['ema_50'] = ta.trend.ema_indicator(df['close'], window=50)

        # Higher highs and higher lows = uptrend
        recent_highs = df['high'].tail(10).values
        recent_lows = df['low'].tail(10).values

        higher_highs = sum([recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs))]) > 6
        higher_lows = sum([recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows))]) > 6

        lower_highs = sum([recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs))]) > 6
        lower_lows = sum([recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows))]) > 6

        if higher_highs and higher_lows and df['ema_20'].iloc[-1] > df['ema_50'].iloc[-1]:
            trend = 'uptrend'
            strength = 'strong'
        elif lower_highs and lower_lows and df['ema_20'].iloc[-1] < df['ema_50'].iloc[-1]:
            trend = 'downtrend'
            strength = 'strong'
        elif df['ema_20'].iloc[-1] > df['ema_50'].iloc[-1]:
            trend = 'uptrend'
            strength = 'weak'
        elif df['ema_20'].iloc[-1] < df['ema_50'].iloc[-1]:
            trend = 'downtrend'
            strength = 'weak'
        else:
            trend = 'sideways'
            strength = 'neutral'

        return {
            'direction': trend,
            'strength': strength,
            'ema_20': df['ema_20'].iloc[-1],
            'ema_50': df['ema_50'].iloc[-1]
        }

    def detect_candlestick_patterns(self, df: pd.DataFrame) -> List[str]:
        """Identify key candlestick patterns at critical levels"""
        patterns = []

        # Get last 3 candles
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

        # Bullish patterns
        if c3['close'] > c3['open']:  # Green candle
            body_size = c3['close'] - c3['open']
            upper_wick = c3['high'] - c3['close']
            lower_wick = c3['open'] - c3['low']

            # Bullish engulfing
            if (c2['close'] < c2['open'] and
                c3['open'] < c2['close'] and
                c3['close'] > c2['open']):
                patterns.append('bullish_engulfing')

            # Hammer (small body, long lower wick)
            if lower_wick > body_size * 2 and upper_wick < body_size * 0.3:
                patterns.append('hammer')

            # Morning star
            if (c1['close'] < c1['open'] and
                c2['close'] < c2['open'] and
                abs(c2['close'] - c2['open']) < body_size * 0.3 and
                c3['close'] > (c1['open'] + c1['close']) / 2):
                patterns.append('morning_star')

        # Bearish patterns
        if c3['close'] < c3['open']:  # Red candle
            body_size = c3['open'] - c3['close']
            upper_wick = c3['high'] - c3['open']
            lower_wick = c3['close'] - c3['low']

            # Bearish engulfing
            if (c2['close'] > c2['open'] and
                c3['open'] > c2['close'] and
                c3['close'] < c2['open']):
                patterns.append('bearish_engulfing')

            # Shooting star (small body, long upper wick)
            if upper_wick > body_size * 2 and lower_wick < body_size * 0.3:
                patterns.append('shooting_star')

            # Evening star
            if (c1['close'] > c1['open'] and
                c2['close'] > c2['open'] and
                abs(c2['close'] - c2['open']) < body_size * 0.3 and
                c3['close'] < (c1['open'] + c1['close']) / 2):
                patterns.append('evening_star')

        return patterns

    def calculate_score(self, analysis: Dict) -> int:
        """Score setup quality from 0-100 based on technical confluence"""
        score = 0
        weights = self.config['technical_criteria']

        # Support/Resistance proximity (25 points)
        sr_score = 0
        current_price = analysis['sr_levels']['current_price']

        for support in analysis['sr_levels']['support']:
            distance_pct = abs(current_price - support) / current_price
            if distance_pct < 0.02:  # Within 2%
                sr_score = 25
            elif distance_pct < 0.03:  # Within 3%
                sr_score = max(sr_score, 20)

        for resistance in analysis['sr_levels']['resistance']:
            distance_pct = abs(current_price - resistance) / current_price
            if distance_pct < 0.02:
                sr_score = max(sr_score, 25)
            elif distance_pct < 0.03:
                sr_score = max(sr_score, 20)

        score += sr_score

        # Fair Value Gap presence (20 points)
        if len(analysis['fvgs']) > 0:
            score += 20
        elif len(analysis['fvgs']) > 2:
            score += 15

        # Trend alignment (20 points)
        if analysis['trend']['strength'] == 'strong':
            score += 20
        elif analysis['trend']['strength'] == 'weak':
            score += 10

        # Candlestick patterns (15 points)
        pattern_scores = {
            'bullish_engulfing': 15,
            'bearish_engulfing': 15,
            'morning_star': 15,
            'evening_star': 15,
            'hammer': 12,
            'shooting_star': 12
        }

        pattern_score = max([pattern_scores.get(p, 0) for p in analysis['patterns']] + [0])
        score += pattern_score

        # Volume profile (10 points)
        if analysis.get('volume_above_avg', False):
            score += 10
        elif analysis.get('volume_moderate', False):
            score += 5

        # Risk:Reward (10 points)
        if analysis.get('risk_reward', 0) >= 3:
            score += 10
        elif analysis.get('risk_reward', 0) >= 2:
            score += 7

        return min(score, 100)

    def analyze_stock(self, symbol: str, df: pd.DataFrame) -> Dict:
        """Complete technical analysis for a single stock"""

        if len(df) < 50:
            return None

        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sr_levels': self.detect_support_resistance(df),
            'fvgs': self.identify_fair_value_gaps(df),
            'trend': self.analyze_trend(df),
            'patterns': self.detect_candlestick_patterns(df),
            'current_price': df['close'].iloc[-1],
            'volume': df['volume'].iloc[-1],
            'avg_volume': df['volume'].mean(),
        }

        # Add volume analysis
        analysis['volume_above_avg'] = analysis['volume'] > analysis['avg_volume'] * 1.5
        analysis['volume_moderate'] = analysis['volume'] > analysis['avg_volume']

        # Calculate score
        analysis['score'] = self.calculate_score(analysis)

        # Determine setup type
        if analysis['score'] >= self.config['entry_rules']['minimum_score']:
            if analysis['trend']['direction'] == 'uptrend':
                analysis['setup_type'] = 'LONG'
                analysis['entry_strategy'] = 'Wait for pullback to support/FVG, enter on bullish confirmation'
            elif analysis['trend']['direction'] == 'downtrend':
                analysis['setup_type'] = 'SHORT'
                analysis['entry_strategy'] = 'Wait for pullback to resistance/FVG, enter on bearish confirmation'
            else:
                analysis['setup_type'] = 'RANGE'
                analysis['entry_strategy'] = 'Trade bounces at support/resistance'
        else:
            analysis['setup_type'] = 'SKIP'
            analysis['entry_strategy'] = 'No high-quality setup'

        return analysis


class MarketScanner:
    """Main scanner that reads OHLCV data and runs technical analysis"""

    PATTERN_LABELS = {
        'bullish_engulfing': 'Bullish Engulfing',
        'bearish_engulfing': 'Bearish Engulfing',
        'hammer': 'Hammer',
        'shooting_star': 'Shooting Star',
        'morning_star': 'Morning Star',
        'evening_star': 'Evening Star',
    }

    def __init__(self, config_path: str):
        self.analyzer = TechnicalAnalyzer(config_path)
        self.config = self.analyzer.config
        self.base_path = self.analyzer.base_path
        self.data_dir = os.path.join(self.base_path, 'data')
        self.ohlcv_path = os.path.join(self.data_dir, 'historical_ohlcv.json')

    def load_ohlcv(self) -> Dict[str, pd.DataFrame]:
        """Load OHLCV data from historical_ohlcv.json into DataFrames"""
        if not os.path.exists(self.ohlcv_path):
            print(f"[ERROR] OHLCV file not found: {self.ohlcv_path}")
            return {}

        with open(self.ohlcv_path, 'r') as f:
            raw = json.load(f)

        if not raw:
            print("[ERROR] OHLCV file is empty")
            return {}

        frames = {}
        for symbol, bars in raw.items():
            if not bars:
                continue
            df = pd.DataFrame(bars)
            # Normalize column names (Kite returns 'date','open','high','low','close','volume')
            df.columns = [c.lower() for c in df.columns]
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            frames[symbol] = df
            print(f"[LOAD] {symbol}: {len(df)} bars")

        return frames

    def format_opportunity(self, analysis: Dict) -> Dict:
        """Transform analyzer output into the format the dashboard expects"""
        # Build signals list
        signals = []
        for p in analysis.get('patterns', []):
            signals.append(self.PATTERN_LABELS.get(p, p.replace('_', ' ').title()))

        trend = analysis.get('trend', {})
        if trend.get('strength') == 'strong':
            signals.append(f"Strong {trend['direction'].title()}")
        elif trend.get('direction') != 'sideways':
            signals.append(trend['direction'].title())

        if analysis.get('volume_above_avg'):
            signals.append('High Volume')
        if analysis.get('fvgs'):
            fvg_type = analysis['fvgs'][0]['type'].title()
            signals.append(f'{fvg_type} FVG Present')

        sr = analysis.get('sr_levels', {})
        current = analysis.get('current_price', 0)

        # Find nearest support for stop loss
        supports = sorted(sr.get('support', []))
        stop_loss = None
        for s in reversed(supports):
            if s < current:
                stop_loss = round(s, 2)
                break
        if stop_loss is None and supports:
            stop_loss = round(supports[0] * 0.98, 2)

        # Find nearest resistance levels for targets
        resistances = sorted(sr.get('resistance', []))
        targets = [r for r in resistances if r > current]
        target1 = round(targets[0], 2) if len(targets) >= 1 else round(current * 1.03, 2)
        target2 = round(targets[1], 2) if len(targets) >= 2 else round(current * 1.05, 2)

        if stop_loss is None:
            stop_loss = round(current * 0.97, 2)

        return {
            'symbol': analysis['symbol'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'score': analysis['score'],
            'ltp': round(current, 2),
            'signals': signals if signals else ['Scanning...'],
            'pattern': signals[0] if signals else 'None',
            'trend': trend.get('direction', 'neutral').title(),
            'stopLoss': stop_loss,
            'target1': target1,
            'target2': target2,
            'setup_type': analysis.get('setup_type', 'SKIP'),
            'entry_strategy': analysis.get('entry_strategy', ''),
        }

    def scan_market(self) -> List[Dict]:
        """Scan all stocks from OHLCV data for opportunities"""
        print(f"\n{'='*60}")
        print(f"[SCAN] Starting market scan at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")

        frames = self.load_ohlcv()
        if not frames:
            print("[WARN] No OHLCV data available. Run data fetch first.")
            return []

        opportunities = []

        for symbol, df in frames.items():
            try:
                analysis = self.analyzer.analyze_stock(symbol, df)
                if analysis is None:
                    print(f"[SKIP] {symbol}: insufficient data ({len(df)} bars)")
                    continue

                formatted = self.format_opportunity(analysis)
                opportunities.append(formatted)
                print(f"[SCAN] {symbol} - Score: {analysis['score']}/100 - {analysis.get('setup_type', 'N/A')}")

            except Exception as e:
                print(f"[ERROR] Failed to analyze {symbol}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        # Sort by score descending
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities

    def save_opportunities(self, opportunities: List[Dict]):
        """Save scan results as a JSON array (format expected by dashboard)"""
        alerts_dir = os.path.join(self.base_path, 'alerts')
        os.makedirs(alerts_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(alerts_dir, f'scan_{timestamp}.json')

        # Save as bare array - matches what the frontend expects
        with open(filepath, 'w') as f:
            json.dump(opportunities, f, indent=2)

        print(f"\n[SAVED] {len(opportunities)} results saved to {filepath}")
        return filepath

    def log_scan(self, opportunities: List[Dict]):
        """Log scan results to journal"""
        journals_dir = os.path.join(self.base_path, 'journals')
        os.makedirs(journals_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d')
        journal_file = os.path.join(journals_dir, f'journal_{timestamp}.jsonl')

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'scan',
            'opportunities_found': len(opportunities),
            'top_scores': [op['score'] for op in opportunities[:5]],
            'top_symbols': [op['symbol'] for op in opportunities[:5]]
        }

        with open(journal_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def run_single_scan(self) -> List[Dict]:
        """Run a single scan and save results. Called by the API."""
        opportunities = self.scan_market()
        if opportunities:
            self.save_opportunities(opportunities)
            self.log_scan(opportunities)
        else:
            # Save empty array so dashboard shows "no setups" instead of stale data
            self.save_opportunities([])
        return opportunities

    def run_continuous(self):
        """Run scanner continuously"""
        print("\n" + "="*60)
        print("TRADING SYSTEM V3 - MARKET SCANNER")
        print("Real-time Technical Analysis & Opportunity Detection")
        print("="*60 + "\n")

        scan_interval = self.config['scanning']['scan_interval_minutes'] * 60

        print(f"[CONFIG] Scan interval: {self.config['scanning']['scan_interval_minutes']} minutes")
        print(f"[CONFIG] Minimum score: {self.config['entry_rules']['minimum_score']}")
        print(f"[CONFIG] Markets: {', '.join(self.config['scanning']['markets'])}\n")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                opportunities = self.run_single_scan()

                if opportunities:
                    high_quality = [o for o in opportunities if o['score'] >= self.config['entry_rules']['minimum_score']]
                    print(f"\n[SUMMARY] {len(opportunities)} scanned, {len(high_quality)} above threshold")
                    for op in opportunities[:3]:
                        print(f"  → {op['symbol']}: {op['score']}/100 - {op['trend']}")
                else:
                    print(f"\n[SUMMARY] No setups found")

                print(f"\n[WAIT] Next scan in {self.config['scanning']['scan_interval_minutes']} minutes...")
                print("-" * 60 + "\n")

                time.sleep(scan_interval)

        except KeyboardInterrupt:
            print("\n\n[STOP] Scanner stopped by user")
            print("="*60)


def run_scan():
    """Run a single scan and return results. Used by the API."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base, 'config', 'trading_rules.json')

    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        return []

    scanner = MarketScanner(config_path)
    return scanner.run_single_scan()


def main():
    """Main entry point"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base, 'config', 'trading_rules.json')

    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    scanner = MarketScanner(config_path)

    if '--once' in sys.argv:
        scanner.run_single_scan()
    else:
        scanner.run_continuous()


if __name__ == "__main__":
    main()
