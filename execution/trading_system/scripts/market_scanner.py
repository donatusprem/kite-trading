#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - MARKET SCANNER
Hybrid data: yfinance for historical OHLCV + Kite MCP for real-time LTP.
Signal engine integration for institutional-grade confluence scoring.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import time
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
    import ta
    import yfinance as yf
except ImportError:
    print("Installing required packages...")
    os.system("pip install pandas numpy ta yfinance --break-system-packages")
    import pandas as pd
    import numpy as np
    import ta
    import yfinance as yf

# ── Kite MCP + Signal Engine integration ─────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EXECUTION_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

_kite_client = None
_signal_engine = None

def _get_kite_client():
    """Lazy-load Kite client. Returns None if unavailable."""
    global _kite_client
    if _kite_client is not None:
        return _kite_client
    try:
        from kite_client import KiteMCPClient
        client = KiteMCPClient()
        if client.check_server():
            _kite_client = client
            return client
    except Exception:
        pass
    return None

def _get_signal_engine():
    """Lazy-load signal engine."""
    global _signal_engine
    if _signal_engine is not None:
        return _signal_engine
    try:
        from signal_engine import SignalEngine
        _signal_engine = SignalEngine()
        return _signal_engine
    except Exception:
        pass
    return None


# ── Universe Presets (dynamic stock lists like Streak) ───────────
UNIVERSE_NIFTY50 = {
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS", "ICICIBANK": "ICICIBANK.NS", "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS", "SBIN": "SBIN.NS", "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "LT": "LT.NS", "AXISBANK": "AXISBANK.NS",
    "ASIANPAINT": "ASIANPAINT.NS", "MARUTI": "MARUTI.NS", "SUNPHARMA": "SUNPHARMA.NS",
    "TITAN": "TITAN.NS", "BAJFINANCE": "BAJFINANCE.NS", "WIPRO": "WIPRO.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS", "NESTLEIND": "NESTLEIND.NS",
    "POWERGRID": "POWERGRID.NS", "NTPC": "NTPC.NS", "TATAMOTORS": "TATAMOTORS.NS",
    "M&M": "M%26M.NS", "ADANIPORTS": "ADANIPORTS.NS", "HCLTECH": "HCLTECH.NS",
    "TATASTEEL": "TATASTEEL.NS", "ONGC": "ONGC.NS", "INDUSINDBK": "INDUSINDBK.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS", "TECHM": "TECHM.NS", "DRREDDY": "DRREDDY.NS",
    "JSWSTEEL": "JSWSTEEL.NS", "COALINDIA": "COALINDIA.NS", "BPCL": "BPCL.NS",
    "CIPLA": "CIPLA.NS", "EICHERMOT": "EICHERMOT.NS", "TATACONSUM": "TATACONSUM.NS",
    "APOLLOHOSP": "APOLLOHOSP.NS", "HEROMOTOCO": "HEROMOTOCO.NS",
    "DIVISLAB": "DIVISLAB.NS", "GRASIM": "GRASIM.NS", "BRITANNIA": "BRITANNIA.NS",
    "SBILIFE": "SBILIFE.NS", "HDFCLIFE": "HDFCLIFE.NS", "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
    "ADANIENT": "ADANIENT.NS", "HINDALCO": "HINDALCO.NS", "BEL": "BEL.NS",
    "SHRIRAMFIN": "SHRIRAMFIN.NS", "TRENT": "TRENT.NS",
}

UNIVERSE_BANKNIFTY = {
    "HDFCBANK": "HDFCBANK.NS", "ICICIBANK": "ICICIBANK.NS", "SBIN": "SBIN.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "AXISBANK": "AXISBANK.NS", "INDUSINDBK": "INDUSINDBK.NS",
    "BANKBARODA": "BANKBARODA.NS", "PNB": "PNB.NS", "FEDERALBNK": "FEDERALBNK.NS",
    "IDFCFIRSTB": "IDFCFIRSTB.NS", "BANDHANBNK": "BANDHANBNK.NS",
    "AUBANK": "AUBANK.NS",
}

UNIVERSE_FNO = {
    **UNIVERSE_NIFTY50,
    **UNIVERSE_BANKNIFTY,
    "VEDL": "VEDL.NS", "NATIONALUM": "NATIONALUM.NS", "ADANIGREEN": "ADANIGREEN.NS",
    "IDEA": "IDEA.NS", "PNB": "PNB.NS", "SAIL": "SAIL.NS",
    "TATAPOWER": "TATAPOWER.NS", "IRCTC": "IRCTC.NS", "ZOMATO": "ZOMATO.NS",
    "PAYTM": "PAYTM.NS", "DELHIVERY": "DELHIVERY.NS", "HAL": "HAL.NS",
    "BEL": "BEL.NS", "NHPC": "NHPC.NS", "PFC": "PFC.NS", "RECLTD": "RECLTD.NS",
    "CANBK": "CANBK.NS", "UNIONBANK": "UNIONBANK.NS",
}

