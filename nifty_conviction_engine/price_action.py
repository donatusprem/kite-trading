"""
Price Action Analyzer - Layer 4 of Nifty Direction Conviction Engine

This module analyzes price action patterns, volume behavior, trend structures, and support/resistance
levels to generate conviction signals for trading direction.

Pure Python implementation with no external dependencies.
"""

from typing import List, Dict, Tuple, Optional, Union
from statistics import mean, stdev


class PriceActionAnalyzer:
    """
    Analyzes price action patterns and volume behavior for market direction conviction.

    Processes OHLCV candle data to identify:
    - Support and resistance levels
    - Trend structures (higher/lower highs and lows)
    - Breakout patterns with volume confirmation
    - Volume profile and trends
    - Price-volume divergences
    - Pivot points

    All methods operate on pure Python without external dependencies.
    """

    def __init__(self, candles: List[Dict[str, Union[float, str]]]):
        """
        Initialize the analyzer with candle data.

        Args:
            candles: List of candle dictionaries with keys:
                    'date' (str), 'open' (float), 'high' (float),
                    'low' (float), 'close' (float), 'volume' (float)

        Raises:
            ValueError: If candles list is empty or malformed
        """
        if not candles:
            raise ValueError("Candles list cannot be empty")

        required_keys = {'open', 'high', 'low', 'close', 'volume'}
        if not all(required_keys.issubset(c.keys()) for c in candles):
            raise ValueError(f"Each candle must contain keys: {required_keys}")

        self.candles = candles
        self.length = len(candles)

    # ==================== Support & Resistance ====================

    def identify_support_resistance(self, lookback: int = 50) -> List[Dict[str, Union[float, str, int]]]:
        """
        Identify key support and resistance levels from swing highs and lows.

        Algorithm:
        1. Find local maxima (swing highs) and local minima (swing lows) using 5-candle window
        2. Group nearby levels (within 0.3% of each other)
        3. Count touches at each level
        4. Assign strength based on number of touches

        Args:
            lookback: Number of recent candles to analyze (default: 50)

        Returns:
            List of dicts with keys:
            - level: float, the S/R price level
            - type: "support" or "resistance"
            - touches: int, number of times price touched this level
            - strength: "weak", "moderate", or "strong"
        """
        lookback = min(lookback, self.length)
        start_idx = max(0, self.length - lookback)
        candles_slice = self.candles[start_idx:]

        if len(candles_slice) < 5:
            return []

        swing_highs = []
        swing_lows = []

        # Find swing highs and lows using 5-candle window
        for i in range(2, len(candles_slice) - 2):
            high_prices = [candles_slice[j]['high'] for j in range(i - 2, i + 3)]
            low_prices = [candles_slice[j]['low'] for j in range(i - 2, i + 3)]

            current_high = candles_slice[i]['high']
            current_low = candles_slice[i]['low']

            # Check if current candle is swing high (highest in 5-candle window)
            if current_high == max(high_prices):
                swing_highs.append((start_idx + i, current_high))

            # Check if current candle is swing low (lowest in 5-candle window)
            if current_low == min(low_prices):
                swing_lows.append((start_idx + i, current_low))

        # Group levels within 0.3% tolerance
        def group_levels(prices: List[float], tolerance_pct: float = 0.3) -> List[List[float]]:
            if not prices:
                return []

            sorted_prices = sorted(prices)
            groups = []
            current_group = [sorted_prices[0]]

            for price in sorted_prices[1:]:
                tolerance = current_group[0] * (tolerance_pct / 100)
                if price <= current_group[0] + tolerance:
                    current_group.append(price)
                else:
                    groups.append(current_group)
                    current_group = [price]

            groups.append(current_group)
            return groups

        resistance_prices = [sh[1] for sh in swing_highs]
        support_prices = [sl[1] for sl in swing_lows]

        resistance_groups = group_levels(resistance_prices)
        support_groups = group_levels(support_prices)

        sr_levels = []

        # Process resistance levels
        for group in resistance_groups:
            level = mean(group)
            # Count touches (candles that reached this level)
            touches = sum(1 for c in candles_slice if c['high'] >= level * 0.997 and c['high'] <= level * 1.003)
            strength = self._get_strength(touches)
            sr_levels.append({
                'level': round(level, 2),
                'type': 'resistance',
                'touches': touches,
                'strength': strength
            })

        # Process support levels
        for group in support_groups:
            level = mean(group)
            # Count touches (candles that reached this level)
            touches = sum(1 for c in candles_slice if c['low'] >= level * 0.997 and c['low'] <= level * 1.003)
            strength = self._get_strength(touches)
            sr_levels.append({
                'level': round(level, 2),
                'type': 'support',
                'touches': touches,
                'strength': strength
            })

        # Sort by level
        sr_levels.sort(key=lambda x: x['level'])
        return sr_levels

    def _get_strength(self, touches: int) -> str:
        """Determine strength level based on number of touches."""
        if touches <= 1:
            return 'weak'
        elif touches <= 2:
            return 'moderate'
        else:
            return 'strong'

    # ==================== Trend Structure ====================

    def detect_trend_structure(self, lookback: int = 20) -> Dict[str, Union[str, List[Tuple[int, float]], bool]]:
        """
        Analyze trend structure by identifying higher/lower highs and lows.

        Returns:
            Dict with keys:
            - trend: "UPTREND", "DOWNTREND", or "SIDEWAYS"
            - swing_highs: List of (candle_index, price) tuples
            - swing_lows: List of (candle_index, price) tuples
            - higher_highs: bool, true if recent highs are higher
            - higher_lows: bool, true if recent lows are higher
            - lower_highs: bool, true if recent highs are lower
            - lower_lows: bool, true if recent lows are lower
        """
        lookback = min(lookback, self.length)
        start_idx = max(0, self.length - lookback)
        candles_slice = self.candles[start_idx:]

        if len(candles_slice) < 5:
            return self._default_trend_structure()

        # Find swing highs and lows
        swing_highs = []
        swing_lows = []

        for i in range(2, len(candles_slice) - 2):
            high_prices = [candles_slice[j]['high'] for j in range(i - 2, i + 3)]
            low_prices = [candles_slice[j]['low'] for j in range(i - 2, i + 3)]

            if candles_slice[i]['high'] == max(high_prices):
                swing_highs.append((start_idx + i, candles_slice[i]['high']))

            if candles_slice[i]['low'] == min(low_prices):
                swing_lows.append((start_idx + i, candles_slice[i]['low']))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return self._default_trend_structure()

        # Analyze recent swings
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]

        higher_highs = recent_highs[-1][1] > recent_highs[-2][1] if len(recent_highs) >= 2 else False
        higher_lows = recent_lows[-1][1] > recent_lows[-2][1] if len(recent_lows) >= 2 else False
        lower_highs = recent_highs[-1][1] < recent_highs[-2][1] if len(recent_highs) >= 2 else False
        lower_lows = recent_lows[-1][1] < recent_lows[-2][1] if len(recent_lows) >= 2 else False

        # Determine trend
        if higher_highs and higher_lows:
            trend = "UPTREND"
        elif lower_highs and lower_lows:
            trend = "DOWNTREND"
        else:
            trend = "SIDEWAYS"

        return {
            'trend': trend,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'higher_highs': higher_highs,
            'higher_lows': higher_lows,
            'lower_highs': lower_highs,
            'lower_lows': lower_lows
        }

    def _default_trend_structure(self) -> Dict[str, Union[str, List, bool]]:
        """Return default/neutral trend structure."""
        return {
            'trend': 'SIDEWAYS',
            'swing_highs': [],
            'swing_lows': [],
            'higher_highs': False,
            'higher_lows': False,
            'lower_highs': False,
            'lower_lows': False
        }

    # ==================== Breakout Detection ====================

    def detect_breakout(self, support_resistance_levels: List[Dict]) -> Dict[str, Union[bool, Optional[str], float, int]]:
        """
        Detect if current price is breaking out above resistance or below support.

        Args:
            support_resistance_levels: Output from identify_support_resistance()

        Returns:
            Dict with keys:
            - is_breakout: bool
            - breakout_type: "bullish", "bearish", or None
            - level_broken: float, the S/R level that was broken (or None)
            - volume_confirmed: bool, true if volume > 1.5x average
            - candles_above_below: int, number of candles that closed beyond the level
        """
        if not support_resistance_levels or self.length < 2:
            return {
                'is_breakout': False,
                'breakout_type': None,
                'level_broken': None,
                'volume_confirmed': False,
                'candles_above_below': 0
            }

        current_close = self.candles[-1]['close']
        current_high = self.candles[-1]['high']
        current_low = self.candles[-1]['low']
        current_volume = self.candles[-1]['volume']

        # Calculate average volume from last 20 candles
        lookback_vol = min(20, self.length)
        avg_volume = mean([c['volume'] for c in self.candles[-lookback_vol:]])
        volume_confirmed = current_volume > (avg_volume * 1.5)

        is_breakout = False
        breakout_type = None
        level_broken = None
        candles_above_below = 0

        # Check for breakouts
        for level_dict in support_resistance_levels:
            level = level_dict['level']
            level_type = level_dict['type']

            if level_type == 'resistance' and current_close > level:
                # Bullish breakout
                is_breakout = True
                breakout_type = 'bullish'
                level_broken = level
                # Count candles that closed above this level
                candles_above_below = sum(1 for c in self.candles[-10:] if c['close'] > level)
                break
            elif level_type == 'support' and current_close < level:
                # Bearish breakout
                is_breakout = True
                breakout_type = 'bearish'
                level_broken = level
                # Count candles that closed below this level
                candles_above_below = sum(1 for c in self.candles[-10:] if c['close'] < level)
                break

        return {
            'is_breakout': is_breakout,
            'breakout_type': breakout_type,
            'level_broken': level_broken,
            'volume_confirmed': volume_confirmed,
            'candles_above_below': candles_above_below
        }

    # ==================== Volume Analysis ====================

    def analyze_volume_profile(self, lookback: int = 20) -> Dict[str, Union[float, str, bool]]:
        """
        Analyze volume behavior and trends.

        Args:
            lookback: Number of recent candles to analyze (default: 20)

        Returns:
            Dict with keys:
            - avg_volume: float, average volume over lookback period
            - current_volume_ratio: float, current volume / average volume
            - volume_trend: "INCREASING", "DECREASING", or "STABLE"
            - volume_confirms_price: bool, true if volume supports price direction
        """
        lookback = min(lookback, self.length)
        if lookback < 2:
            return {
                'avg_volume': 0.0,
                'current_volume_ratio': 0.0,
                'volume_trend': 'STABLE',
                'volume_confirms_price': False
            }

        candles_slice = self.candles[-lookback:]
        volumes = [c['volume'] for c in candles_slice]

        avg_volume = mean(volumes)
        current_volume = candles_slice[-1]['volume']
        current_volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0.0

        # Determine volume trend
        first_half_avg = mean(volumes[:len(volumes)//2])
        second_half_avg = mean(volumes[len(volumes)//2:])

        if second_half_avg > first_half_avg * 1.1:
            volume_trend = 'INCREASING'
        elif second_half_avg < first_half_avg * 0.9:
            volume_trend = 'DECREASING'
        else:
            volume_trend = 'STABLE'

        # Check if volume confirms price direction
        current_close = candles_slice[-1]['close']
        current_open = candles_slice[-1]['open']
        price_up = current_close > current_open

        # Calculate average volume of last 5 candles
        recent_vol_avg = mean([c['volume'] for c in candles_slice[-5:]])

        # Rising price + rising volume OR falling price + rising volume = confirmation
        volume_confirms_price = False
        if price_up and current_volume > recent_vol_avg:
            volume_confirms_price = True
        elif not price_up and current_volume > recent_vol_avg:
            volume_confirms_price = True

        return {
            'avg_volume': round(avg_volume, 2),
            'current_volume_ratio': round(current_volume_ratio, 2),
            'volume_trend': volume_trend,
            'volume_confirms_price': volume_confirms_price
        }

    # ==================== Divergence Detection ====================

    def detect_divergence(self, lookback: int = 20) -> Dict[str, Union[bool, Optional[str]]]:
        """
        Detect price-volume divergence using OBV (On-Balance Volume).

        Bullish divergence: Price makes lower lows but OBV makes higher lows
        Bearish divergence: Price makes higher highs but OBV makes lower highs

        Args:
            lookback: Number of recent candles to analyze (default: 20)

        Returns:
            Dict with keys:
            - has_divergence: bool
            - divergence_type: "bullish", "bearish", or None
            - description: str, human-readable description
        """
        lookback = min(lookback, self.length)
        if lookback < 5:
            return {
                'has_divergence': False,
                'divergence_type': None,
                'description': 'Not enough data for divergence analysis'
            }

        candles_slice = self.candles[-lookback:]

        # Calculate OBV
        obv = self._calculate_obv(candles_slice)

        # Find swing lows in price and OBV
        price_lows = []
        obv_lows = []

        for i in range(1, len(candles_slice) - 1):
            if candles_slice[i]['low'] < candles_slice[i-1]['low'] and candles_slice[i]['low'] < candles_slice[i+1]['low']:
                price_lows.append((i, candles_slice[i]['low']))
            if obv[i] < obv[i-1] and obv[i] < obv[i+1]:
                obv_lows.append((i, obv[i]))

        # Find swing highs in price and OBV
        price_highs = []
        obv_highs = []

        for i in range(1, len(candles_slice) - 1):
            if candles_slice[i]['high'] > candles_slice[i-1]['high'] and candles_slice[i]['high'] > candles_slice[i+1]['high']:
                price_highs.append((i, candles_slice[i]['high']))
            if obv[i] > obv[i-1] and obv[i] > obv[i+1]:
                obv_highs.append((i, obv[i]))

        has_divergence = False
        divergence_type = None
        description = 'No divergence detected'

        # Check for bullish divergence: lower price lows, higher OBV lows
        if len(price_lows) >= 2 and len(obv_lows) >= 2:
            if price_lows[-1][1] < price_lows[-2][1] and obv_lows[-1][1] > obv_lows[-2][1]:
                has_divergence = True
                divergence_type = 'bullish'
                description = 'Bullish divergence: Price making lower lows but volume making higher lows'

        # Check for bearish divergence: higher price highs, lower OBV highs
        if len(price_highs) >= 2 and len(obv_highs) >= 2:
            if price_highs[-1][1] > price_highs[-2][1] and obv_highs[-1][1] < obv_highs[-2][1]:
                has_divergence = True
                divergence_type = 'bearish'
                description = 'Bearish divergence: Price making higher highs but volume making lower highs'

        return {
            'has_divergence': has_divergence,
            'divergence_type': divergence_type,
            'description': description
        }

    def _calculate_obv(self, candles: List[Dict]) -> List[float]:
        """Calculate On-Balance Volume (OBV) for a series of candles."""
        obv = []
        obv_value = 0.0

        for candle in candles:
            close = candle['close']
            prev_close = candles[max(0, candles.index(candle) - 1)]['close'] if candles.index(candle) > 0 else close
            volume = candle['volume']

            if close > prev_close:
                obv_value += volume
            elif close < prev_close:
                obv_value -= volume

            obv.append(obv_value)

        return obv

    # ==================== Pivot Points ====================

    def compute_pivot_points(self) -> Dict[str, float]:
        """
        Calculate classic pivot points from the last completed candle.

        Uses: High, Low, Close of the previous session/candle
        Pivot = (H + L + C) / 3
        R1 = (2 * Pivot) - Low
        S1 = (2 * Pivot) - High
        R2 = Pivot + (High - Low)
        S2 = Pivot - (High - Low)
        R3 = Pivot + 2 * (High - Low)
        S3 = Pivot - 2 * (High - Low)

        Returns:
            Dict with keys: pivot, r1, r2, r3, s1, s2, s3 (all floats)
        """
        if self.length < 1:
            return {
                'pivot': 0.0, 'r1': 0.0, 'r2': 0.0, 'r3': 0.0,
                's1': 0.0, 's2': 0.0, 's3': 0.0
            }

        # Use last candle (most recent completed candle)
        last = self.candles[-1]
        high = last['high']
        low = last['low']
        close = last['close']

        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = pivot + 2 * (high - low)
        s3 = pivot - 2 * (high - low)

        return {
            'pivot': round(pivot, 2),
            'r1': round(r1, 2),
            'r2': round(r2, 2),
            'r3': round(r3, 2),
            's1': round(s1, 2),
            's2': round(s2, 2),
            's3': round(s3, 2)
        }

    # ==================== Master Scoring ====================

    def get_price_action_score(self, support_resistance_levels: Optional[List[Dict]] = None) -> Dict:
        """
        Generate comprehensive price action analysis with conviction score.

        Scoring logic:
        - Uptrend structure (HH + HL): +0.5
        - Downtrend structure (LH + LL): -0.5
        - Bullish breakout with volume: +0.7
        - Bearish breakout with volume: -0.7
        - Volume confirms price direction: +0.3 or -0.3
        - Bullish divergence: +0.3
        - Bearish divergence: -0.3
        - Price above pivot: +0.2, below pivot: -0.2

        Score ranges from -2.0 (very bearish) to +2.0 (very bullish)

        Args:
            support_resistance_levels: Optional pre-calculated S/R levels.
                                      If None, will be calculated.

        Returns:
            Dict with comprehensive analysis:
            - score: float (-2.0 to +2.0)
            - direction: "BULLISH", "BEARISH", or "NEUTRAL"
            - trend: dict from detect_trend_structure()
            - support_resistance: list from identify_support_resistance()
            - breakout: dict from detect_breakout()
            - volume: dict from analyze_volume_profile()
            - divergence: dict from detect_divergence()
            - pivots: dict from compute_pivot_points()
            - signals: list of string descriptions of detected signals
        """
        # Get all analysis components
        trend_data = self.detect_trend_structure()
        sr_levels = support_resistance_levels or self.identify_support_resistance()
        breakout_data = self.detect_breakout(sr_levels)
        volume_data = self.analyze_volume_profile()
        divergence_data = self.detect_divergence()
        pivot_data = self.compute_pivot_points()

        # Calculate score
        score = 0.0
        signals = []

        # Trend structure scoring
        if trend_data['higher_highs'] and trend_data['higher_lows']:
            score += 0.5
            signals.append("Uptrend structure (Higher Highs & Lows)")
        elif trend_data['lower_highs'] and trend_data['lower_lows']:
            score -= 0.5
            signals.append("Downtrend structure (Lower Highs & Lows)")
        else:
            signals.append(f"Sideways trend ({trend_data['trend']})")

        # Breakout scoring
        if breakout_data['is_breakout']:
            if breakout_data['breakout_type'] == 'bullish':
                score += 0.7
                if breakout_data['volume_confirmed']:
                    signals.append(f"Bullish breakout above {breakout_data['level_broken']} with volume confirmation")
                else:
                    signals.append(f"Bullish breakout above {breakout_data['level_broken']} (weak volume)")
            elif breakout_data['breakout_type'] == 'bearish':
                score -= 0.7
                if breakout_data['volume_confirmed']:
                    signals.append(f"Bearish breakout below {breakout_data['level_broken']} with volume confirmation")
                else:
                    signals.append(f"Bearish breakout below {breakout_data['level_broken']} (weak volume)")

        # Volume scoring
        if volume_data['volume_confirms_price']:
            current_close = self.candles[-1]['close']
            current_open = self.candles[-1]['open']
            if current_close > current_open:
                score += 0.3
                signals.append("Volume confirms rising price")
            else:
                score -= 0.3
                signals.append("Volume confirms falling price")

        # Divergence scoring
        if divergence_data['has_divergence']:
            if divergence_data['divergence_type'] == 'bullish':
                score += 0.3
                signals.append("Bullish divergence detected")
            elif divergence_data['divergence_type'] == 'bearish':
                score -= 0.3
                signals.append("Bearish divergence detected")

        # Pivot point scoring
        current_close = self.candles[-1]['close']
        pivot = pivot_data['pivot']
        if current_close > pivot:
            score += 0.2
            signals.append(f"Price above pivot ({pivot})")
        elif current_close < pivot:
            score -= 0.2
            signals.append(f"Price below pivot ({pivot})")

        # Clamp score to -2.0 to +2.0
        score = max(-2.0, min(2.0, score))

        # Determine direction
        if score > 0.3:
            direction = 'BULLISH'
        elif score < -0.3:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'

        return {
            'score': round(score, 2),
            'direction': direction,
            'trend': trend_data,
            'support_resistance': sr_levels,
            'breakout': breakout_data,
            'volume': volume_data,
            'divergence': divergence_data,
            'pivots': pivot_data,
            'signals': signals
        }
