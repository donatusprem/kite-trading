"""
Candlestick Pattern Detection Module - Layer 2 of Nifty Direction Conviction Engine

This module provides comprehensive candlestick pattern recognition for OHLCV data.
Detects 15+ classic candlestick patterns and provides conviction scoring for trading direction.

Pure Python implementation with no external dependencies.
"""

from typing import List, Dict, Tuple, Optional


class CandlestickAnalyzer:
    """
    Analyzes candlestick patterns from OHLCV data.

    Attributes:
        candles (List[Dict]): List of candlestick data with keys:
            - date: str or datetime
            - open: float
            - high: float
            - low: float
            - close: float
            - volume: int or float
    """

    def __init__(self, candles: List[Dict]):
        """
        Initialize the analyzer with candlestick data.

        Args:
            candles: List of dicts containing OHLCV data for each candle

        Raises:
            ValueError: If candles list is empty or invalid
        """
        if not candles:
            raise ValueError("Candles list cannot be empty")

        # Validate candle structure
        required_keys = {'open', 'high', 'low', 'close', 'volume'}
        for i, candle in enumerate(candles):
            if not all(key in candle for key in required_keys):
                raise ValueError(
                    f"Candle at index {i} missing required keys. "
                    f"Required: {required_keys}, Got: {set(candle.keys())}"
                )
            # Validate OHLC logic
            if not (candle['low'] <= candle['open'] and
                    candle['low'] <= candle['close'] and
                    candle['open'] <= candle['high'] and
                    candle['close'] <= candle['high']):
                raise ValueError(f"Candle at index {i} has invalid OHLC values")

        self.candles = candles

    # ==================== HELPER METHODS ====================

    def _body_size(self, candle: Dict) -> float:
        """
        Calculate the body size of a candlestick.

        Args:
            candle: Candlestick data

        Returns:
            Absolute difference between close and open
        """
        return abs(candle['close'] - candle['open'])

    def _upper_shadow(self, candle: Dict) -> float:
        """
        Calculate the upper shadow (wick) of a candlestick.

        Args:
            candle: Candlestick data

        Returns:
            Distance from high to the top of the body (max of open/close)
        """
        body_top = max(candle['open'], candle['close'])
        return candle['high'] - body_top

    def _lower_shadow(self, candle: Dict) -> float:
        """
        Calculate the lower shadow (wick) of a candlestick.

        Args:
            candle: Candlestick data

        Returns:
            Distance from the bottom of the body (min of open/close) to low
        """
        body_bottom = min(candle['open'], candle['close'])
        return body_bottom - candle['low']

    def _is_bullish(self, candle: Dict) -> bool:
        """
        Determine if a candle is bullish (close > open).

        Args:
            candle: Candlestick data

        Returns:
            True if close > open, False otherwise
        """
        return candle['close'] > candle['open']

    def _is_bearish(self, candle: Dict) -> bool:
        """
        Determine if a candle is bearish (close < open).

        Args:
            candle: Candlestick data

        Returns:
            True if close < open, False otherwise
        """
        return candle['close'] < candle['open']

    def _total_range(self, candle: Dict) -> float:
        """
        Calculate total range (high - low) of a candlestick.

        Args:
            candle: Candlestick data

        Returns:
            Difference between high and low
        """
        return candle['high'] - candle['low']

    def _avg_body_size(self, lookback: int = 10) -> float:
        """
        Calculate average body size of recent candles.

        Args:
            lookback: Number of recent candles to average (default: 10)

        Returns:
            Average body size, or 0 if insufficient data
        """
        if len(self.candles) == 0:
            return 0

        look_count = min(lookback, len(self.candles))
        total = sum(self._body_size(self.candles[-i]) for i in range(1, look_count + 1))
        return total / look_count

    def _avg_volume(self, lookback: int = 20) -> float:
        """
        Calculate average volume of recent candles.

        Args:
            lookback: Number of recent candles to average (default: 20)

        Returns:
            Average volume, or 0 if insufficient data
        """
        if len(self.candles) == 0:
            return 0

        look_count = min(lookback, len(self.candles))
        total = sum(self.candles[-i]['volume'] for i in range(1, look_count + 1))
        return total / look_count

    # ==================== PATTERN DETECTION METHODS ====================

    def detect_bullish_engulfing(self, idx: int) -> Tuple[bool, float]:
        """
        Detect bullish engulfing pattern.

        Current bullish candle completely engulfs previous bearish candle.
        Current close > previous open AND current open < previous close.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 1:
            return False, 0.0

        curr = self.candles[idx]
        prev = self.candles[idx - 1]

        # Requires previous bearish and current bullish
        if not self._is_bearish(prev) or not self._is_bullish(curr):
            return False, 0.0

        # Current candle must engulf previous
        if curr['close'] > prev['open'] and curr['open'] < prev['close']:
            # Confidence based on how much current engulfs previous
            engulf_ratio = (curr['close'] - curr['open']) / (prev['open'] - prev['close'])
            confidence = min(1.0, engulf_ratio * 0.5 + 0.5)
            return True, confidence

        return False, 0.0

    def detect_bearish_engulfing(self, idx: int) -> Tuple[bool, float]:
        """
        Detect bearish engulfing pattern.

        Current bearish candle completely engulfs previous bullish candle.
        Current open > previous close AND current close < previous open.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 1:
            return False, 0.0

        curr = self.candles[idx]
        prev = self.candles[idx - 1]

        # Requires previous bullish and current bearish
        if not self._is_bullish(prev) or not self._is_bearish(curr):
            return False, 0.0

        # Current candle must engulf previous
        if curr['open'] > prev['close'] and curr['close'] < prev['open']:
            # Confidence based on how much current engulfs previous
            engulf_ratio = (prev['close'] - prev['open']) / (curr['open'] - curr['close'])
            confidence = min(1.0, engulf_ratio * 0.5 + 0.5)
            return True, confidence

        return False, 0.0

    def detect_hammer(self, idx: int) -> Tuple[bool, float]:
        """
        Detect hammer pattern.

        Small body at the top, long lower shadow (2x+ body size), minimal upper shadow.
        Bullish reversal pattern.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        candle = self.candles[idx]
        body = self._body_size(candle)
        upper_shadow = self._upper_shadow(candle)
        lower_shadow = self._lower_shadow(candle)

        # Small body check
        avg_body = self._avg_body_size()
        if avg_body > 0 and body > avg_body * 1.5:
            return False, 0.0

        # Long lower shadow (at least 2x the body)
        if lower_shadow < body * 2:
            return False, 0.0

        # Minimal upper shadow
        if upper_shadow > body * 0.5:
            return False, 0.0

        # Confidence based on shadow ratio
        if body > 0:
            confidence = min(1.0, (lower_shadow / body) / 5.0)
        else:
            confidence = 0.5

        return True, confidence

    def detect_inverted_hammer(self, idx: int) -> Tuple[bool, float]:
        """
        Detect inverted hammer pattern.

        Small body at bottom, long upper shadow, minimal lower shadow.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        candle = self.candles[idx]
        body = self._body_size(candle)
        upper_shadow = self._upper_shadow(candle)
        lower_shadow = self._lower_shadow(candle)

        # Small body check
        avg_body = self._avg_body_size()
        if avg_body > 0 and body > avg_body * 1.5:
            return False, 0.0

        # Long upper shadow (at least 2x the body)
        if upper_shadow < body * 2:
            return False, 0.0

        # Minimal lower shadow
        if lower_shadow > body * 0.5:
            return False, 0.0

        # Confidence based on shadow ratio
        if body > 0:
            confidence = min(1.0, (upper_shadow / body) / 5.0)
        else:
            confidence = 0.5

        return True, confidence

    def detect_doji(self, idx: int) -> Tuple[bool, float]:
        """
        Detect doji pattern.

        Body < 10% of total range. Indicates indecision.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        candle = self.candles[idx]
        body = self._body_size(candle)
        total_range = self._total_range(candle)

        if total_range == 0:
            return False, 0.0

        body_ratio = body / total_range

        # Body < 10% of range
        if body_ratio <= 0.1:
            confidence = 1.0 - body_ratio * 10  # Higher confidence for smaller bodies
            return True, confidence

        return False, 0.0

    def detect_dragonfly_doji(self, idx: int) -> Tuple[bool, float]:
        """
        Detect dragonfly doji pattern.

        Doji with long lower shadow and no (or minimal) upper shadow.
        Bullish reversal pattern.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        candle = self.candles[idx]

        # Must be a doji first
        is_doji, doji_conf = self.detect_doji(idx)
        if not is_doji:
            return False, 0.0

        upper_shadow = self._upper_shadow(candle)
        lower_shadow = self._lower_shadow(candle)
        body = self._body_size(candle)

        # Long lower shadow, minimal upper shadow
        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            confidence = min(doji_conf, 0.9)
            return True, confidence

        return False, 0.0

    def detect_gravestone_doji(self, idx: int) -> Tuple[bool, float]:
        """
        Detect gravestone doji pattern.

        Doji with long upper shadow and no (or minimal) lower shadow.
        Bearish reversal pattern.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        candle = self.candles[idx]

        # Must be a doji first
        is_doji, doji_conf = self.detect_doji(idx)
        if not is_doji:
            return False, 0.0

        upper_shadow = self._upper_shadow(candle)
        lower_shadow = self._lower_shadow(candle)
        body = self._body_size(candle)

        # Long upper shadow, minimal lower shadow
        if upper_shadow > body * 2 and lower_shadow < body * 0.5:
            confidence = min(doji_conf, 0.9)
            return True, confidence

        return False, 0.0

    def detect_morning_star(self, idx: int) -> Tuple[bool, float]:
        """
        Detect morning star pattern.

        3-candle pattern: big bearish, small body, big bullish closing above 50% of first candle.
        Bullish reversal pattern.

        Args:
            idx: Index of the third (bullish) candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 2:
            return False, 0.0

        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]

        # First candle must be big bearish
        if not self._is_bearish(c1):
            return False, 0.0

        c1_body = self._body_size(c1)
        c2_body = self._body_size(c2)
        c3_body = self._body_size(c3)

        avg_body = self._avg_body_size()

        # First candle is big
        if avg_body > 0 and c1_body < avg_body:
            return False, 0.0

        # Second candle is small
        if c2_body > avg_body:
            return False, 0.0

        # Third candle is bullish and big
        if not self._is_bullish(c3) or c3_body < avg_body:
            return False, 0.0

        # Third closes above 50% of first candle
        midpoint = (c1['open'] + c1['close']) / 2
        if c3['close'] > midpoint:
            confidence = min(1.0, c3_body / (avg_body * 2))
            return True, confidence

        return False, 0.0

    def detect_evening_star(self, idx: int) -> Tuple[bool, float]:
        """
        Detect evening star pattern.

        3-candle pattern: big bullish, small body, big bearish closing below 50% of first.
        Bearish reversal pattern.

        Args:
            idx: Index of the third (bearish) candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 2:
            return False, 0.0

        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]

        # First candle must be big bullish
        if not self._is_bullish(c1):
            return False, 0.0

        c1_body = self._body_size(c1)
        c2_body = self._body_size(c2)
        c3_body = self._body_size(c3)

        avg_body = self._avg_body_size()

        # First candle is big
        if avg_body > 0 and c1_body < avg_body:
            return False, 0.0

        # Second candle is small
        if c2_body > avg_body:
            return False, 0.0

        # Third candle is bearish and big
        if not self._is_bearish(c3) or c3_body < avg_body:
            return False, 0.0

        # Third closes below 50% of first candle
        midpoint = (c1['open'] + c1['close']) / 2
        if c3['close'] < midpoint:
            confidence = min(1.0, c3_body / (avg_body * 2))
            return True, confidence

        return False, 0.0

    def detect_three_white_soldiers(self, idx: int) -> Tuple[bool, float]:
        """
        Detect three white soldiers pattern.

        3 consecutive bullish candles, each closing higher than previous.
        Bullish continuation pattern.

        Args:
            idx: Index of the third candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 2:
            return False, 0.0

        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]

        # All three must be bullish
        if not (self._is_bullish(c1) and self._is_bullish(c2) and self._is_bullish(c3)):
            return False, 0.0

        # Each closes higher than previous
        if not (c2['close'] > c1['close'] and c3['close'] > c2['close']):
            return False, 0.0

        # Additional check: opens should be above or near previous close
        if not (c2['open'] < c2['close'] and c3['open'] < c3['close']):
            return False, 0.0

        # Confidence based on consistency of gap up and close progression
        gap1 = max(0, c2['open'] - c1['close']) / self._total_range(c1) if self._total_range(c1) > 0 else 0
        gap2 = max(0, c3['open'] - c2['close']) / self._total_range(c2) if self._total_range(c2) > 0 else 0

        confidence = min(1.0, 0.5 + (gap1 + gap2) / 2)
        return True, confidence

    def detect_three_black_crows(self, idx: int) -> Tuple[bool, float]:
        """
        Detect three black crows pattern.

        3 consecutive bearish candles, each closing lower than previous.
        Bearish continuation pattern.

        Args:
            idx: Index of the third candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 2:
            return False, 0.0

        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]

        # All three must be bearish
        if not (self._is_bearish(c1) and self._is_bearish(c2) and self._is_bearish(c3)):
            return False, 0.0

        # Each closes lower than previous
        if not (c2['close'] < c1['close'] and c3['close'] < c2['close']):
            return False, 0.0

        # Additional check: opens should be below or near previous close
        if not (c2['open'] > c2['close'] and c3['open'] > c3['close']):
            return False, 0.0

        # Confidence based on consistency of gap down and close progression
        gap1 = max(0, c1['close'] - c2['open']) / self._total_range(c1) if self._total_range(c1) > 0 else 0
        gap2 = max(0, c2['close'] - c3['open']) / self._total_range(c2) if self._total_range(c2) > 0 else 0

        confidence = min(1.0, 0.5 + (gap1 + gap2) / 2)
        return True, confidence

    def detect_piercing_pattern(self, idx: int) -> Tuple[bool, float]:
        """
        Detect piercing pattern.

        Bearish followed by bullish candle that closes above 50% of previous bearish candle.
        Bullish reversal pattern.

        Args:
            idx: Index of the bullish candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 1:
            return False, 0.0

        prev = self.candles[idx - 1]
        curr = self.candles[idx]

        # Previous bearish, current bullish
        if not self._is_bearish(prev) or not self._is_bullish(curr):
            return False, 0.0

        # Current opens below previous close (gap down)
        if curr['open'] >= prev['close']:
            return False, 0.0

        # Current closes above 50% of previous candle
        prev_midpoint = (prev['open'] + prev['close']) / 2
        if curr['close'] > prev_midpoint:
            # Confidence based on how far it pierces
            penetration = (curr['close'] - prev['close']) / (prev['open'] - prev['close'])
            confidence = min(1.0, penetration)
            return True, confidence

        return False, 0.0

    def detect_dark_cloud_cover(self, idx: int) -> Tuple[bool, float]:
        """
        Detect dark cloud cover pattern.

        Bullish followed by bearish candle that closes below 50% of previous bullish candle.
        Bearish reversal pattern.

        Args:
            idx: Index of the bearish candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        if idx < 1:
            return False, 0.0

        prev = self.candles[idx - 1]
        curr = self.candles[idx]

        # Previous bullish, current bearish
        if not self._is_bullish(prev) or not self._is_bearish(curr):
            return False, 0.0

        # Current opens above previous close (gap up)
        if curr['open'] <= prev['close']:
            return False, 0.0

        # Current closes below 50% of previous candle
        prev_midpoint = (prev['open'] + prev['close']) / 2
        if curr['close'] < prev_midpoint:
            # Confidence based on how much it penetrates
            penetration = (prev['open'] - curr['close']) / (prev['close'] - prev['open'])
            confidence = min(1.0, penetration)
            return True, confidence

        return False, 0.0

    def detect_shooting_star(self, idx: int) -> Tuple[bool, float]:
        """
        Detect shooting star pattern.

        Small body at bottom, long upper shadow, typically after uptrend.
        Bearish reversal pattern.

        Args:
            idx: Index of current candle

        Returns:
            Tuple of (pattern_detected: bool, confidence: float 0-1)
        """
        candle = self.candles[idx]
        body = self._body_size(candle)
        upper_shadow = self._upper_shadow(candle)
        lower_shadow = self._lower_shadow(candle)

        # Small body check
        avg_body = self._avg_body_size()
        if avg_body > 0 and body > avg_body * 1.5:
            return False, 0.0

        # Long upper shadow (at least 2x the body)
        if upper_shadow < body * 2:
            return False, 0.0

        # Minimal lower shadow
        if lower_shadow > body * 0.5:
            return False, 0.0

        # Check for prior uptrend
        if idx > 0:
            prev = self.candles[idx - 1]
            if prev['close'] <= prev['open']:
                # Previous was not bullish, reduce confidence
                return True, 0.6

        # Confidence based on shadow ratio
        if body > 0:
            confidence = min(1.0, (upper_shadow / body) / 5.0)
        else:
            confidence = 0.7

        return True, confidence

    # ==================== MAIN ANALYSIS METHOD ====================

    def get_candlestick_score(self) -> Dict:
        """
        Analyze the last 3 candles for all patterns and compute conviction score.

        Returns:
            Dictionary with keys:
                - score: float from -3 to +3
                - direction: "BULLISH" / "BEARISH" / "NEUTRAL"
                - patterns_found: list of dicts with:
                    - pattern_name: str
                    - type: "bullish" or "bearish"
                    - confidence: float 0-1
                    - candle_index: int (index in self.candles)
                - volume_confirmation: bool (was average volume above normal?)
        """
        if len(self.candles) < 1:
            raise ValueError("Need at least 1 candle for analysis")

        patterns_found = []
        total_score = 0.0
        bullish_count = 0
        bearish_count = 0

        # Determine how many candles to analyze (up to 3 most recent)
        analyze_count = min(3, len(self.candles))
        start_idx = len(self.candles) - analyze_count

        avg_vol = self._avg_volume(20)

        # Analyze each candle in the window
        for i in range(start_idx, len(self.candles)):
            # Pattern detection with scoring
            patterns_to_check = [
                ("Bullish Engulfing", self.detect_bullish_engulfing, 1.0, "bullish"),
                ("Bearish Engulfing", self.detect_bearish_engulfing, -1.0, "bearish"),
                ("Hammer", self.detect_hammer, 0.7, "bullish"),
                ("Inverted Hammer", self.detect_inverted_hammer, 0.5, "bullish"),
                ("Dragonfly Doji", self.detect_dragonfly_doji, 0.6, "bullish"),
                ("Gravestone Doji", self.detect_gravestone_doji, -0.6, "bearish"),
                ("Morning Star", self.detect_morning_star, 1.2, "bullish"),
                ("Evening Star", self.detect_evening_star, -1.2, "bearish"),
                ("Three White Soldiers", self.detect_three_white_soldiers, 1.5, "bullish"),
                ("Three Black Crows", self.detect_three_black_crows, -1.5, "bearish"),
                ("Piercing Pattern", self.detect_piercing_pattern, 0.6, "bullish"),
                ("Dark Cloud Cover", self.detect_dark_cloud_cover, -0.6, "bearish"),
                ("Shooting Star", self.detect_shooting_star, -0.7, "bearish"),
            ]

            for pattern_name, detect_func, base_score, pattern_type in patterns_to_check:
                detected, confidence = detect_func(i)

                if detected:
                    # Apply confidence multiplier
                    weighted_score = base_score * confidence

                    # Check for volume confirmation on pattern candle
                    pattern_vol = self.candles[i]['volume']
                    has_volume = pattern_vol > avg_vol if avg_vol > 0 else True

                    # Boost score if volume confirms the pattern
                    if has_volume and abs(weighted_score) > 0:
                        weighted_score *= 1.3 if abs(weighted_score) >= 1.0 else 1.15

                    total_score += weighted_score

                    patterns_found.append({
                        'pattern_name': pattern_name,
                        'type': pattern_type,
                        'confidence': confidence,
                        'candle_index': i,
                        'volume_confirmed': has_volume
                    })

                    if pattern_type == "bullish":
                        bullish_count += 1
                    else:
                        bearish_count += 1

            # Check for Doji (neutral pattern)
            is_doji, doji_conf = self.detect_doji(i)
            if is_doji:
                # Doji direction depends on prior trend
                doji_score = 0.0
                if i > 0:
                    prev = self.candles[i - 1]
                    doji_score = 0.1 if self._is_bullish(prev) else -0.1
                else:
                    doji_score = 0.0

                doji_score *= doji_conf
                total_score += doji_score

                patterns_found.append({
                    'pattern_name': 'Doji',
                    'type': 'neutral',
                    'confidence': doji_conf,
                    'candle_index': i,
                    'volume_confirmed': False
                })

        # Cap score between -3 and +3
        total_score = max(-3.0, min(3.0, total_score))

        # Determine direction
        if total_score > 0.2:
            direction = "BULLISH"
        elif total_score < -0.2:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # Volume confirmation: check if recent candle volume is above average
        latest_candle = self.candles[-1]
        volume_confirmed = latest_candle['volume'] > avg_vol if avg_vol > 0 else True

        return {
            'score': total_score,
            'direction': direction,
            'patterns_found': patterns_found,
            'volume_confirmation': volume_confirmed,
            'last_candle_index': len(self.candles) - 1
        }


# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    # Example usage
    sample_candles = [
        {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 99, 'close': 104, 'volume': 1000},
        {'date': '2024-01-02', 'open': 105, 'high': 110, 'low': 104, 'close': 108, 'volume': 1200},
        {'date': '2024-01-03', 'open': 108, 'high': 112, 'low': 107, 'close': 111, 'volume': 1100},
        {'date': '2024-01-04', 'open': 111, 'high': 115, 'low': 110, 'close': 114, 'volume': 1300},
    ]

    analyzer = CandlestickAnalyzer(sample_candles)
    result = analyzer.get_candlestick_score()

    print(f"Direction: {result['direction']}")
    print(f"Score: {result['score']:.2f}")
    print(f"Patterns Found: {len(result['patterns_found'])}")
    for pattern in result['patterns_found']:
        print(f"  - {pattern['pattern_name']}: {pattern['confidence']:.2f} confidence")