# Quick-scan subset for fast page loads (top traded, <15 stocks)
UNIVERSE_QUICK = {
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS", "ICICIBANK": "ICICIBANK.NS", "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "ITC": "ITC.NS", "TATAMOTORS": "TATAMOTORS.NS",
    "BAJFINANCE": "BAJFINANCE.NS", "ADANIPORTS": "ADANIPORTS.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "LT": "LT.NS", "AXISBANK": "AXISBANK.NS",
    "POWERGRID": "POWERGRID.NS",
}

UNIVERSES = {
    "nifty50": UNIVERSE_NIFTY50,
    "banknifty": UNIVERSE_BANKNIFTY,
    "fno": UNIVERSE_FNO,
    "quick": UNIVERSE_QUICK,
}

# Legacy alias
WATCHLIST = UNIVERSE_QUICK


# ── Pre-built Scanner Presets (like Streak's scanner gallery) ────
SCANNER_PRESETS = {
    "rsi_oversold": {
        "name": "RSI Oversold Bounce",
        "description": "Stocks with RSI below 30 showing reversal potential",
        "icon": "TrendingUp",
        "conditions": [{"indicator": "RSI", "operator": "<", "value": 30}],
        "sort": "rsi_asc",
    },
    "rsi_overbought": {
        "name": "RSI Overbought",
        "description": "Stocks with RSI above 70 — potential short or exit",
        "icon": "TrendingDown",
        "conditions": [{"indicator": "RSI", "operator": ">", "value": 70}],
        "sort": "rsi_desc",
    },
    "volume_breakout": {
        "name": "Volume Breakout",
        "description": "Volume > 2x average with price momentum",
        "icon": "BarChart3",
        "conditions": [{"indicator": "VOLUME_RATIO", "operator": ">", "value": 2.0}],
        "sort": "volume_ratio_desc",
    },
    "ema_crossover": {
        "name": "EMA Crossover (20/50)",
        "description": "EMA 20 just crossed above EMA 50 — bullish",
        "icon": "ArrowUpRight",
        "conditions": [{"indicator": "EMA_CROSS", "operator": "==", "value": "bullish"}],
        "sort": "score_desc",
    },
    "supertrend_buy": {
        "name": "Supertrend Buy",
        "description": "Supertrend flipped to BUY signal",
        "icon": "Zap",
        "conditions": [{"indicator": "SUPERTREND", "operator": "==", "value": "buy"}],
        "sort": "score_desc",
    },
    "near_support": {
        "name": "Near Support Zone",
        "description": "Price within 2% of key support level",
        "icon": "Shield",
        "conditions": [{"indicator": "SUPPORT_DIST", "operator": "<", "value": 2.0}],
        "sort": "support_dist_asc",
    },
    "vwap_reclaim": {
        "name": "VWAP Reclaim",
        "description": "Price reclaimed above VWAP — institutional buying",
        "icon": "Activity",
        "conditions": [{"indicator": "VWAP_POSITION", "operator": "==", "value": "above"}],
        "sort": "score_desc",
    },
    "strong_uptrend": {
        "name": "Strong Uptrend",
        "description": "Higher highs + higher lows + EMA alignment",
        "icon": "Rocket",
        "conditions": [
            {"indicator": "TREND", "operator": "==", "value": "uptrend"},
            {"indicator": "TREND_STRENGTH", "operator": "==", "value": "strong"},
        ],
        "sort": "score_desc",
    },
}



def fetch_kite_ltp_batch(symbols: List[str]) -> Dict[str, float]:
    """Fetch real-time LTP from Kite MCP for a batch of symbols."""
    client = _get_kite_client()
    if not client:
        return {}
    try:
        instruments = [f"NSE:{s}" for s in symbols if s != "NIFTY50"]
        if "NIFTY50" in symbols:
            instruments.append("NSE:NIFTY 50")
        raw = client.get_ltp(instruments)
        # Parse response — handle both dict and list formats
        ltp_map = {}
        if isinstance(raw, dict):
            for key, val in raw.items():
                sym = key.replace("NSE:", "").replace(" ", "")
                if sym == "NIFTY50":
                    sym = "NIFTY50"
                price = val.get("last_price", 0) if isinstance(val, dict) else val
                if price:
                    ltp_map[sym] = float(price)
        return ltp_map
    except Exception as e:
        print(f"[KITE] LTP fetch failed: {e}")
        return {}


