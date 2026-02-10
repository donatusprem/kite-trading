#!/usr/bin/env python3
"""
SIGNAL ENGINE — Quantitative Indicator Suite
VWAP, RSI with Divergence Detection, Supertrend, ATR-based Stops,
Volume Profile, and Multi-Timeframe Confluence Scoring.

This module supplements the existing MarketScanner by adding
institutional-grade indicators that improve signal quality.
"""

import sys
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import deque

SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EXECUTION_DIR))

from kite_client import KiteMCPClient


# ══════════════════════════════════════════════════════════════════
# Indicator Functions (Pure NumPy — no pandas dependency)
# ══════════════════════════════════════════════════════════════════

def calc_vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
              volumes: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    VWAP + Upper/Lower deviation bands.
    Institutional traders use VWAP as fair value — price above = bullish, below = bearish.
    """
    typical_price = (highs + lows + closes) / 3
    cum_tp_vol = np.cumsum(typical_price * volumes)
    cum_vol = np.cumsum(volumes)
    
    vwap = np.where(cum_vol > 0, cum_tp_vol / cum_vol, typical_price)
    
    # Standard deviation bands (1σ)
    cum_tp2_vol = np.cumsum(typical_price**2 * volumes)
    variance = np.where(cum_vol > 0, (cum_tp2_vol / cum_vol) - vwap**2, 0)
    variance = np.maximum(variance, 0)  # Prevent negative variance
    std = np.sqrt(variance)
    
    upper_band = vwap + std
    lower_band = vwap - std
    
    return vwap, upper_band, lower_band


def calc_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """RSI using Wilder's smoothing (exponential moving average of gains/losses)."""
    if len(closes) < period + 1:
        return np.full_like(closes, 50.0)
    
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    
    # Initial SMA
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rsi = np.full(len(closes), 50.0)
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i + 1] = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi


def detect_rsi_divergence(closes: np.ndarray, rsi: np.ndarray,
                          lookback: int = 20) -> Dict:
    """
    Detect bullish/bearish RSI divergence.
    - Bullish: Price makes lower low, RSI makes higher low → reversal up
    - Bearish: Price makes higher high, RSI makes lower high → reversal down
    """
    if len(closes) < lookback + 5:
        return {"type": "none", "strength": 0}
    
    recent = closes[-lookback:]
    recent_rsi = rsi[-lookback:]
    
    # Find swing lows/highs (simple method — look for local minima/maxima)
    price_lows = []
    price_highs = []
    rsi_lows = []
    rsi_highs = []
    
    for i in range(2, len(recent) - 2):
        if recent[i] <= recent[i-1] and recent[i] <= recent[i+1] and recent[i] <= recent[i-2]:
            price_lows.append((i, recent[i], recent_rsi[i]))
        if recent[i] >= recent[i-1] and recent[i] >= recent[i+1] and recent[i] >= recent[i-2]:
            price_highs.append((i, recent[i], recent_rsi[i]))
    
    # Bullish divergence: last two lows — price lower but RSI higher
    if len(price_lows) >= 2:
        prev_low = price_lows[-2]
        curr_low = price_lows[-1]
        
        if curr_low[1] < prev_low[1] and curr_low[2] > prev_low[2]:
            strength = abs(curr_low[2] - prev_low[2])
            return {
                "type": "bullish_divergence",
                "strength": min(round(strength, 1), 30),
                "note": f"Price lower low but RSI higher low → reversal likely"
            }
    
    # Bearish divergence: last two highs — price higher but RSI lower
    if len(price_highs) >= 2:
        prev_high = price_highs[-2]
        curr_high = price_highs[-1]
        
        if curr_high[1] > prev_high[1] and curr_high[2] < prev_high[2]:
            strength = abs(prev_high[2] - curr_high[2])
            return {
                "type": "bearish_divergence",
                "strength": min(round(strength, 1), 30),
                "note": f"Price higher high but RSI lower high → top forming"
            }
    
    return {"type": "none", "strength": 0}


