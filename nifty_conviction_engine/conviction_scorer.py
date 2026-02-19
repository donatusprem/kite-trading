"""
Nifty Direction Conviction Engine - Master Conviction Scorer
Combines all 4 analysis layers into a unified conviction score for trading decisions.
"""

from .technical_analysis import TechnicalAnalyzer
from .candlestick_patterns import CandlestickAnalyzer
from .options_intelligence import OptionsAnalyzer
from .price_action import PriceActionAnalyzer


class ConvictionScorer:
    """
    Master scorer that combines:
    - Layer 1: Technical Analysis (EMA, RSI, MACD, ADX, Supertrend, VWAP)
    - Layer 2: Candlestick Pattern Recognition (15 patterns)
    - Layer 3: Options Intelligence (PCR, OI walls, Max Pain)
    - Layer 4: Price Action (S/R, trend structure, breakouts, volume, divergence)

    Multi-timeframe analysis with weighted scoring produces a -10 to +10 conviction score.
    """

    # Timeframe weights
    TF_WEIGHTS = {"5min": 0.15, "15min": 0.30, "60min": 0.35, "daily": 0.20}

    # Layer weights (with options data)
    LAYER_WEIGHTS_WITH_OPTIONS = {"technical": 0.35, "candlestick": 0.15, "options": 0.25, "price_action": 0.25}
    # Layer weights (without options data)
    LAYER_WEIGHTS_NO_OPTIONS = {"technical": 0.45, "candlestick": 0.20, "price_action": 0.35}

    def __init__(self, candles_5min, candles_15min, candles_60min, candles_daily,
                 spot_price, options_data=None):
        """
        Args:
            candles_5min: list of dicts {date, open, high, low, close, volume}
            candles_15min: same format
            candles_60min: same format
            candles_daily: same format
            spot_price: current Nifty spot price (float)
            options_data: optional list of {strike, type, oi, volume, ltp, bid, ask, change_oi}
        """
        self.candles = {
            "5min": candles_5min or [],
            "15min": candles_15min or [],
            "60min": candles_60min or [],
            "daily": candles_daily or [],
        }
        self.spot_price = spot_price
        self.options_data = options_data
        self.atm_strike = round(spot_price / 50) * 50

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, value))

    @staticmethod
    def _normalize(value, old_max, new_max=5.0):
        """Normalize a score from [-old_max, +old_max] to [-new_max, +new_max]."""
        if old_max == 0:
            return 0.0
        return (value / old_max) * new_max

    @staticmethod
    def _direction_label(score):
        if score >= 4:
            return "STRONG_BULLISH"
        if score >= 1.0:
            return "BULLISH"
        if score <= -4:
            return "STRONG_BEARISH"
        if score <= -1.0:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _conviction_level(score):
        a = abs(score)
        if a >= 5:
            return "VERY_HIGH"
        if a >= 3:
            return "HIGH"
        if a >= 2:
            return "MODERATE"
        if a >= 0.8:
            return "LOW"
        return "NEUTRAL"

    # ------------------------------------------------------------------
    # Per-timeframe analysis
    # ------------------------------------------------------------------

    def analyze_timeframe(self, candles, timeframe_name):
        """Run Layers 1, 2, 4 on a single timeframe's candles.

        Returns:
            dict with keys tech, candle, price_action (each has score + direction + details).
        """
        result = {"timeframe": timeframe_name, "tech": None, "candle": None, "price_action": None,
                  "combined_score": 0.0, "direction": "NEUTRAL"}

        # Layer 1 - Technical
        try:
            ta = TechnicalAnalyzer(candles)
            tech = ta.get_trend_momentum_score()
            result["tech"] = tech
        except Exception as e:
            result["tech"] = {"score": 0, "direction": "NEUTRAL", "signals": [], "details": {}, "error": str(e)}

        # Layer 2 - Candlestick
        try:
            ca = CandlestickAnalyzer(candles)
            cand = ca.get_candlestick_score()
            result["candle"] = cand
        except Exception as e:
            result["candle"] = {"score": 0, "direction": "NEUTRAL", "patterns_found": [], "error": str(e)}

        # Layer 4 - Price Action
        try:
            pa = PriceActionAnalyzer(candles)
            pact = pa.get_price_action_score()
            result["price_action"] = pact
        except Exception as e:
            result["price_action"] = {"score": 0, "direction": "NEUTRAL", "signals": [], "error": str(e)}

        # Combine for this timeframe (simple weighted avg: tech 50%, candle 25%, PA 25%)
        tech_s = result["tech"].get("score", 0)
        cand_s = self._normalize(result["candle"].get("score", 0), 3, 5)
        pa_s = self._normalize(result["price_action"].get("score", 0), 2, 5)
        combined = tech_s * 0.50 + cand_s * 0.25 + pa_s * 0.25
        result["combined_score"] = round(combined, 2)
        result["direction"] = self._direction_label(combined)
        return result

    # ------------------------------------------------------------------
    # Multi-timeframe
    # ------------------------------------------------------------------

    def multi_timeframe_analysis(self):
        """Run analysis across all 4 timeframes with weighting.

        Returns:
            dict with per-timeframe results, weighted combined score, and alignment info.
        """
        tf_results = {}
        weighted_score = 0.0

        for tf_name, weight in self.TF_WEIGHTS.items():
            candles = self.candles.get(tf_name, [])
            if len(candles) < 5:
                tf_results[tf_name] = {"combined_score": 0.0, "direction": "NEUTRAL",
                                       "tech": {"score": 0}, "candle": {"score": 0},
                                       "price_action": {"score": 0}}
                continue
            res = self.analyze_timeframe(candles, tf_name)
            tf_results[tf_name] = res
            weighted_score += res["combined_score"] * weight

        # Alignment bonus: reward timeframe agreement
        directions = [tf_results[tf]["direction"] for tf in tf_results]
        bullish_count = sum(1 for d in directions if "BULLISH" in d)
        bearish_count = sum(1 for d in directions if "BEARISH" in d)
        alignment_bonus = 0.0
        if bullish_count >= 3:
            alignment_bonus = 1.5
        elif bearish_count >= 3:
            alignment_bonus = -1.5
        elif bullish_count >= 2:
            alignment_bonus = 0.5
        elif bearish_count >= 2:
            alignment_bonus = -0.5

        return {
            "timeframe_results": tf_results,
            "weighted_score": round(weighted_score, 2),
            "alignment_bonus": alignment_bonus,
            "total_score": round(weighted_score + alignment_bonus, 2),
        }

    # ------------------------------------------------------------------
    # Options analysis
    # ------------------------------------------------------------------

    def analyze_options(self):
        """Run Layer 3 (Options Intelligence) if data is available."""
        if not self.options_data:
            return None
        try:
            oa = OptionsAnalyzer(self.spot_price, self.options_data)
            return oa.get_options_score()
        except Exception as e:
            return {"score": 0, "direction": "NEUTRAL", "error": str(e)}

    # ------------------------------------------------------------------
    # Key levels extraction
    # ------------------------------------------------------------------

    def _extract_key_levels(self, mtf, options_result):
        """Pull together key levels from all analyses."""
        levels = {
            "support": None, "resistance": None,
            "pivot": None, "max_pain": None, "vwap": None,
        }

        # Try to get from 15min price action first, fallback to 60min
        for tf in ("15min", "60min", "daily"):
            tf_res = mtf["timeframe_results"].get(tf, {})
            pa = tf_res.get("price_action") if isinstance(tf_res, dict) else None
            if pa and isinstance(pa, dict):
                sr = pa.get("support_resistance", [])
                if sr:
                    supports = [l for l in sr if l.get("type") == "support"]
                    resistances = [l for l in sr if l.get("type") == "resistance"]
                    if supports and levels["support"] is None:
                        levels["support"] = max(s["level"] for s in supports if s["level"] < self.spot_price) if [s for s in supports if s["level"] < self.spot_price] else supports[0]["level"]
                    if resistances and levels["resistance"] is None:
                        levels["resistance"] = min(r["level"] for r in resistances if r["level"] > self.spot_price) if [r for r in resistances if r["level"] > self.spot_price] else resistances[0]["level"]
                pivots = pa.get("pivots", {})
                if pivots and levels["pivot"] is None:
                    levels["pivot"] = pivots.get("pivot")

                tech = tf_res.get("tech")
                if tech and isinstance(tech, dict):
                    details = tech.get("details", {})
                    if details.get("vwap") and levels["vwap"] is None:
                        levels["vwap"] = details["vwap"]

        # Fallbacks from candle data
        if levels["support"] is None and self.candles["daily"]:
            recent_lows = [c["low"] for c in self.candles["daily"][-20:]]
            levels["support"] = min(recent_lows) if recent_lows else self.spot_price - 200
        if levels["resistance"] is None and self.candles["daily"]:
            recent_highs = [c["high"] for c in self.candles["daily"][-20:]]
            levels["resistance"] = max(recent_highs) if recent_highs else self.spot_price + 200
        if levels["vwap"] is None:
            levels["vwap"] = self.spot_price  # fallback

        # Options levels
        if options_result and isinstance(options_result, dict):
            levels["max_pain"] = options_result.get("max_pain", {}).get("max_pain_strike")
            opt_support = options_result.get("support_level")
            opt_resistance = options_result.get("resistance_level")
            if opt_support and (levels["support"] is None or opt_support > levels["support"]):
                levels["support"] = opt_support
            if opt_resistance and (levels["resistance"] is None or opt_resistance < levels["resistance"]):
                levels["resistance"] = opt_resistance

        return levels

    # ------------------------------------------------------------------
    # Risk factors
    # ------------------------------------------------------------------

    def _identify_risk_factors(self, mtf, options_result):
        """Identify potential risk factors and warnings."""
        risks = []
        # Check RSI extremes from 15min
        tf15 = mtf["timeframe_results"].get("15min", {})
        tech15 = tf15.get("tech", {}) if isinstance(tf15, dict) else {}
        details = tech15.get("details", {}) if isinstance(tech15, dict) else {}
        rsi = details.get("rsi")
        if rsi is not None:
            if rsi > 75:
                risks.append(f"RSI overbought at {rsi:.1f} on 15min — reversal risk")
            elif rsi < 25:
                risks.append(f"RSI oversold at {rsi:.1f} on 15min — bounce likely but risky")
        adx = details.get("adx")
        if adx is not None and adx < 20:
            risks.append(f"ADX weak at {adx:.1f} — no clear trend, avoid breakout trades")

        # Conflicting timeframes
        dirs = {tf: mtf["timeframe_results"].get(tf, {}).get("direction", "NEUTRAL")
                for tf in self.TF_WEIGHTS}
        bull = sum(1 for d in dirs.values() if "BULLISH" in d)
        bear = sum(1 for d in dirs.values() if "BEARISH" in d)
        if bull > 0 and bear > 0:
            conflicts = [f"{tf}={d}" for tf, d in dirs.items() if d != "NEUTRAL"]
            risks.append(f"Conflicting timeframes: {', '.join(conflicts)}")

        # PCR extremes
        if options_result and isinstance(options_result, dict):
            pcr = options_result.get("pcr", {})
            oi_pcr = pcr.get("oi_pcr", 1.0) if isinstance(pcr, dict) else 1.0
            if oi_pcr > 1.5:
                risks.append(f"PCR very high ({oi_pcr:.2f}) — extreme bearish sentiment, contrarian bounce possible")
            elif oi_pcr < 0.7:
                risks.append(f"PCR very low ({oi_pcr:.2f}) — extreme bullish sentiment, contrarian selloff possible")

        return risks

    # ------------------------------------------------------------------
    # MAIN METHOD
    # ------------------------------------------------------------------

    def compute_final_conviction(self):
        """Compute the final conviction score combining all layers.

        Returns:
            dict with conviction_score, conviction_level, direction, recommendation,
            layers, timeframe_scores, key_levels, risk_factors, trade_setup.
        """
        try:
            # Step 1: Multi-timeframe analysis (Layers 1, 2, 4)
            mtf = self.multi_timeframe_analysis()

            # Step 2: Options analysis (Layer 3)
            options_result = self.analyze_options()

            # Step 3: Combine layer scores
            # Extract per-layer scores from weighted MTF
            tf_results = mtf["timeframe_results"]

            # Aggregate layer scores across timeframes (weighted)
            tech_score = 0.0
            candle_score = 0.0
            pa_score = 0.0
            for tf_name, weight in self.TF_WEIGHTS.items():
                tfr = tf_results.get(tf_name, {})
                tech_score += (tfr.get("tech", {}).get("score", 0)) * weight
                candle_score += self._normalize(tfr.get("candle", {}).get("score", 0), 3, 5) * weight
                pa_score += self._normalize(tfr.get("price_action", {}).get("score", 0), 2, 5) * weight

            # Options score (already on -3 to +3 scale, normalize to ±5)
            options_score = 0.0
            if options_result and isinstance(options_result, dict) and "error" not in options_result:
                options_score = self._normalize(options_result.get("score", 0), 3, 5)

            # Weighted final score
            if options_result and "error" not in (options_result or {}):
                w = self.LAYER_WEIGHTS_WITH_OPTIONS
                raw_score = (tech_score * w["technical"] +
                             candle_score * w["candlestick"] +
                             options_score * w["options"] +
                             pa_score * w["price_action"])
            else:
                w = self.LAYER_WEIGHTS_NO_OPTIONS
                raw_score = (tech_score * w["technical"] +
                             candle_score * w["candlestick"] +
                             pa_score * w["price_action"])

            # Add alignment bonus
            raw_score += mtf.get("alignment_bonus", 0)

            # Clamp to -10, +10
            conviction_score = self._clamp(round(raw_score, 2), -10, 10)

            # Step 4: Derive direction, level, recommendation
            direction = self._direction_label(conviction_score)
            conviction_level = self._conviction_level(conviction_score)

            # Key levels
            key_levels = self._extract_key_levels(mtf, options_result)
            support = key_levels.get("support") or (self.spot_price - 200)
            resistance = key_levels.get("resistance") or (self.spot_price + 200)

            # Recommendation
            # Trade when conviction is at least LOW-MODERATE (abs >= 1.5)
            if conviction_score >= 1.5:
                action = "BUY_CE"
                sl = support - 50
                target = resistance
            elif conviction_score <= -1.5:
                action = "BUY_PE"
                sl = resistance + 50
                target = support
            else:
                action = "NO_TRADE"
                sl = support - 50
                target = resistance

            risk_distance = abs(self.spot_price - sl)
            reward_distance = abs(target - self.spot_price)
            rr_ratio = round(reward_distance / risk_distance, 2) if risk_distance > 0 else 0.0
            confidence = min(100, abs(conviction_score) * 10)

            # Collect top signals for reasoning
            top_signals = []
            for tf in ("15min", "60min"):
                tfr = tf_results.get(tf, {})
                tech = tfr.get("tech", {})
                if isinstance(tech, dict):
                    for sig in tech.get("signals", [])[:2]:
                        if isinstance(sig, dict):
                            top_signals.append(f"{sig.get('name', '')} {sig.get('signal', '')} ({tf})")
                cand = tfr.get("candle", {})
                if isinstance(cand, dict):
                    for pat in cand.get("patterns_found", [])[:1]:
                        if isinstance(pat, dict):
                            top_signals.append(f"{pat.get('pattern_name', '')} ({tf})")

            if options_result and isinstance(options_result, dict):
                pcr_val = options_result.get("pcr", {}).get("oi_pcr")
                if pcr_val:
                    top_signals.append(f"PCR {pcr_val:.2f}")

            reasoning = f"{direction} setup. Score {conviction_score}/10. " + "; ".join(top_signals[:5])

            # Trade setup string
            if action == "NO_TRADE":
                trade_setup = (f"NO TRADE ({conviction_score}/10 {conviction_level}): "
                               f"Conviction too low. Sit on hands. "
                               f"Support {support:.0f}, Resistance {resistance:.0f}.")
            else:
                option_type = "CE" if action == "BUY_CE" else "PE"
                trade_setup = (
                    f"{direction} SETUP ({conviction_score}/10 {conviction_level}): "
                    f"Buy NIFTY {self.atm_strike} {option_type}. "
                    f"Support {support:.0f}, Resistance {resistance:.0f}. "
                    f"SL at Nifty {sl:.0f}. Target {target:.0f}. R/R 1:{rr_ratio}. "
                    f"Key: {'; '.join(top_signals[:4])}"
                )

            # Risk factors
            risk_factors = self._identify_risk_factors(mtf, options_result)

            # Build timeframe_scores summary
            timeframe_scores = {}
            for tf in self.TF_WEIGHTS:
                tfr = tf_results.get(tf, {})
                timeframe_scores[tf] = {
                    "score": round(tfr.get("combined_score", 0), 2),
                    "direction": tfr.get("direction", "NEUTRAL"),
                }

            # Build layers summary
            layers = {
                "technical": {
                    "score": round(tech_score, 2),
                    "direction": self._direction_label(tech_score),
                    "key_signals": top_signals[:3],
                },
                "candlestick": {
                    "score": round(candle_score, 2),
                    "direction": self._direction_label(candle_score),
                    "patterns": [],
                },
                "options": None,
                "price_action": {
                    "score": round(pa_score, 2),
                    "direction": self._direction_label(pa_score),
                    "trend": tf_results.get("60min", {}).get("price_action", {}).get("trend", {}).get("trend", "UNKNOWN") if isinstance(tf_results.get("60min", {}).get("price_action"), dict) else "UNKNOWN",
                },
            }

            # Candlestick patterns from 15min
            tf15_cand = tf_results.get("15min", {}).get("candle", {})
            if isinstance(tf15_cand, dict):
                layers["candlestick"]["patterns"] = [
                    p.get("pattern_name", "") for p in tf15_cand.get("patterns_found", [])
                    if isinstance(p, dict)
                ]

            # Options layer
            if options_result and isinstance(options_result, dict) and "error" not in options_result:
                layers["options"] = {
                    "score": round(options_score, 2),
                    "direction": options_result.get("direction", "NEUTRAL"),
                    "pcr": options_result.get("pcr", {}).get("oi_pcr"),
                    "support": options_result.get("support_level"),
                    "resistance": options_result.get("resistance_level"),
                    "max_pain": options_result.get("max_pain", {}).get("max_pain_strike"),
                }

            return {
                "conviction_score": conviction_score,
                "conviction_level": conviction_level,
                "direction": direction,
                "recommendation": {
                    "action": action,
                    "confidence": round(confidence, 1),
                    "reasoning": reasoning,
                    "atm_strike": self.atm_strike,
                    "stop_loss_level": round(sl, 0),
                    "target_level": round(target, 0),
                    "risk_reward_ratio": rr_ratio,
                },
                "layers": layers,
                "timeframe_scores": timeframe_scores,
                "key_levels": key_levels,
                "risk_factors": risk_factors,
                "trade_setup": trade_setup,
            }

        except Exception as e:
            # Safe fallback
            return {
                "conviction_score": 0.0,
                "conviction_level": "NEUTRAL",
                "direction": "NEUTRAL",
                "recommendation": {
                    "action": "NO_TRADE",
                    "confidence": 0,
                    "reasoning": f"Analysis failed: {str(e)}",
                    "atm_strike": self.atm_strike,
                    "stop_loss_level": 0,
                    "target_level": 0,
                    "risk_reward_ratio": 0,
                },
                "layers": {"technical": None, "candlestick": None, "options": None, "price_action": None},
                "timeframe_scores": {},
                "key_levels": {},
                "risk_factors": [f"Engine error: {str(e)}"],
                "trade_setup": f"NO TRADE: Engine error — {str(e)}",
            }