def fetch_ohlcv(symbol: str, yf_ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch OHLCV from yfinance. Returns clean DataFrame or empty."""
    try:
        df = yf.download(yf_ticker, period=period, interval="1d", progress=False)
        if df.empty:
            print(f"[WARN] No data returned for {symbol} ({yf_ticker})")
            return pd.DataFrame()

        # Flatten multi-level columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() for col in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]

        df = df.reset_index()
        df.rename(columns={"index": "date", "Date": "date"}, inplace=True)
        if "date" not in df.columns:
            df["date"] = df.index

        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
        return df

    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol}: {e}")
        return pd.DataFrame()


class TechnicalAnalyzer:
    """Advanced technical analysis for structure-based trading"""

    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = json.load(f)
        self.base_path = os.path.dirname(os.path.dirname(config_path))

    def detect_support_resistance(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """Identify key support and resistance levels"""
        highs = df["high"].rolling(window=lookback, center=True).max()
        lows = df["low"].rolling(window=lookback, center=True).min()

        resistance_levels = []
        support_levels = []

        for i in range(lookback, len(df) - lookback):
            if df["high"].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df["high"].iloc[i])
            if df["low"].iloc[i] == lows.iloc[i]:
                support_levels.append(df["low"].iloc[i])

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
            "resistance": cluster_levels(resistance_levels)[-3:],
            "support": cluster_levels(support_levels)[-3:],
            "current_price": float(df["close"].iloc[-1]),
        }

    def identify_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """Find Fair Value Gaps (FVG) - price imbalances"""
        fvgs = []
        for i in range(2, len(df)):
            if df["high"].iloc[i - 2] < df["low"].iloc[i]:
                fvgs.append({
                    "type": "bullish",
                    "high": float(df["low"].iloc[i]),
                    "low": float(df["high"].iloc[i - 2]),
                    "index": i,
                })
            if df["low"].iloc[i - 2] > df["high"].iloc[i]:
                fvgs.append({
                    "type": "bearish",
                    "high": float(df["low"].iloc[i - 2]),
                    "low": float(df["high"].iloc[i]),
                    "index": i,
                })

        current_price = float(df["close"].iloc[-1])
        unfilled = []
        for fvg in fvgs[-10:]:
            if fvg["type"] == "bullish" and current_price >= fvg["low"]:
                unfilled.append(fvg)
            elif fvg["type"] == "bearish" and current_price <= fvg["high"]:
                unfilled.append(fvg)
        return unfilled

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Determine trend direction and strength"""
        ema_20 = ta.trend.ema_indicator(df["close"], window=20)
        ema_50 = ta.trend.ema_indicator(df["close"], window=50)

        recent_highs = df["high"].tail(10).values
        recent_lows = df["low"].tail(10).values

        higher_highs = sum(recent_highs[i] > recent_highs[i - 1] for i in range(1, len(recent_highs))) > 6
        higher_lows = sum(recent_lows[i] > recent_lows[i - 1] for i in range(1, len(recent_lows))) > 6
        lower_highs = sum(recent_highs[i] < recent_highs[i - 1] for i in range(1, len(recent_highs))) > 6
        lower_lows = sum(recent_lows[i] < recent_lows[i - 1] for i in range(1, len(recent_lows))) > 6

        ema20_val = float(ema_20.iloc[-1])
        ema50_val = float(ema_50.iloc[-1])

        if higher_highs and higher_lows and ema20_val > ema50_val:
            trend, strength = "uptrend", "strong"
        elif lower_highs and lower_lows and ema20_val < ema50_val:
            trend, strength = "downtrend", "strong"
        elif ema20_val > ema50_val:
            trend, strength = "uptrend", "weak"
        elif ema20_val < ema50_val:
            trend, strength = "downtrend", "weak"
        else:
            trend, strength = "sideways", "neutral"

        return {
            "direction": trend,
            "strength": strength,
            "ema_20": ema20_val,
            "ema_50": ema50_val,
        }

    def detect_candlestick_patterns(self, df: pd.DataFrame) -> List[str]:
        """Identify key candlestick patterns at critical levels"""
        patterns = []
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

        if c3["close"] > c3["open"]:
            body = c3["close"] - c3["open"]
            upper_wick = c3["high"] - c3["close"]
            lower_wick = c3["open"] - c3["low"]

            if c2["close"] < c2["open"] and c3["open"] < c2["close"] and c3["close"] > c2["open"]:
                patterns.append("bullish_engulfing")
            if body > 0 and lower_wick > body * 2 and upper_wick < body * 0.3:
                patterns.append("hammer")
            if (c1["close"] < c1["open"] and c2["close"] < c2["open"]
                    and abs(c2["close"] - c2["open"]) < body * 0.3
                    and c3["close"] > (c1["open"] + c1["close"]) / 2):
                patterns.append("morning_star")

        if c3["close"] < c3["open"]:
            body = c3["open"] - c3["close"]
            upper_wick = c3["high"] - c3["open"]
            lower_wick = c3["close"] - c3["low"]

            if c2["close"] > c2["open"] and c3["open"] > c2["close"] and c3["close"] < c2["open"]:
                patterns.append("bearish_engulfing")
            if body > 0 and upper_wick > body * 2 and lower_wick < body * 0.3:
                patterns.append("shooting_star")
            if (c1["close"] > c1["open"] and c2["close"] > c2["open"]
                    and abs(c2["close"] - c2["open"]) < body * 0.3
                    and c3["close"] < (c1["open"] + c1["close"]) / 2):
                patterns.append("evening_star")

        return patterns

    def calculate_score(self, analysis: Dict) -> int:
        """Score setup quality from 0-100 based on technical confluence"""
        score = 0
        current_price = analysis["sr_levels"]["current_price"]

        # Support/Resistance proximity (25 points)
        sr_score = 0
        for support in analysis["sr_levels"]["support"]:
            dist = abs(current_price - support) / current_price
            if dist < 0.02:
                sr_score = 25
            elif dist < 0.03:
                sr_score = max(sr_score, 20)
        for resistance in analysis["sr_levels"]["resistance"]:
            dist = abs(current_price - resistance) / current_price
            if dist < 0.02:
                sr_score = max(sr_score, 25)
            elif dist < 0.03:
                sr_score = max(sr_score, 20)
        score += sr_score

        # FVG (20 points)
        if len(analysis["fvgs"]) > 0:
            score += 20

        # Trend (20 points)
        if analysis["trend"]["strength"] == "strong":
            score += 20
        elif analysis["trend"]["strength"] == "weak":
            score += 10

        # Candlestick patterns (15 points)
        pattern_scores = {
            "bullish_engulfing": 15, "bearish_engulfing": 15,
            "morning_star": 15, "evening_star": 15,
            "hammer": 12, "shooting_star": 12,
        }
        score += max([pattern_scores.get(p, 0) for p in analysis["patterns"]] + [0])

        # Volume (10 points)
        if analysis.get("volume_above_avg"):
            score += 10
        elif analysis.get("volume_moderate"):
            score += 5

        # R:R (10 points)
        if analysis.get("risk_reward", 0) >= 3:
            score += 10
        elif analysis.get("risk_reward", 0) >= 2:
            score += 7

        return min(score, 100)

    def analyze_stock(self, symbol: str, df: pd.DataFrame,
                      live_price: Optional[float] = None) -> Dict:
        """Complete technical analysis for a single stock"""
        if len(df) < 50:
            return None

        # If we have a live Kite price, overlay it on the last candle
        if live_price and live_price > 0:
            df = df.copy()
            df.iloc[-1, df.columns.get_loc("close")] = live_price
            df.iloc[-1, df.columns.get_loc("high")] = max(
                float(df.iloc[-1]["high"]), live_price)
            df.iloc[-1, df.columns.get_loc("low")] = min(
                float(df.iloc[-1]["low"]), live_price)

        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "sr_levels": self.detect_support_resistance(df),
            "fvgs": self.identify_fair_value_gaps(df),
            "trend": self.analyze_trend(df),
            "patterns": self.detect_candlestick_patterns(df),
            "current_price": float(df["close"].iloc[-1]),
            "volume": float(df["volume"].iloc[-1]),
            "avg_volume": float(df["volume"].mean()),
            "data_source": "kite+yfinance" if live_price else "yfinance",
        }

        analysis["volume_above_avg"] = analysis["volume"] > analysis["avg_volume"] * 1.5
        analysis["volume_moderate"] = analysis["volume"] > analysis["avg_volume"]
        analysis["score"] = self.calculate_score(analysis)

        # ── Signal Engine boost: add confluence score if available ──
        engine = _get_signal_engine()
        if engine and len(df) >= 20:
            candles = []
            for _, row in df.tail(100).iterrows():
                candles.append({
                    "open": float(row["open"]), "high": float(row["high"]),
                    "low": float(row["low"]), "close": float(row["close"]),
                    "volume": float(row["volume"]),
                })
            sig = engine.analyze(candles, symbol, "daily")
            if "error" not in sig:
                analysis["signal_engine"] = {
                    "direction": sig["direction"],
                    "confidence": sig["confidence"],
                    "trend_strength": sig["trend_strength"],
                    "rsi": sig["rsi"]["value"],
                    "supertrend": sig["supertrend"]["signal"],
                    "vwap_position": sig["vwap"]["position"],
                    "divergence": sig["rsi"]["divergence"]["type"],
                }
                # Boost original score with signal engine confluence
                if sig["confidence"] >= 75:
                    analysis["score"] = min(100, analysis["score"] + 10)
                elif sig["confidence"] >= 60:
                    analysis["score"] = min(100, analysis["score"] + 5)

        min_score = self.config["entry_rules"]["minimum_score"]
        if analysis["score"] >= min_score:
            if analysis["trend"]["direction"] == "uptrend":
                analysis["setup_type"] = "LONG"
                analysis["entry_strategy"] = "Wait for pullback to support/FVG, enter on bullish confirmation"
            elif analysis["trend"]["direction"] == "downtrend":
                analysis["setup_type"] = "SHORT"
                analysis["entry_strategy"] = "Wait for pullback to resistance/FVG, enter on bearish confirmation"
            else:
                analysis["setup_type"] = "RANGE"
                analysis["entry_strategy"] = "Trade bounces at support/resistance"
        else:
            analysis["setup_type"] = "SKIP"
            analysis["entry_strategy"] = "No high-quality setup"

        return analysis