def calc_supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                    period: int = 10, multiplier: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Supertrend indicator — trend-following filter.
    Returns (supertrend_values, direction) where direction 1=up, -1=down.
    """
    n = len(closes)
    if n < period + 1:
        return np.full(n, closes[-1] if n > 0 else 0), np.ones(n)
    
    # ATR calculation
    tr = np.maximum(
        highs - lows,
        np.maximum(
            np.abs(highs - np.roll(closes, 1)),
            np.abs(lows - np.roll(closes, 1))
        )
    )
    tr[0] = highs[0] - lows[0]
    
    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    
    # Basic upper/lower bands
    hl2 = (highs + lows) / 2
    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr
    
    # Final bands with trend logic
    upper_band = np.zeros(n)
    lower_band = np.zeros(n)
    supertrend = np.zeros(n)
    direction = np.ones(n)  # 1 = uptrend, -1 = downtrend
    
    upper_band[0] = basic_upper[0]
    lower_band[0] = basic_lower[0]
    
    for i in range(1, n):
        # Upper band
        if basic_upper[i] < upper_band[i-1] or closes[i-1] > upper_band[i-1]:
            upper_band[i] = basic_upper[i]
        else:
            upper_band[i] = upper_band[i-1]
        
        # Lower band
        if basic_lower[i] > lower_band[i-1] or closes[i-1] < lower_band[i-1]:
            lower_band[i] = basic_lower[i]
        else:
            lower_band[i] = lower_band[i-1]
        
        # Direction
        if direction[i-1] == 1:
            if closes[i] < lower_band[i]:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            else:
                direction[i] = 1
                supertrend[i] = lower_band[i]
        else:
            if closes[i] > upper_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
    
    return supertrend, direction


def calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
             period: int = 14) -> np.ndarray:
    """Average True Range — volatility measure for dynamic stop-losses."""
    n = len(closes)
    if n < 2:
        return np.array([highs[0] - lows[0]] if n > 0 else [0])
    
    tr = np.maximum(
        highs - lows,
        np.maximum(
            np.abs(highs - np.roll(closes, 1)),
            np.abs(lows - np.roll(closes, 1))
        )
    )
    tr[0] = highs[0] - lows[0]
    
    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period]) if n >= period else np.mean(tr)
    for i in range(max(period, 1), n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    
    return atr


def calc_ema(values: np.ndarray, period: int) -> np.ndarray:
    """Exponential Moving Average."""
    ema = np.zeros_like(values)
    if len(values) == 0:
        return ema
    multiplier = 2.0 / (period + 1)
    ema[0] = values[0]
    for i in range(1, len(values)):
        ema[i] = values[i] * multiplier + ema[i-1] * (1 - multiplier)
    return ema


def calc_volume_profile(closes: np.ndarray, volumes: np.ndarray,
                        n_bins: int = 20) -> Dict:
    """
    Volume Profile — identifies POC (Point of Control), VAH, VAL.
    POC = price level with highest volume — where big money trades.
    """
    if len(closes) < 5:
        return {"poc": closes[-1] if len(closes) > 0 else 0, "vah": 0, "val": 0}
    
    price_min = float(np.min(closes))
    price_max = float(np.max(closes))
    
    if price_max == price_min:
        return {"poc": price_min, "vah": price_max, "val": price_min}
    
    bin_edges = np.linspace(price_min, price_max, n_bins + 1)
    bin_volumes = np.zeros(n_bins)
    
    for i in range(len(closes)):
        bin_idx = int((closes[i] - price_min) / (price_max - price_min) * (n_bins - 1))
        bin_idx = min(max(bin_idx, 0), n_bins - 1)
        bin_volumes[bin_idx] += volumes[i]
    
    # POC = bin with max volume
    poc_idx = int(np.argmax(bin_volumes))
    poc = float((bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2)
    
    # Value Area: 70% of total volume centered around POC
    total_vol = float(np.sum(bin_volumes))
    target_vol = total_vol * 0.70
    
    low_idx = poc_idx
    high_idx = poc_idx
    area_vol = float(bin_volumes[poc_idx])
    
    while area_vol < target_vol and (low_idx > 0 or high_idx < n_bins - 1):
        expand_low = bin_volumes[low_idx - 1] if low_idx > 0 else 0
        expand_high = bin_volumes[high_idx + 1] if high_idx < n_bins - 1 else 0
        
        if expand_low >= expand_high and low_idx > 0:
            low_idx -= 1
            area_vol += float(expand_low)
        elif high_idx < n_bins - 1:
            high_idx += 1
            area_vol += float(expand_high)
        else:
            break
    
    val = float(bin_edges[low_idx])      # Value Area Low
    vah = float(bin_edges[high_idx + 1])  # Value Area High
    
    return {"poc": round(poc, 2), "vah": round(vah, 2), "val": round(val, 2)}


# ══════════════════════════════════════════════════════════════════
# Signal Engine — Combines all indicators into one analysis
# ══════════════════════════════════════════════════════════════════

class SignalEngine:
    """
    Quantitative signal generator that computes institutional-grade
    indicators and produces a confluence score for any instrument.
    """

    def __init__(self, client: Optional[KiteMCPClient] = None):
        self.client = client

    def analyze(self, candles: List[Dict], symbol: str = "",
                timeframe: str = "15min") -> Dict:
        """
        Run full indicator suite on OHLCV candle data.
        
        Args:
            candles: List of dicts with keys: open, high, low, close, volume
            symbol: Instrument symbol for reporting
            timeframe: '5min', '15min', '1hr', 'day'
            
        Returns:
            Comprehensive analysis dict with indicator values and signal
        """
        if not candles or len(candles) < 20:
            return {"error": "Need at least 20 candles", "signal": "NEUTRAL"}

        # Convert to numpy arrays
        opens = np.array([c.get("open", 0) for c in candles], dtype=float)
        highs = np.array([c.get("high", 0) for c in candles], dtype=float)
        lows = np.array([c.get("low", 0) for c in candles], dtype=float)
        closes = np.array([c.get("close", 0) for c in candles], dtype=float)
        volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)

        current_price = float(closes[-1])
        
        # ── 1. VWAP ──
        vwap, vwap_upper, vwap_lower = calc_vwap(highs, lows, closes, volumes)
        vwap_current = float(vwap[-1])
        vwap_position = "above" if current_price > vwap_current else "below"
        vwap_distance_pct = ((current_price - vwap_current) / vwap_current * 100) if vwap_current > 0 else 0
        
        # ── 2. RSI ──
        rsi = calc_rsi(closes, 14)
        rsi_current = float(rsi[-1])
        rsi_zone = (
            "oversold" if rsi_current < 30 else
            "overbought" if rsi_current > 70 else
            "neutral"
        )
        
        # ── 3. RSI Divergence ──
        divergence = detect_rsi_divergence(closes, rsi, lookback=20)
        
        # ── 4. Supertrend ──
        st_values, st_direction = calc_supertrend(highs, lows, closes, 10, 3.0)
        supertrend_signal = "BULLISH" if st_direction[-1] == 1 else "BEARISH"
        supertrend_value = float(st_values[-1])
        
        # ── 5. ATR ──
        atr = calc_atr(highs, lows, closes, 14)
        atr_current = float(atr[-1])
        atr_pct = (atr_current / current_price * 100) if current_price > 0 else 0
        
        # ATR-based dynamic stop loss
        atr_sl_long = current_price - 2.0 * atr_current
        atr_sl_short = current_price + 2.0 * atr_current
        
        # ── 6. EMAs ──
        ema_9 = calc_ema(closes, 9)
        ema_21 = calc_ema(closes, 21)
        ema_50 = calc_ema(closes, 50) if len(closes) >= 50 else calc_ema(closes, len(closes))
        
        ema_trend = "BULLISH" if float(ema_9[-1]) > float(ema_21[-1]) > float(ema_50[-1]) else (
            "BEARISH" if float(ema_9[-1]) < float(ema_21[-1]) < float(ema_50[-1]) else
            "MIXED"
        )
        
        # ── 7. Volume Profile ──
        vp = calc_volume_profile(closes[-50:], volumes[-50:])
        
        # ── 8. Volume Analysis ──
        avg_vol_20 = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
        current_vol = float(volumes[-1])
        vol_ratio = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
        volume_surge = vol_ratio > 1.5
        
        # ══════════════════════════════════════════════════════════
        # Confluence Scoring
        # ══════════════════════════════════════════════════════════
        
        bull_points = 0
        bear_points = 0
        signals = []
        
        # VWAP position (weight: 15)
        if vwap_position == "above" and vwap_distance_pct < 1.5:
            bull_points += 15
            signals.append("Price holding above VWAP")
        elif vwap_position == "above" and vwap_distance_pct >= 1.5:
            bull_points += 10
            signals.append("Price extended above VWAP")
        elif vwap_position == "below" and abs(vwap_distance_pct) < 1.5:
            bear_points += 15
            signals.append("Price below VWAP")
        else:
            bear_points += 10
            signals.append("Price far below VWAP — oversold bounce?")
        
        # RSI (weight: 15)
        if rsi_zone == "oversold":
            bull_points += 15
            signals.append(f"RSI oversold ({rsi_current:.0f}) — bounce setup")
        elif rsi_zone == "overbought":
            bear_points += 15
            signals.append(f"RSI overbought ({rsi_current:.0f}) — exhaustion")
        elif rsi_current > 50:
            bull_points += 8
        else:
            bear_points += 8
        
        # RSI Divergence (weight: 20 — very high signal quality)
        if divergence["type"] == "bullish_divergence":
            bull_points += 20
            signals.append(f"🔥 Bullish RSI Divergence (strength: {divergence['strength']})")
        elif divergence["type"] == "bearish_divergence":
            bear_points += 20
            signals.append(f"🔥 Bearish RSI Divergence (strength: {divergence['strength']})")
        
        # Supertrend (weight: 15)
        if supertrend_signal == "BULLISH":
            bull_points += 15
            signals.append("Supertrend bullish")
        else:
            bear_points += 15
            signals.append("Supertrend bearish")
        
        # EMA alignment (weight: 15)
        if ema_trend == "BULLISH":
            bull_points += 15
            signals.append("EMA 9 > 21 > 50 — strong uptrend")
        elif ema_trend == "BEARISH":
            bear_points += 15
            signals.append("EMA 9 < 21 < 50 — strong downtrend")
        else:
            signals.append("EMA mixed — no clear trend")
        
        # Volume confirmation (weight: 10)
        if volume_surge:
            if bull_points > bear_points:
                bull_points += 10
            else:
                bear_points += 10
            signals.append(f"Volume surge ({vol_ratio:.1f}x avg)")
        
        # Volume Profile — price near POC (weight: 10)
        poc_distance = abs(current_price - vp["poc"]) / current_price * 100 if current_price > 0 else 100
        if poc_distance < 0.5:
            bull_points += 5
            bear_points += 5
            signals.append(f"Price at POC ({vp['poc']}) — high-volume zone")
        
        # ── Final Signal ──
        total = bull_points + bear_points
        if total == 0:
            total = 1
        
        if bull_points > bear_points:
            direction = "LONG"
            confidence = round(bull_points / total * 100)
            trend_strength = "strong" if confidence > 70 else "moderate" if confidence > 55 else "weak"
        elif bear_points > bull_points:
            direction = "SHORT"
            confidence = round(bear_points / total * 100)
            trend_strength = "strong" if confidence > 70 else "moderate" if confidence > 55 else "weak"
        else:
            direction = "NEUTRAL"
            confidence = 50
            trend_strength = "weak"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": round(current_price, 2),
            "direction": direction,
            "confidence": confidence,
            "trend_strength": trend_strength,
            "signals": signals,
            
            # Individual indicators
            "vwap": {
                "value": round(vwap_current, 2),
                "upper": round(float(vwap_upper[-1]), 2),
                "lower": round(float(vwap_lower[-1]), 2),
                "position": vwap_position,
                "distance_pct": round(vwap_distance_pct, 2),
            },
            "rsi": {
                "value": round(rsi_current, 1),
                "zone": rsi_zone,
                "divergence": divergence,
            },
            "supertrend": {
                "signal": supertrend_signal,
                "value": round(supertrend_value, 2),
            },
            "atr": {
                "value": round(atr_current, 2),
                "pct": round(atr_pct, 2),
                "sl_long": round(atr_sl_long, 2),
                "sl_short": round(atr_sl_short, 2),
            },
            "ema": {
                "ema_9": round(float(ema_9[-1]), 2),
                "ema_21": round(float(ema_21[-1]), 2),
                "ema_50": round(float(ema_50[-1]), 2),
                "trend": ema_trend,
            },
            "volume_profile": vp,
            "volume": {
                "current": round(current_vol, 0),
                "avg_20": round(avg_vol_20, 0),
                "ratio": round(vol_ratio, 2),
                "surge": volume_surge,
            },
            
            # Scoring
            "score_breakdown": {
                "bull_points": bull_points,
                "bear_points": bear_points,
            },
        }

    def multi_timeframe_analysis(self, candles_5m: List[Dict],
                                  candles_15m: List[Dict],
                                  candles_1hr: List[Dict],
                                  symbol: str = "") -> Dict:
        """
        Multi-timeframe confluence — strongest signals come from alignment
        across 5min, 15min, and 1hr timeframes.
        """
        analysis_5m = self.analyze(candles_5m, symbol, "5min") if candles_5m else {}
        analysis_15m = self.analyze(candles_15m, symbol, "15min") if candles_15m else {}
        analysis_1hr = self.analyze(candles_1hr, symbol, "1hr") if candles_1hr else {}

        directions = []
        confidences = []
        strengths = []
        
        for analysis, weight in [(analysis_1hr, 3), (analysis_15m, 2), (analysis_5m, 1)]:
            if not analysis or "error" in analysis:
                continue
            d = analysis.get("direction", "NEUTRAL")
            c = analysis.get("confidence", 50)
            s = analysis.get("trend_strength", "weak")
            
            for _ in range(weight):
                directions.append(d)
                confidences.append(c)
                strengths.append(s)

        if not directions:
            return {"signal": "NEUTRAL", "confluence": 0, "mtf_aligned": False}

        # Count direction votes
        long_votes = directions.count("LONG")
        short_votes = directions.count("SHORT")
        total_votes = len(directions)
        
        if long_votes > short_votes:
            mtf_direction = "LONG"
            alignment_pct = long_votes / total_votes * 100
        elif short_votes > long_votes:
            mtf_direction = "SHORT"
            alignment_pct = short_votes / total_votes * 100
        else:
            mtf_direction = "NEUTRAL"
            alignment_pct = 50

        # Check if all timeframes agree
        tf_dirs = [
            analysis_5m.get("direction", "NEUTRAL") if analysis_5m else "NEUTRAL",
            analysis_15m.get("direction", "NEUTRAL") if analysis_15m else "NEUTRAL",
            analysis_1hr.get("direction", "NEUTRAL") if analysis_1hr else "NEUTRAL",
        ]
        all_aligned = len(set(d for d in tf_dirs if d != "NEUTRAL")) <= 1

        # Confluence score
        avg_confidence = sum(confidences) / len(confidences)
        strong_count = strengths.count("strong")
        
        confluence_score = avg_confidence
        if all_aligned:
            confluence_score = min(100, confluence_score + 15)
        if strong_count >= 2:
            confluence_score = min(100, confluence_score + 10)

        # Determine overall trend strength
        if confluence_score >= 80 and all_aligned:
            overall_strength = "strong"
        elif confluence_score >= 60:
            overall_strength = "moderate"
        else:
            overall_strength = "weak"

        return {
            "signal": mtf_direction,
            "confluence": round(confluence_score),
            "mtf_aligned": all_aligned,
            "alignment_pct": round(alignment_pct),
            "trend_strength": overall_strength,
            "timeframes": {
                "5min": {"direction": tf_dirs[0], "confidence": analysis_5m.get("confidence", 0) if analysis_5m else 0},
                "15min": {"direction": tf_dirs[1], "confidence": analysis_15m.get("confidence", 0) if analysis_15m else 0},
                "1hr": {"direction": tf_dirs[2], "confidence": analysis_1hr.get("confidence", 0) if analysis_1hr else 0},
            },
            "details": {
                "5min": analysis_5m,
                "15min": analysis_15m,
                "1hr": analysis_1hr,
            },
        }

    def analyze_from_kite(self, instrument_token: int, symbol: str = "",
                          timeframe: str = "15minute") -> Dict:
        """
        Convenience method: fetch candles from Kite MCP and analyze.
        """
        if not self.client:
            return {"error": "No Kite client provided"}
        
        now = datetime.now()
        from_date = (now - timedelta(days=5)).strftime("%Y-%m-%d 09:15:00")
        to_date = now.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            raw = self.client.get_historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=timeframe
            )
            
            if not raw:
                return {"error": "No data returned from Kite"}
            
            # Convert Kite format to our format
            candles = []
            data_list = raw if isinstance(raw, list) else raw.get("data", [])
            
            for c in data_list:
                if isinstance(c, list) and len(c) >= 6:
                    candles.append({
                        "open": c[1], "high": c[2], "low": c[3],
                        "close": c[4], "volume": c[5]
                    })
                elif isinstance(c, dict):
                    candles.append({
                        "open": c.get("open", 0), "high": c.get("high", 0),
                        "low": c.get("low", 0), "close": c.get("close", 0),
                        "volume": c.get("volume", 0)
                    })
            
            return self.analyze(candles, symbol, timeframe)
            
        except Exception as e:
            return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════
# Demo
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  SIGNAL ENGINE — Demo with Synthetic Data")
    print("=" * 60)

    # Generate synthetic trending candles for testing
    np.random.seed(42)
    n = 100
    base_price = 22000
    trend = np.linspace(0, 300, n)  # uptrend
    noise = np.random.normal(0, 30, n)
    prices = base_price + trend + noise

    candles = []
    for i in range(n):
        o = prices[i] + np.random.uniform(-10, 10)
        h = max(o, prices[i]) + np.random.uniform(5, 25)
        l = min(o, prices[i]) - np.random.uniform(5, 25)
        c = prices[i]
        v = np.random.uniform(50000, 200000) * (1 + 0.5 * (i > 80))  # Volume surge at end
        candles.append({"open": o, "high": h, "low": l, "close": c, "volume": v})

    engine = SignalEngine()
    result = engine.analyze(candles, symbol="NIFTY_SYNTHETIC", timeframe="15min")

    print(f"\n📊 Analysis for {result['symbol']}:")
    print(f"   Direction: {result['direction']} | Confidence: {result['confidence']}%")
    print(f"   Trend: {result['trend_strength']}")
    print(f"\n   VWAP: {result['vwap']['value']} (price {result['vwap']['position']}, {result['vwap']['distance_pct']}%)")
    print(f"   RSI:  {result['rsi']['value']} ({result['rsi']['zone']})")
    print(f"   Supertrend: {result['supertrend']['signal']}")
    print(f"   EMA Trend:  {result['ema']['trend']}")
    print(f"   ATR: {result['atr']['value']} ({result['atr']['pct']}%)")
    print(f"   Volume: {result['volume']['ratio']}x avg (surge: {result['volume']['surge']})")
    print(f"   Volume Profile POC: {result['volume_profile']['poc']}")
    
    print(f"\n   Signals:")
    for s in result["signals"]:
        print(f"     • {s}")
    
    print(f"\n   Score: Bull {result['score_breakdown']['bull_points']} / Bear {result['score_breakdown']['bear_points']}")
    print("\n✅ Demo complete!")
