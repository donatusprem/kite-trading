"""
Layer 1: Technical Analysis Module for Nifty Direction Conviction Engine

Pure Python implementation of technical indicators for OHLCV candle data.
No external dependencies beyond standard library (math, statistics).

Indicators included:
- EMA (Exponential Moving Average)
- SMA (Simple Moving Average)
- RSI (Relative Strength Index with Wilder's smoothing)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- Supertrend
- VWAP (Volume Weighted Average Price)
- Bollinger Bands
- ATR (Average True Range)
- Stochastic Oscillator
- OBV (On Balance Volume)
- Trend Momentum Score (composite scoring method)
"""

import math
from statistics import mean


class TechnicalAnalyzer:
    """
    Computes technical indicators from OHLCV candle data.

    Attributes:
        candles (list): List of dicts with keys: date, open, high, low, close, volume
        closes (list): List of closing prices
        highs (list): List of high prices
        lows (list): List of low prices
        opens (list): List of opening prices
        volumes (list): List of volumes
    """

    def __init__(self, candles):
        """
        Initialize TechnicalAnalyzer with candle data.

        Args:
            candles (list): List of dicts {date, open, high, low, close, volume}
        """
        self.candles = candles
        self.closes = [c['close'] for c in candles]
        self.highs = [c['high'] for c in candles]
        self.lows = [c['low'] for c in candles]
        self.opens = [c['open'] for c in candles]
        self.volumes = [c['volume'] for c in candles]

    def compute_ema(self, period, data=None):
        """
        Compute Exponential Moving Average.

        Args:
            period (int): EMA period
            data (list, optional): Data to compute EMA on. Defaults to self.closes

        Returns:
            list: EMA values

        Raises:
            ValueError: If period is invalid or data is insufficient
        """
        if data is None:
            data = self.closes

        if period <= 0 or period > len(data):
            raise ValueError(f"Period {period} invalid for data length {len(data)}")

        if len(data) < period:
            return []

        ema = []
        multiplier = 2.0 / (period + 1)

        # Calculate SMA for first period
        sma = sum(data[:period]) / period
        ema.append(sma)

        # Calculate EMA for remaining values
        for i in range(period, len(data)):
            ema_val = (data[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_val)

        return ema

    def compute_sma(self, period, data=None):
        """
        Compute Simple Moving Average.

        Args:
            period (int): SMA period
            data (list, optional): Data to compute SMA on. Defaults to self.closes

        Returns:
            list: SMA values

        Raises:
            ValueError: If period is invalid or data is insufficient
        """
        if data is None:
            data = self.closes

        if period <= 0 or period > len(data):
            raise ValueError(f"Period {period} invalid for data length {len(data)}")

        sma = []
        for i in range(period - 1, len(data)):
            avg = sum(data[i - period + 1:i + 1]) / period
            sma.append(avg)

        return sma

    def compute_rsi(self, period=14):
        """
        Compute Relative Strength Index using Wilder's smoothing.

        Args:
            period (int): RSI period (default 14)

        Returns:
            list: RSI values (0-100)

        Note:
            Returns empty list if insufficient data.
            Uses Wilder's method: first RS uses SMA, subsequent use EMA smoothing.
        """
        if len(self.closes) < period + 1:
            return []

        rsi = []
        gains = []
        losses = []

        # Calculate gains and losses
        for i in range(1, len(self.closes)):
            change = self.closes[i] - self.closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        # Initialize with SMA
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        # Calculate RSI for first valid point
        if avg_loss == 0:
            rsi.append(100 if avg_gain > 0 else 0)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))

        # Wilder's smoothing for subsequent values
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi.append(100 if avg_gain > 0 else 0)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))

        return rsi

    def compute_macd(self, fast=12, slow=26, signal=9):
        """
        Compute Moving Average Convergence Divergence.

        Args:
            fast (int): Fast EMA period (default 12)
            slow (int): Slow EMA period (default 26)
            signal (int): Signal line EMA period (default 9)

        Returns:
            dict: {
                'macd_line': list of MACD values,
                'signal_line': list of signal line values,
                'histogram': list of histogram values (MACD - Signal)
            }

        Note:
            Returns dict with empty lists if insufficient data.
        """
        if len(self.closes) < slow + signal:
            return {'macd_line': [], 'signal_line': [], 'histogram': []}

        fast_ema = self.compute_ema(fast)
        slow_ema = self.compute_ema(slow)

        # MACD line is difference between fast and slow EMA
        # Align to slow EMA length
        macd_line = []
        for i in range(len(slow_ema)):
            macd_line.append(fast_ema[i + (len(fast_ema) - len(slow_ema))] - slow_ema[i])

        # Signal line is EMA of MACD line
        signal_line = self.compute_ema(signal, macd_line)

        # Histogram is MACD - Signal
        histogram = []
        for i in range(len(signal_line)):
            histogram.append(macd_line[i + (len(macd_line) - len(signal_line))] - signal_line[i])

        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }

    def compute_atr(self, period=14):
        """
        Compute Average True Range.

        Args:
            period (int): ATR period (default 14)

        Returns:
            list: ATR values

        Note:
            True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
            Uses Wilder's smoothing method.
        """
        if len(self.candles) < 2:
            return []

        tr_values = []

        # Calculate True Range
        for i in range(len(self.candles)):
            high = self.highs[i]
            low = self.lows[i]
            tr = high - low

            if i > 0:
                prev_close = self.closes[i - 1]
                tr = max(tr, abs(high - prev_close), abs(low - prev_close))

            tr_values.append(tr)

        if len(tr_values) < period:
            return []

        atr = []

        # First ATR is simple average
        atr_val = sum(tr_values[:period]) / period
        atr.append(atr_val)

        # Subsequent values use Wilder's smoothing
        for i in range(period, len(tr_values)):
            atr_val = (atr_val * (period - 1) + tr_values[i]) / period
            atr.append(atr_val)

        return atr

    def compute_supertrend(self, period=10, multiplier=3.0):
        """
        Compute Supertrend indicator.

        Args:
            period (int): ATR period (default 10)
            multiplier (float): ATR multiplier for bands (default 3.0)

        Returns:
            dict: {
                'supertrend': list of supertrend values,
                'direction': list of direction (1 for bullish, -1 for bearish)
            }

        Note:
            Supertrend uses Basic Upper Band (hl2 + atr*multiplier)
            and Basic Lower Band (hl2 - atr*multiplier)
            Direction: 1 = price above supertrend (bullish), -1 = below (bearish)
        """
        if len(self.candles) < period + 1:
            return {'supertrend': [], 'direction': []}

        atr = self.compute_atr(period)
        if not atr:
            return {'supertrend': [], 'direction': []}

        supertrend = []
        direction = []

        # Start from where ATR is available
        for i in range(len(atr)):
            idx = i + (len(self.candles) - len(atr))
            hl2 = (self.highs[idx] + self.lows[idx]) / 2

            basic_ub = hl2 + multiplier * atr[i]
            basic_lb = hl2 - multiplier * atr[i]

            # Final upper and lower bands
            if i == 0:
                final_ub = basic_ub
                final_lb = basic_lb
            else:
                final_ub = basic_ub if basic_ub < supertrend[i - 1] or self.closes[idx - 1] > supertrend[i - 1] else supertrend[i - 1]
                final_lb = basic_lb if basic_lb > supertrend[i - 1] or self.closes[idx - 1] < supertrend[i - 1] else supertrend[i - 1]

            # Supertrend is the upper or lower band
            if i == 0:
                st = final_lb if self.closes[idx] <= final_ub else final_ub
                dir_val = -1 if self.closes[idx] <= final_ub else 1
            else:
                if supertrend[i - 1] == supertrend[i - 1]:  # Previous was upper band
                    st = final_ub
                    dir_val = 1 if self.closes[idx] >= final_ub else -1
                else:
                    st = final_lb
                    dir_val = -1 if self.closes[idx] <= final_lb else 1

            supertrend.append(final_lb if dir_val == -1 else final_ub)
            direction.append(dir_val)

        return {'supertrend': supertrend, 'direction': direction}

    def compute_vwap(self):
        """
        Compute Volume Weighted Average Price.

        Args:
            None (uses self.candles)

        Returns:
            list: VWAP values for each candle

        Formula:
            VWAP = Cumulative(TP * Volume) / Cumulative(Volume)
            where TP (Typical Price) = (High + Low + Close) / 3
        """
        if not self.candles:
            return []

        vwap = []
        cum_vol = 0
        cum_tp_vol = 0

        for i in range(len(self.candles)):
            tp = (self.highs[i] + self.lows[i] + self.closes[i]) / 3
            cum_tp_vol += tp * self.volumes[i]
            cum_vol += self.volumes[i]

            if cum_vol > 0:
                vwap.append(cum_tp_vol / cum_vol)
            else:
                vwap.append(tp)

        return vwap

    def compute_bollinger_bands(self, period=20, std_dev=2):
        """
        Compute Bollinger Bands.

        Args:
            period (int): Period for middle band (SMA) (default 20)
            std_dev (float): Number of standard deviations (default 2)

        Returns:
            dict: {
                'upper': list of upper band values,
                'middle': list of middle band values (SMA),
                'lower': list of lower band values
            }

        Formula:
            Middle = SMA(period)
            Upper = Middle + std_dev * StdDev
            Lower = Middle - std_dev * StdDev
        """
        if len(self.closes) < period:
            return {'upper': [], 'middle': [], 'lower': []}

        middle = self.compute_sma(period)
        upper = []
        lower = []

        for i in range(period - 1, len(self.closes)):
            subset = self.closes[i - period + 1:i + 1]
            mean_val = sum(subset) / period
            variance = sum((x - mean_val) ** 2 for x in subset) / period
            std = math.sqrt(variance)

            band_offset = std_dev * std
            upper.append(middle[i - (period - 1)] + band_offset)
            lower.append(middle[i - (period - 1)] - band_offset)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    def compute_stochastic(self, k_period=14, d_period=3):
        """
        Compute Stochastic Oscillator.

        Args:
            k_period (int): Period for %K calculation (default 14)
            d_period (int): Period for %D (SMA of %K) (default 3)

        Returns:
            dict: {
                'k': list of %K values (0-100),
                'd': list of %D values (0-100)
            }

        Formula:
            %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
            %D = SMA of %K
        """
        if len(self.closes) < k_period:
            return {'k': [], 'd': []}

        k_values = []

        for i in range(k_period - 1, len(self.closes)):
            subset_high = self.highs[i - k_period + 1:i + 1]
            subset_low = self.lows[i - k_period + 1:i + 1]

            highest = max(subset_high)
            lowest = min(subset_low)

            if highest - lowest == 0:
                k_val = 50
            else:
                k_val = 100 * (self.closes[i] - lowest) / (highest - lowest)

            k_values.append(k_val)

        # Calculate %D as SMA of %K
        d_values = []
        for i in range(d_period - 1, len(k_values)):
            d_val = sum(k_values[i - d_period + 1:i + 1]) / d_period
            d_values.append(d_val)

        return {
            'k': k_values,
            'd': d_values
        }

    def compute_obv(self):
        """
        Compute On Balance Volume.

        Args:
            None (uses self.candles)

        Returns:
            list: OBV values

        Formula:
            If Close > Previous Close: OBV = Previous OBV + Volume
            If Close < Previous Close: OBV = Previous OBV - Volume
            If Close = Previous Close: OBV = Previous OBV
        """
        if not self.candles:
            return []

        obv = [self.volumes[0]]

        for i in range(1, len(self.candles)):
            if self.closes[i] > self.closes[i - 1]:
                obv.append(obv[-1] + self.volumes[i])
            elif self.closes[i] < self.closes[i - 1]:
                obv.append(obv[-1] - self.volumes[i])
            else:
                obv.append(obv[-1])

        return obv

    def compute_adx(self, period=14):
        """
        Compute Average Directional Index (ADX) with directional indicators.

        Args:
            period (int): ADX period (default 14)

        Returns:
            dict: {
                'adx': list of ADX values,
                'plus_di': list of +DI values,
                'minus_di': list of -DI values
            }

        Note:
            ADX measures trend strength (0-100).
            +DI and -DI measure directional movement.
            Uses Wilder's smoothing method.
        """
        if len(self.candles) < period + 1:
            return {'adx': [], 'plus_di': [], 'minus_di': []}

        plus_dm = []
        minus_dm = []
        tr_values = []

        # Calculate DM and TR
        for i in range(1, len(self.candles)):
            high_diff = self.highs[i] - self.highs[i - 1]
            low_diff = self.lows[i - 1] - self.lows[i]

            plus_d = 0
            minus_d = 0

            if high_diff > 0 and high_diff > low_diff:
                plus_d = high_diff
            if low_diff > 0 and low_diff > high_diff:
                minus_d = low_diff

            plus_dm.append(plus_d)
            minus_dm.append(minus_d)

            # True Range
            high = self.highs[i]
            low = self.lows[i]
            prev_close = self.closes[i - 1]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)

        if len(tr_values) < period:
            return {'adx': [], 'plus_di': [], 'minus_di': []}

        # Initialize with sums
        plus_dm_sum = sum(plus_dm[:period])
        minus_dm_sum = sum(minus_dm[:period])
        tr_sum = sum(tr_values[:period])

        adx_values = []
        plus_di_values = []
        minus_di_values = []

        # Calculate DI values
        if tr_sum > 0:
            plus_di = 100 * plus_dm_sum / tr_sum
            minus_di = 100 * minus_dm_sum / tr_sum
        else:
            plus_di = 0
            minus_di = 0

        plus_di_values.append(plus_di)
        minus_di_values.append(minus_di)

        # DX calculation
        di_sum = plus_di + minus_di
        if di_sum > 0:
            dx = 100 * abs(plus_di - minus_di) / di_sum
        else:
            dx = 0

        adx = dx
        adx_values.append(adx)

        # Subsequent values with Wilder's smoothing
        for i in range(period, len(plus_dm)):
            plus_dm_sum = plus_dm_sum * (period - 1) / period + plus_dm[i]
            minus_dm_sum = minus_dm_sum * (period - 1) / period + minus_dm[i]
            tr_sum = tr_sum * (period - 1) / period + tr_values[i]

            if tr_sum > 0:
                plus_di = 100 * plus_dm_sum / tr_sum
                minus_di = 100 * minus_dm_sum / tr_sum
            else:
                plus_di = 0
                minus_di = 0

            plus_di_values.append(plus_di)
            minus_di_values.append(minus_di)

            di_sum = plus_di + minus_di
            if di_sum > 0:
                dx = 100 * abs(plus_di - minus_di) / di_sum
            else:
                dx = 0

            adx = (adx * (period - 1) + dx) / period
            adx_values.append(adx)

        return {
            'adx': adx_values,
            'plus_di': plus_di_values,
            'minus_di': minus_di_values
        }

    def get_trend_momentum_score(self):
        """
        Main scoring method: computes composite trend momentum score from all indicators.

        Returns:
            dict: {
                'score': float between -5 and +5,
                'direction': str ('BULLISH', 'BEARISH', or 'NEUTRAL'),
                'signals': list of signal dicts with keys:
                    - 'name': signal name
                    - 'value': current value description
                    - 'signal': 'BULLISH', 'BEARISH', or 'NEUTRAL'
                    - 'weight': contribution weight
                'details': dict with key indicator values
            }

        Scoring Logic:
            - EMA Alignment (9>21>50): +1, reverse: -1
            - EMA 9/21 Crossover: ±0.5
            - RSI >60: +0.5, >70: +0.3 caution, <40: -0.5, <30: -0.3
            - MACD histogram positive+rising: +1, negative+falling: -1, crossover: ±0.5
            - ADX >25 amplifies by 1.2x, <20 dampens by 0.8x
            - Supertrend green: +1, red: -1
            - VWAP price above: +0.5, below: -0.5
            - Stochastic <20: +0.3 (oversold), >80: -0.3 (overbought)

        Edge Cases:
            - Returns neutral score if insufficient data
            - Handles division by zero gracefully
        """
        # Check minimum data requirement
        if len(self.candles) < 20:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'signals': [{'name': 'Data Insufficient', 'value': f'{len(self.candles)} candles', 'signal': 'NEUTRAL', 'weight': 0}],
                'details': {}
            }

        signals = []
        score = 0

        # 1. EMA Alignment (9, 21, 50)
        ema_9 = self.compute_ema(9)
        ema_21 = self.compute_ema(21)
        ema_50 = self.compute_ema(50)

        if ema_9 and ema_21 and ema_50:
            ema_9_last = ema_9[-1]
            ema_21_last = ema_21[-1]
            ema_50_last = ema_50[-1]

            if ema_9_last > ema_21_last > ema_50_last:
                signals.append({
                    'name': 'EMA Alignment',
                    'value': f'{ema_9_last:.2f} > {ema_21_last:.2f} > {ema_50_last:.2f}',
                    'signal': 'BULLISH',
                    'weight': 1.0
                })
                score += 1.0
            elif ema_9_last < ema_21_last < ema_50_last:
                signals.append({
                    'name': 'EMA Alignment',
                    'value': f'{ema_9_last:.2f} < {ema_21_last:.2f} < {ema_50_last:.2f}',
                    'signal': 'BEARISH',
                    'weight': 1.0
                })
                score -= 1.0
            else:
                signals.append({
                    'name': 'EMA Alignment',
                    'value': 'Mixed',
                    'signal': 'NEUTRAL',
                    'weight': 0.5
                })

        # 2. EMA 9/21 Crossover
        if len(ema_9) > 1 and len(ema_21) > 1:
            if ema_9[-2] < ema_21[-2] and ema_9[-1] > ema_21[-1]:
                signals.append({
                    'name': 'EMA 9/21 Crossover',
                    'value': 'Golden Cross',
                    'signal': 'BULLISH',
                    'weight': 0.5
                })
                score += 0.5
            elif ema_9[-2] > ema_21[-2] and ema_9[-1] < ema_21[-1]:
                signals.append({
                    'name': 'EMA 9/21 Crossover',
                    'value': 'Death Cross',
                    'signal': 'BEARISH',
                    'weight': 0.5
                })
                score -= 0.5

        # 3. RSI Analysis
        rsi = self.compute_rsi(14)
        if rsi:
            rsi_last = rsi[-1]

            if rsi_last > 70:
                signals.append({
                    'name': 'RSI',
                    'value': f'{rsi_last:.2f} (Overbought)',
                    'signal': 'BEARISH',
                    'weight': 0.3
                })
                score -= 0.3
            elif rsi_last > 60:
                signals.append({
                    'name': 'RSI',
                    'value': f'{rsi_last:.2f} (Strong)',
                    'signal': 'BULLISH',
                    'weight': 0.5
                })
                score += 0.5
            elif rsi_last < 30:
                signals.append({
                    'name': 'RSI',
                    'value': f'{rsi_last:.2f} (Oversold)',
                    'signal': 'BULLISH',
                    'weight': 0.3
                })
                score += 0.3
            elif rsi_last < 40:
                signals.append({
                    'name': 'RSI',
                    'value': f'{rsi_last:.2f} (Weak)',
                    'signal': 'BEARISH',
                    'weight': 0.5
                })
                score -= 0.5

        # 4. MACD Analysis
        macd = self.compute_macd()
        if macd['histogram']:
            hist_last = macd['histogram'][-1]

            if len(macd['histogram']) > 1:
                hist_prev = macd['histogram'][-2]

                if hist_last > 0 and hist_last > hist_prev:
                    signals.append({
                        'name': 'MACD',
                        'value': f'Histogram positive & rising ({hist_last:.4f})',
                        'signal': 'BULLISH',
                        'weight': 1.0
                    })
                    score += 1.0
                elif hist_last < 0 and hist_last < hist_prev:
                    signals.append({
                        'name': 'MACD',
                        'value': f'Histogram negative & falling ({hist_last:.4f})',
                        'signal': 'BEARISH',
                        'weight': 1.0
                    })
                    score -= 1.0
                elif len(macd['macd_line']) > 1 and len(macd['signal_line']) > 1:
                    if macd['macd_line'][-2] < macd['signal_line'][-2] and macd['macd_line'][-1] > macd['signal_line'][-1]:
                        signals.append({
                            'name': 'MACD Crossover',
                            'value': 'MACD crossed above signal',
                            'signal': 'BULLISH',
                            'weight': 0.5
                        })
                        score += 0.5
                    elif macd['macd_line'][-2] > macd['signal_line'][-2] and macd['macd_line'][-1] < macd['signal_line'][-1]:
                        signals.append({
                            'name': 'MACD Crossover',
                            'value': 'MACD crossed below signal',
                            'signal': 'BEARISH',
                            'weight': 0.5
                        })
                        score -= 0.5

        # 5. ADX Analysis
        adx_data = self.compute_adx()
        adx_amplification = 1.0

        if adx_data['adx']:
            adx_last = adx_data['adx'][-1]

            if adx_last > 25:
                adx_amplification = 1.2
                signals.append({
                    'name': 'ADX Strength',
                    'value': f'{adx_last:.2f} (Strong Trend)',
                    'signal': 'NEUTRAL',
                    'weight': 0
                })
            elif adx_last < 20:
                adx_amplification = 0.8
                signals.append({
                    'name': 'ADX Strength',
                    'value': f'{adx_last:.2f} (Weak Trend)',
                    'signal': 'NEUTRAL',
                    'weight': 0
                })

        # 6. Supertrend
        supertrend = self.compute_supertrend()
        if supertrend['direction']:
            st_dir = supertrend['direction'][-1]

            if st_dir == 1:
                signals.append({
                    'name': 'Supertrend',
                    'value': 'Bullish (Green)',
                    'signal': 'BULLISH',
                    'weight': 1.0
                })
                score += 1.0 * adx_amplification
            else:
                signals.append({
                    'name': 'Supertrend',
                    'value': 'Bearish (Red)',
                    'signal': 'BEARISH',
                    'weight': 1.0
                })
                score -= 1.0 * adx_amplification

        # 7. VWAP
        vwap = self.compute_vwap()
        if vwap:
            current_price = self.closes[-1]
            vwap_last = vwap[-1]

            if current_price > vwap_last:
                signals.append({
                    'name': 'VWAP',
                    'value': f'{current_price:.2f} > {vwap_last:.2f}',
                    'signal': 'BULLISH',
                    'weight': 0.5
                })
                score += 0.5
            else:
                signals.append({
                    'name': 'VWAP',
                    'value': f'{current_price:.2f} < {vwap_last:.2f}',
                    'signal': 'BEARISH',
                    'weight': 0.5
                })
                score -= 0.5

        # 8. Stochastic
        stoch = self.compute_stochastic()
        if stoch['k']:
            k_last = stoch['k'][-1]

            if k_last < 20:
                signals.append({
                    'name': 'Stochastic %K',
                    'value': f'{k_last:.2f} (Oversold)',
                    'signal': 'BULLISH',
                    'weight': 0.3
                })
                score += 0.3
            elif k_last > 80:
                signals.append({
                    'name': 'Stochastic %K',
                    'value': f'{k_last:.2f} (Overbought)',
                    'signal': 'BEARISH',
                    'weight': 0.3
                })
                score -= 0.3

        # Clamp score to -5 to +5 range
        score = max(-5, min(5, score))

        # Determine direction
        if score > 0.5:
            direction = 'BULLISH'
        elif score < -0.5:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'

        # Build details dict
        details = {
            'current_price': self.closes[-1] if self.closes else 0,
            'ema_9': ema_9[-1] if ema_9 else 0,
            'ema_21': ema_21[-1] if ema_21 else 0,
            'ema_50': ema_50[-1] if ema_50 else 0,
            'rsi': rsi[-1] if rsi else 0,
            'macd_histogram': macd['histogram'][-1] if macd['histogram'] else 0,
            'adx': adx_data['adx'][-1] if adx_data['adx'] else 0,
            'plus_di': adx_data['plus_di'][-1] if adx_data['plus_di'] else 0,
            'minus_di': adx_data['minus_di'][-1] if adx_data['minus_di'] else 0,
            'supertrend_direction': supertrend['direction'][-1] if supertrend['direction'] else 0,
            'vwap': vwap[-1] if vwap else 0
        }

        return {
            'score': score,
            'direction': direction,
            'signals': signals,
            'details': details
        }