class MarketScanner:
    """Main scanner — hybrid Kite LTP + yfinance data with signal engine"""

    PATTERN_LABELS = {
        "bullish_engulfing": "Bullish Engulfing",
        "bearish_engulfing": "Bearish Engulfing",
        "hammer": "Hammer",
        "shooting_star": "Shooting Star",
        "morning_star": "Morning Star",
        "evening_star": "Evening Star",
    }

    def __init__(self, config_path: str):
        self.analyzer = TechnicalAnalyzer(config_path)
        self.config = self.analyzer.config
        self.base_path = self.analyzer.base_path
        self._ltp_cache: Dict[str, float] = {}

    def fetch_all(self) -> Dict[str, pd.DataFrame]:
        """Fetch OHLCV for entire watchlist from yfinance"""
        frames = {}
        for symbol, yf_ticker in WATCHLIST.items():
            df = fetch_ohlcv(symbol, yf_ticker)
            if not df.empty and len(df) >= 50:
                frames[symbol] = df
                print(f"[FETCH] {symbol}: {len(df)} bars")
            else:
                print(f"[SKIP] {symbol}: insufficient data ({len(df)} bars)")

        # Overlay real-time Kite LTP
        kite_ltps = fetch_kite_ltp_batch(list(frames.keys()))
        if kite_ltps:
            self._ltp_cache = kite_ltps
            print(f"[KITE] Live LTP for {len(kite_ltps)} symbols")
        else:
            print(f"[KITE] Offline — using yfinance close prices")

        return frames

    def format_opportunity(self, analysis: Dict) -> Dict:
        """Transform analyzer output into the format the dashboard expects"""
        signals = []
        for p in analysis.get("patterns", []):
            signals.append(self.PATTERN_LABELS.get(p, p.replace("_", " ").title()))

        trend = analysis.get("trend", {})
        if trend.get("strength") == "strong":
            signals.append(f"Strong {trend['direction'].title()}")
        elif trend.get("direction") != "sideways":
            signals.append(trend["direction"].title())

        if analysis.get("volume_above_avg"):
            signals.append("High Volume")
        if analysis.get("fvgs"):
            fvg_type = analysis["fvgs"][0]["type"].title()
            signals.append(f"{fvg_type} FVG Present")

        sr = analysis.get("sr_levels", {})
        current = analysis.get("current_price", 0)

        supports = sorted(sr.get("support", []))
        stop_loss = None
        for s in reversed(supports):
            if s < current:
                stop_loss = round(s, 2)
                break
        if stop_loss is None:
            stop_loss = round(current * 0.97, 2)

        resistances = sorted(sr.get("resistance", []))
        targets = [r for r in resistances if r > current]
        target1 = round(targets[0], 2) if len(targets) >= 1 else round(current * 1.03, 2)
        target2 = round(targets[1], 2) if len(targets) >= 2 else round(current * 1.05, 2)

        return {
            "symbol": analysis["symbol"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": analysis["score"],
            "ltp": round(current, 2),
            "signals": signals if signals else ["Scanning..."],
            "pattern": signals[0] if signals else "None",
            "trend": trend.get("direction", "neutral").title(),
            "stopLoss": stop_loss,
            "target1": target1,
            "target2": target2,
            "setup_type": analysis.get("setup_type", "SKIP"),
            "entry_strategy": analysis.get("entry_strategy", ""),
        }

    def scan_market(self) -> List[Dict]:
        """Scan all watchlist stocks — hybrid Kite + yfinance"""
        print(f"\n{'='*60}")
        print(f"[SCAN] Starting market scan at {datetime.now().strftime('%H:%M:%S')}")
        print(f"[SCAN] Hybrid mode: yfinance history + Kite real-time LTP")
        print(f"{'='*60}\n")

        frames = self.fetch_all()
        if not frames:
            print("[WARN] No data fetched from yfinance.")
            return []

        opportunities = []
        for symbol, df in frames.items():
            try:
                live_price = self._ltp_cache.get(symbol)
                analysis = self.analyzer.analyze_stock(symbol, df, live_price)
                if analysis is None:
                    continue
                formatted = self.format_opportunity(analysis)
                opportunities.append(formatted)
                src = "KITE" if live_price else "YF"
                se_info = ""
                if "signal_engine" in analysis:
                    se = analysis["signal_engine"]
                    se_info = f" | SE: {se['direction']} {se['confidence']}%"
                print(f"[SCAN] {symbol} - Score: {analysis['score']}/100 - {analysis.get('setup_type', 'N/A')} [{src}]{se_info}")
            except Exception as e:
                print(f"[ERROR] {symbol}: {e}")
                import traceback
                traceback.print_exc()

        opportunities.sort(key=lambda x: x["score"], reverse=True)
        return opportunities

    def save_opportunities(self, opportunities: List[Dict]):
        """Save scan results as JSON array for dashboard"""
        alerts_dir = os.path.join(self.base_path, "alerts")
        os.makedirs(alerts_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(alerts_dir, f"scan_{timestamp}.json")

        with open(filepath, "w") as f:
            json.dump(opportunities, f, indent=2)

        print(f"\n[SAVED] {len(opportunities)} results → {filepath}")
        return filepath

    def log_scan(self, opportunities: List[Dict]):
        """Log scan results to journal"""
        journals_dir = os.path.join(self.base_path, "journals")
        os.makedirs(journals_dir, exist_ok=True)

        journal_file = os.path.join(journals_dir, f"journal_{datetime.now().strftime('%Y%m%d')}.jsonl")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "scan",
            "opportunities_found": len(opportunities),
            "top_scores": [op["score"] for op in opportunities[:5]],
            "top_symbols": [op["symbol"] for op in opportunities[:5]],
        }
        with open(journal_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def run_single_scan(self) -> List[Dict]:
        """Run a single scan and save results. Called by the API."""
        opportunities = self.scan_market()
        if opportunities:
            self.save_opportunities(opportunities)
            self.log_scan(opportunities)
        else:
            self.save_opportunities([])
        return opportunities

    # ── Live Scan (Streak-like: direct results, no file) ─────────

    def _extract_indicators(self, symbol: str, df: pd.DataFrame,
                            live_price: Optional[float] = None) -> Optional[Dict]:
        """Compute all indicators for a stock — used by preset/custom scans."""
        if len(df) < 50:
            return None

        if live_price and live_price > 0:
            df = df.copy()
            df.iloc[-1, df.columns.get_loc("close")] = live_price
            df.iloc[-1, df.columns.get_loc("high")] = max(float(df.iloc[-1]["high"]), live_price)
            df.iloc[-1, df.columns.get_loc("low")] = min(float(df.iloc[-1]["low"]), live_price)

        close = df["close"]
        current_price = float(close.iloc[-1])

        # RSI
        rsi_series = ta.momentum.rsi(close, window=14)
        rsi_val = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0

        # EMA 20/50
        ema20 = ta.trend.ema_indicator(close, window=20)
        ema50 = ta.trend.ema_indicator(close, window=50)
        ema20_val = float(ema20.iloc[-1])
        ema50_val = float(ema50.iloc[-1])
        ema20_prev = float(ema20.iloc[-2]) if len(ema20) > 1 else ema20_val
        ema50_prev = float(ema50.iloc[-2]) if len(ema50) > 1 else ema50_val
        ema_cross = "bullish" if (ema20_prev <= ema50_prev and ema20_val > ema50_val) else \
                    "bearish" if (ema20_prev >= ema50_prev and ema20_val < ema50_val) else "none"

        # Volume ratio
        vol = float(df["volume"].iloc[-1])
        avg_vol = float(df["volume"].mean())
        volume_ratio = round(vol / avg_vol, 2) if avg_vol > 0 else 0

        # Supertrend (using ATR-based approximation)
        supertrend_signal = "buy" if ema20_val > ema50_val and rsi_val > 45 else "sell"
        engine = _get_signal_engine()
        if engine and len(df) >= 20:
            try:
                candles = []
                for _, row in df.tail(100).iterrows():
                    candles.append({
                        "open": float(row["open"]), "high": float(row["high"]),
                        "low": float(row["low"]), "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    })
                sig = engine.analyze(candles, symbol, "daily")
                if "error" not in sig:
                    supertrend_signal = sig["supertrend"]["signal"]
                    vwap_position = sig["vwap"]["position"]
                else:
                    vwap_position = "above" if current_price > ema20_val else "below"
            except Exception:
                vwap_position = "above" if current_price > ema20_val else "below"
        else:
            vwap_position = "above" if current_price > ema20_val else "below"

        # Trend detection
        recent_highs = df["high"].tail(10).values
        recent_lows = df["low"].tail(10).values
        hh = sum(recent_highs[i] > recent_highs[i - 1] for i in range(1, len(recent_highs))) > 6
        hl = sum(recent_lows[i] > recent_lows[i - 1] for i in range(1, len(recent_lows))) > 6
        if hh and hl and ema20_val > ema50_val:
            trend, trend_strength = "uptrend", "strong"
        elif ema20_val > ema50_val:
            trend, trend_strength = "uptrend", "weak"
        elif ema20_val < ema50_val:
            trend, trend_strength = "downtrend", "weak"
        else:
            trend, trend_strength = "sideways", "neutral"

        # Support distance
        sr = self.analyzer.detect_support_resistance(df)
        supports = sr.get("support", [])
        support_dist = 100.0
        for s in supports:
            dist = abs(current_price - s) / current_price * 100
            if s < current_price and dist < support_dist:
                support_dist = round(dist, 2)

        # Full analysis for score
        analysis = self.analyzer.analyze_stock(symbol, df, live_price)
        score = analysis["score"] if analysis else 50

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "rsi": round(rsi_val, 1),
            "ema20": round(ema20_val, 2),
            "ema50": round(ema50_val, 2),
            "ema_cross": ema_cross,
            "volume_ratio": volume_ratio,
            "supertrend": supertrend_signal,
            "vwap_position": vwap_position,
            "trend": trend,
            "trend_strength": trend_strength,
            "support_dist": support_dist,
            "score": score,
            "setup_type": analysis.get("setup_type", "SKIP") if analysis else "SKIP",
            "data_source": "kite+yfinance" if live_price else "yfinance",
            "patterns": analysis.get("patterns", []) if analysis else [],
            "sr_levels": sr,
            "volume": int(vol),
            "avg_volume": int(avg_vol),
        }

    def _check_conditions(self, indicators: Dict, conditions: List[Dict]) -> bool:
        """Check if a stock matches ALL given conditions (AND logic)."""
        for cond in conditions:
            indicator = cond["indicator"].upper()
            operator = cond["operator"]
            value = cond["value"]

            # Map indicator name to actual value
            actual = None
            if indicator == "RSI":
                actual = indicators["rsi"]
            elif indicator == "VOLUME_RATIO":
                actual = indicators["volume_ratio"]
            elif indicator == "EMA_CROSS":
                actual = indicators["ema_cross"]
            elif indicator == "SUPERTREND":
                actual = indicators["supertrend"]
            elif indicator == "VWAP_POSITION":
                actual = indicators["vwap_position"]
            elif indicator == "TREND":
                actual = indicators["trend"]
            elif indicator == "TREND_STRENGTH":
                actual = indicators["trend_strength"]
            elif indicator == "SUPPORT_DIST":
                actual = indicators["support_dist"]
            elif indicator == "SCORE":
                actual = indicators["score"]
            elif indicator == "EMA20":
                actual = indicators["ema20"]
            elif indicator == "EMA50":
                actual = indicators["ema50"]
            elif indicator == "PRICE":
                actual = indicators["current_price"]
            else:
                continue  # Unknown indicator, skip

            if actual is None:
                return False

            # Evaluate condition
            if isinstance(actual, (int, float)) and isinstance(value, (int, float)):
                if operator == ">" and not (actual > value):
                    return False
                elif operator == ">=" and not (actual >= value):
                    return False
                elif operator == "<" and not (actual < value):
                    return False
                elif operator == "<=" and not (actual <= value):
                    return False
                elif operator == "==" and not (actual == value):
                    return False
            elif isinstance(actual, str):
                if operator == "==" and actual.lower() != str(value).lower():
                    return False
                elif operator == "!=" and actual.lower() == str(value).lower():
                    return False

        return True

    def live_scan(self, universe: str = "quick",
                  preset: Optional[str] = None,
                  conditions: Optional[List[Dict]] = None,
                  custom_symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        Run a live scan — returns results directly (no file save).
        Like Streak: select universe, pick preset or custom conditions.
        """
        # Resolve universe
        if custom_symbols:
            watchlist = {s: f"{s}.NS" for s in custom_symbols}
        else:
            watchlist = UNIVERSES.get(universe, UNIVERSE_QUICK)

        # Resolve conditions from preset
        scan_conditions = conditions or []
        sort_key = "score_desc"
        if preset and preset in SCANNER_PRESETS:
            preset_def = SCANNER_PRESETS[preset]
            scan_conditions = preset_def["conditions"]
            sort_key = preset_def.get("sort", "score_desc")

        print(f"\n[LIVE SCAN] Universe: {universe} ({len(watchlist)} stocks)")
        if preset:
            print(f"[LIVE SCAN] Preset: {preset}")
        if scan_conditions:
            print(f"[LIVE SCAN] Conditions: {scan_conditions}")

        # Fetch data
        frames = {}
        for symbol, yf_ticker in watchlist.items():
            df = fetch_ohlcv(symbol, yf_ticker)
            if not df.empty and len(df) >= 50:
                frames[symbol] = df

        # Get live prices
        kite_ltps = fetch_kite_ltp_batch(list(frames.keys()))

        # Extract indicators and filter
        results = []
        for symbol, df in frames.items():
            try:
                live_price = kite_ltps.get(symbol)
                indicators = self._extract_indicators(symbol, df, live_price)
                if indicators is None:
                    continue

                # Apply conditions filter
                if scan_conditions and not self._check_conditions(indicators, scan_conditions):
                    continue

                # Format for frontend
                formatted = self.format_opportunity(
                    self.analyzer.analyze_stock(symbol, df, live_price) or indicators
                )
                # Attach indicator data for the frontend
                formatted["indicators"] = {
                    "rsi": indicators["rsi"],
                    "ema20": indicators["ema20"],
                    "ema50": indicators["ema50"],
                    "ema_cross": indicators["ema_cross"],
                    "volume_ratio": indicators["volume_ratio"],
                    "supertrend": indicators["supertrend"],
                    "vwap_position": indicators["vwap_position"],
                    "trend_strength": indicators["trend_strength"],
                    "support_dist": indicators["support_dist"],
                }
                results.append(formatted)
                print(f"  ✓ {symbol}: score={formatted['score']} rsi={indicators['rsi']}")

            except Exception as e:
                print(f"  ✗ {symbol}: {e}")

        # Sort results
        if sort_key == "rsi_asc":
            results.sort(key=lambda x: x["indicators"].get("rsi", 50))
        elif sort_key == "rsi_desc":
            results.sort(key=lambda x: x["indicators"].get("rsi", 50), reverse=True)
        elif sort_key == "volume_ratio_desc":
            results.sort(key=lambda x: x["indicators"].get("volume_ratio", 0), reverse=True)
        elif sort_key == "support_dist_asc":
            results.sort(key=lambda x: x["indicators"].get("support_dist", 100))
        else:
            results.sort(key=lambda x: x["score"], reverse=True)

        print(f"[LIVE SCAN] {len(results)} matches from {len(frames)} stocks")
        return results

    def run_continuous(self):
        """Run scanner in a loop"""
        print("\n" + "=" * 60)
        print("MARKET SCANNER - Live yfinance Data")
        print("=" * 60 + "\n")

        interval = self.config["scanning"]["scan_interval_minutes"] * 60
        print(f"[CONFIG] Interval: {self.config['scanning']['scan_interval_minutes']}min")
        print(f"[CONFIG] Min score: {self.config['entry_rules']['minimum_score']}")
        print(f"[CONFIG] Watchlist: {len(WATCHLIST)} stocks\n")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                opps = self.run_single_scan()
                if opps:
                    high_q = [o for o in opps if o["score"] >= self.config["entry_rules"]["minimum_score"]]
                    print(f"\n[SUMMARY] {len(opps)} scanned, {len(high_q)} above threshold")
                    for op in opps[:3]:
                        print(f"  → {op['symbol']}: {op['score']}/100 - {op['trend']}")
                else:
                    print("\n[SUMMARY] No setups found")

                print(f"\n[WAIT] Next scan in {self.config['scanning']['scan_interval_minutes']} minutes...")
                print("-" * 60 + "\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n[STOP] Scanner stopped by user")


def run_scan():
    """Run a single scan and return results. Used by the API."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base, "config", "trading_rules.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] Config not found: {config_path}")
        return []
    scanner = MarketScanner(config_path)
    return scanner.run_single_scan()


def main():
    """Main entry point"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base, "config", "trading_rules.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] Config not found: {config_path}")
        sys.exit(1)
    scanner = MarketScanner(config_path)
    if "--once" in sys.argv:
        scanner.run_single_scan()
    else:
        scanner.run_continuous()


if __name__ == "__main__":
    main()
