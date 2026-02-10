#!/usr/bin/env python3
"""
OPTIONS ANALYZER — Strike Selection, Greeks Analysis, and Chain Intelligence
Uses Kite MCP to fetch option chains and select optimal strikes for
directional trades based on scanner signals.
"""

import sys
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from pathlib import Path
from collections import defaultdict

# Add execution directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EXECUTION_DIR))

from kite_client import KiteMCPClient


# ──────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────

NIFTY_LOT_SIZE = 25
BANKNIFTY_LOT_SIZE = 15
FINNIFTY_LOT_SIZE = 25

LOT_SIZES = {
    "NIFTY": NIFTY_LOT_SIZE,
    "BANKNIFTY": BANKNIFTY_LOT_SIZE,
    "FINNIFTY": FINNIFTY_LOT_SIZE,
}

STRIKE_INTERVALS = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
}

# NFO underlying mapping
UNDERLYING_MAP = {
    "NIFTY": "NSE:NIFTY 50",
    "BANKNIFTY": "NSE:NIFTY BANK",
    "FINNIFTY": "NSE:NIFTY FIN SERVICE",
}


# ──────────────────────────────────────────────────────────────────
# Options Analyzer
# ──────────────────────────────────────────────────────────────────

class OptionsAnalyzer:
    """
    Analyzes option chains and selects optimal strikes for directional trades.
    Supports both MIS (intraday) and NRML (positional/swing) modes.
    """

    def __init__(self, client: KiteMCPClient):
        self.client = client

    # ── Chain Fetching ──

    def get_option_chain(self, underlying: str = "NIFTY", expiry_preference: str = "weekly") -> Dict:
        """
        Fetch the option chain for an underlying using MCP instrument search.
        
        Args:
            underlying: NIFTY, BANKNIFTY, or FINNIFTY
            expiry_preference: 'weekly' (current week), 'next_week', 'monthly'
            
        Returns:
            Dict with 'calls', 'puts', 'spot_price', 'expiry', 'strikes'
        """
        # 1. Get spot price
        spot_symbol = UNDERLYING_MAP.get(underlying, "NSE:NIFTY 50")
        spot_price = 0
        try:
            ltp_data = self.client.get_ltp([spot_symbol])
            if ltp_data:
                spot_price = ltp_data.get(spot_symbol, {}).get("last_price", 0)
        except Exception as e:
            print(f"⚠️ Could not fetch spot price: {e}")
            return {}

        if not spot_price:
            print("❌ No spot price available")
            return {}

        # 2. Search for F&O instruments
        try:
            # Use underlying filter to get all futures and options
            instruments = self.client.search_instruments(
                query=f"NFO:{underlying}",
                filter_on="underlying",
                limit=500
            )
        except Exception as e:
            print(f"⚠️ Could not fetch instruments: {e}")
            return {}

        if not instruments:
            print(f"❌ No instruments found for {underlying}")
            return {}

        # Handle paginated response
        if isinstance(instruments, dict) and "data" in instruments:
            instruments = instruments["data"]

        # 3. Filter and organize by expiry
        options = []
        expiries = set()
        
        for inst in instruments:
            if not isinstance(inst, dict):
                continue
            
            inst_type = inst.get("instrument_type", "")
            if inst_type not in ("CE", "PE"):
                continue
            
            expiry_str = inst.get("expiry", "")
            if expiry_str:
                expiries.add(expiry_str)
                options.append(inst)

        if not expiries:
            print(f"❌ No option expiries found for {underlying}")
            return {}

        # 4. Select target expiry
        sorted_expiries = sorted(expiries)
        target_expiry = self._select_expiry(sorted_expiries, expiry_preference)
        
        if not target_expiry:
            print(f"❌ Could not determine expiry. Available: {sorted_expiries[:5]}")
            return {}

        # 5. Filter to target expiry and organize
        chain = {"calls": {}, "puts": {}, "spot_price": spot_price, "expiry": target_expiry, "strikes": []}
        
        for opt in options:
            if opt.get("expiry") != target_expiry:
                continue
                
            strike = opt.get("strike", 0)
            inst_type = opt.get("instrument_type", "")
            
            entry = {
                "tradingsymbol": opt.get("tradingsymbol", ""),
                "instrument_token": opt.get("instrument_token", 0),
                "strike": strike,
                "lot_size": opt.get("lot_size", LOT_SIZES.get(underlying, 25)),
                "expiry": target_expiry,
            }
            
            if inst_type == "CE":
                chain["calls"][strike] = entry
            elif inst_type == "PE":
                chain["puts"][strike] = entry

            if strike not in chain["strikes"]:
                chain["strikes"].append(strike)

        chain["strikes"] = sorted(chain["strikes"])
        print(f"✅ Chain loaded: {underlying} | Expiry: {target_expiry} | "
              f"Spot: {spot_price} | Strikes: {len(chain['strikes'])}")
        
        return chain

    def _select_expiry(self, sorted_expiries: List[str], preference: str) -> Optional[str]:
        """Select the appropriate expiry based on preference."""
        today = datetime.now().date()
        
        # Parse expiry dates
        future_expiries = []
        for exp_str in sorted_expiries:
            try:
                # Kite expiry format can vary: "2026-02-13" or "13-02-2026"
                for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
                    try:
                        dt = datetime.strptime(exp_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    continue
                    
                if dt >= today:
                    days_to_expiry = (dt - today).days
                    future_expiries.append((exp_str, dt, days_to_expiry))
            except Exception:
                continue

        if not future_expiries:
            return sorted_expiries[0] if sorted_expiries else None

        future_expiries.sort(key=lambda x: x[2])

        if preference == "weekly":
            # Nearest expiry with >= 1 day
            for exp_str, dt, dte in future_expiries:
                if dte >= 1:
                    return exp_str
            return future_expiries[0][0]
            
        elif preference == "next_week":
            # Second nearest expiry
            if len(future_expiries) >= 2:
                return future_expiries[1][0]
            return future_expiries[0][0]
            
        elif preference == "monthly":
            # Expiry with >= 15 days to go
            for exp_str, dt, dte in future_expiries:
                if dte >= 15:
                    return exp_str
            return future_expiries[-1][0]

        return future_expiries[0][0]

    # ── Strike Selection ──

    def select_strike(self, chain: Dict, direction: Literal["LONG", "SHORT"],
                      strategy: str = "slightly_otm") -> Optional[Dict]:
        """
        Select optimal strike for a directional trade.
        
        Args:
            chain: Option chain from get_option_chain()
            direction: 'LONG' (bullish → buy CE) or 'SHORT' (bearish → buy PE)
            strategy: 'atm', 'slightly_otm', 'deep_otm'
            
        Returns:
            Dict with selected option details and rationale
        """
        spot = chain.get("spot_price", 0)
        strikes = chain.get("strikes", [])
        
        if not spot or not strikes:
            return None
        
        # Find ATM strike (closest to spot)
        atm_strike = min(strikes, key=lambda s: abs(s - spot))
        atm_idx = strikes.index(atm_strike)
        
        if direction == "LONG":
            # Bullish → Buy Call (CE)
            options_dict = chain.get("calls", {})
            
            if strategy == "atm":
                target_strike = atm_strike
            elif strategy == "slightly_otm":
                # 1 strike above spot
                target_idx = min(atm_idx + 1, len(strikes) - 1)
                target_strike = strikes[target_idx]
            elif strategy == "deep_otm":
                target_idx = min(atm_idx + 3, len(strikes) - 1)
                target_strike = strikes[target_idx]
            else:
                target_strike = atm_strike
                
        else:
            # Bearish → Buy Put (PE)
            options_dict = chain.get("puts", {})
            
            if strategy == "atm":
                target_strike = atm_strike
            elif strategy == "slightly_otm":
                target_idx = max(atm_idx - 1, 0)
                target_strike = strikes[target_idx]
            elif strategy == "deep_otm":
                target_idx = max(atm_idx - 3, 0)
                target_strike = strikes[target_idx]
            else:
                target_strike = atm_strike
        
        selected = options_dict.get(target_strike)
        if not selected:
            # Fallback to ATM
            selected = options_dict.get(atm_strike)
            target_strike = atm_strike
            
        if not selected:
            return None
            
        option_type = "CE" if direction == "LONG" else "PE"
        moneyness = "ATM" if target_strike == atm_strike else (
            "OTM" if (direction == "LONG" and target_strike > spot) or 
                     (direction == "SHORT" and target_strike < spot)
            else "ITM"
        )
        
        return {
            "tradingsymbol": selected["tradingsymbol"],
            "instrument_token": selected["instrument_token"],
            "strike": target_strike,
            "option_type": option_type,
            "lot_size": selected.get("lot_size", 25),
            "expiry": selected.get("expiry", ""),
            "spot_price": spot,
            "atm_strike": atm_strike,
            "moneyness": moneyness,
            "strategy": strategy,
            "direction": direction,
        }

    # ── Position Sizing ──

    def calculate_position(self, option_info: Dict, capital: float,
                           risk_percent: float = 2.0,
                           product: str = "NRML") -> Dict:
        """
        Calculate position size based on premium and risk.
        
        Args:
            option_info: Output from select_strike()
            capital: Total available capital
            risk_percent: Max % of capital to risk on this trade
            product: 'NRML' (positional) or 'MIS' (intraday)
            
        Returns:
            Dict with lots, quantity, max_risk, etc.
        """
        lot_size = option_info.get("lot_size", 25)
        
        # We need to get the current premium
        tradingsymbol = option_info.get("tradingsymbol", "")
        premium = 0
        
        try:
            ltp_data = self.client.get_ltp([f"NFO:{tradingsymbol}"])
            if ltp_data:
                premium = ltp_data.get(f"NFO:{tradingsymbol}", {}).get("last_price", 0)
        except Exception as e:
            print(f"⚠️ Could not fetch premium for {tradingsymbol}: {e}")

        max_risk = capital * (risk_percent / 100)
        cost_per_lot = premium * lot_size
        
        if cost_per_lot <= 0:
            return {
                "lots": 0, "quantity": 0, "premium": premium,
                "error": "Could not determine premium"
            }

        # For option buying, max loss = premium paid
        # So risk = cost_per_lot * lots
        max_lots = max(1, int(max_risk / cost_per_lot))
        
        # Also check total capital constraint
        max_lots_by_capital = max(1, int(capital * 0.10 / cost_per_lot))  # Max 10% of capital per trade
        lots = min(max_lots, max_lots_by_capital)
        quantity = lots * lot_size
        total_cost = lots * cost_per_lot

        return {
            "lots": lots,
            "quantity": quantity,
            "lot_size": lot_size,
            "premium": round(premium, 2),
            "cost_per_lot": round(cost_per_lot, 2),
            "total_cost": round(total_cost, 2),
            "max_risk": round(total_cost, 2),  # For buying, max risk = premium paid
            "risk_percent_actual": round((total_cost / capital) * 100, 2),
            "product": product,
        }

    # ── Exit Levels ──

    def calculate_exit_levels(self, premium: float, product: str = "NRML",
                              signal_score: int = 85) -> Dict:
        """
        Calculate exit levels based on premium, not underlying price.
        Uses trailing stop logic designed for multi-day holds.
        
        Args:
            premium: Entry premium price
            product: 'NRML' or 'MIS'
            signal_score: Scanner confidence score (influences targets)
        """
        if product == "NRML":
            # Positional: ride the trend, wider stops
            stop_loss_pct = 0.30       # 30% of premium
            target_1_pct = 0.50        # 50% gain (partial exit or trail)
            target_2_pct = 1.00        # 100% gain (double)
            trail_activation = 0.40    # Start trailing after 40% gain
            trail_distance = 0.20      # Trail 20% below peak
            
            if signal_score >= 90:
                # Exceptional: let it run further
                target_2_pct = 2.00     # 200% (3x)
                trail_distance = 0.15   # Tighter trail to capture more
                
        else:
            # MIS: quick in-out
            stop_loss_pct = 0.25
            target_1_pct = 0.30
            target_2_pct = 0.60
            trail_activation = 0.25
            trail_distance = 0.15

        return {
            "entry_premium": round(premium, 2),
            "stop_loss": round(premium * (1 - stop_loss_pct), 2),
            "stop_loss_pct": stop_loss_pct * 100,
            "target_1": round(premium * (1 + target_1_pct), 2),
            "target_1_pct": target_1_pct * 100,
            "target_2": round(premium * (1 + target_2_pct), 2),
            "target_2_pct": target_2_pct * 100,
            "trail_activation": round(premium * (1 + trail_activation), 2),
            "trail_distance_pct": trail_distance * 100,
            "product": product,
            "strategy_note": (
                "NRML: Hold 2-5 days, trail after 40% gain. "
                "Do NOT set fixed targets — use trailing stop to capture full move."
                if product == "NRML" else
                "MIS: Exit by 2:30 PM. Quick 30-60% premium capture."
            ),
        }

    # ── Open Interest Analysis ──

    def analyze_oi(self, chain: Dict) -> Dict:
        """
        Analyze Open Interest distribution for sentiment.
        Identifies max pain, PCR, and OI buildup zones.
        
        Note: Requires quotes for each strike (expensive API call).
        Use sparingly — once per scan cycle, not per tick.
        """
        spot = chain.get("spot_price", 0)
        strikes = chain.get("strikes", [])
        calls = chain.get("calls", {})
        puts = chain.get("puts", {})

        if not strikes or not spot:
            return {"error": "Insufficient chain data"}

        # Fetch quotes for a range around ATM (±5 strikes)
        atm_strike = min(strikes, key=lambda s: abs(s - spot))
        atm_idx = strikes.index(atm_strike)
        
        range_start = max(0, atm_idx - 5)
        range_end = min(len(strikes), atm_idx + 6)
        target_strikes = strikes[range_start:range_end]

        # Build instrument list for quote fetching
        symbols_to_fetch = []
        for strike in target_strikes:
            if strike in calls:
                symbols_to_fetch.append(f"NFO:{calls[strike]['tradingsymbol']}")
            if strike in puts:
                symbols_to_fetch.append(f"NFO:{puts[strike]['tradingsymbol']}")

        if not symbols_to_fetch:
            return {"error": "No symbols to fetch quotes for"}

        # Fetch quotes in batches
        oi_data = {}
        try:
            quotes = self.client.get_quotes(symbols_to_fetch)
            if quotes:
                for sym, data in quotes.items():
                    oi_data[sym] = {
                        "oi": data.get("oi", 0),
                        "volume": data.get("volume", 0),
                        "last_price": data.get("last_price", 0),
                        "oi_day_change": data.get("oi_day_change", 0),
                    }
        except Exception as e:
            print(f"⚠️ OI fetch error: {e}")
            return {"error": str(e)}

        # Calculate PCR (Put-Call Ratio)
        total_call_oi = 0
        total_put_oi = 0
        max_call_oi_strike = None
        max_put_oi_strike = None
        max_call_oi = 0
        max_put_oi = 0
        
        for strike in target_strikes:
            ce_sym = f"NFO:{calls.get(strike, {}).get('tradingsymbol', '')}"
            pe_sym = f"NFO:{puts.get(strike, {}).get('tradingsymbol', '')}"
            
            ce_oi = oi_data.get(ce_sym, {}).get("oi", 0)
            pe_oi = oi_data.get(pe_sym, {}).get("oi", 0)
            
            total_call_oi += ce_oi
            total_put_oi += pe_oi
            
            if ce_oi > max_call_oi:
                max_call_oi = ce_oi
                max_call_oi_strike = strike
            if pe_oi > max_put_oi:
                max_put_oi = pe_oi
                max_put_oi_strike = strike

        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0
        
        # Sentiment interpretation
        if pcr > 1.2:
            sentiment = "BULLISH"
            sentiment_note = "High PCR suggests put writing (support building)"
        elif pcr < 0.7:
            sentiment = "BEARISH"
            sentiment_note = "Low PCR suggests call writing (resistance building)"
        else:
            sentiment = "NEUTRAL"
            sentiment_note = "Balanced OI distribution"

        return {
            "spot_price": spot,
            "pcr": pcr,
            "sentiment": sentiment,
            "sentiment_note": sentiment_note,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "max_call_oi_strike": max_call_oi_strike,
            "max_put_oi_strike": max_put_oi_strike,
            "resistance_zone": max_call_oi_strike,  # Where writers expect resistance
            "support_zone": max_put_oi_strike,       # Where writers expect support
            "range": f"{max_put_oi_strike} - {max_call_oi_strike}",
        }

    # ── Full Trade Recommendation ──

    def recommend_trade(self, 
                        scanner_signal: Dict,
                        capital: float = 100000,
                        underlying: str = "NIFTY") -> Optional[Dict]:
        """
        Full trade recommendation from scanner signal.
        
        Args:
            scanner_signal: Output from market_scanner with score, direction, etc.
            capital: Available trading capital
            underlying: Which index to trade options on
            
        Returns:
            Complete trade plan or None if no trade
        """
        score = scanner_signal.get("score", 0)
        direction = scanner_signal.get("setup_type", "LONG")

        # --- Mode Selection ---
        if score < 75:
            return {"action": "SKIP", "reason": f"Score {score} below threshold"}
        
        if score >= 85:
            product = "NRML"
            expiry_pref = "monthly" if score >= 90 else "next_week"
            strategy = "slightly_otm" if score < 90 else "atm"
        else:
            product = "MIS"
            expiry_pref = "weekly"
            strategy = "slightly_otm"

        # --- Fetch Chain ---
        chain = self.get_option_chain(underlying, expiry_pref)
        if not chain or not chain.get("strikes"):
            return {"action": "ERROR", "reason": "Could not fetch option chain"}

        # --- Select Strike ---
        option = self.select_strike(chain, direction, strategy)
        if not option:
            return {"action": "ERROR", "reason": "No suitable strike found"}

        # --- Position Sizing ---
        position = self.calculate_position(option, capital, risk_percent=2.0, product=product)
        if position.get("lots", 0) == 0:
            return {"action": "ERROR", "reason": "Position size calculated as 0"}

        # --- Exit Levels ---
        exits = self.calculate_exit_levels(position["premium"], product, score)

        # --- OI Check ---
        oi_analysis = self.analyze_oi(chain)

        return {
            "action": "TRADE",
            "score": score,
            "direction": direction,
            "product": product,
            "underlying": underlying,
            "option": option,
            "position": position,
            "exit_levels": exits,
            "oi_analysis": oi_analysis,
            "summary": (
                f"{'BUY' if direction == 'LONG' else 'BUY'} {option['tradingsymbol']} "
                f"({option['option_type']}) @ ₹{position['premium']} × {position['lots']} lots | "
                f"SL: ₹{exits['stop_loss']} | T1: ₹{exits['target_1']} | T2: ₹{exits['target_2']} | "
                f"Mode: {product} | Risk: ₹{position['total_cost']:,.0f} ({position['risk_percent_actual']:.1f}%)"
            ),
        }


# ──────────────────────────────────────────────────────────────────
# Demo / Test
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  OPTIONS ANALYZER — Demo")
    print("=" * 60)

    client = KiteMCPClient()

    if not client.check_server():
        print("Starting MCP server...")
        if not client.start_server():
            print("❌ Could not start server")
            sys.exit(1)

    if not client.login():
        print("❌ Authentication failed")
        sys.exit(1)

    analyzer = OptionsAnalyzer(client)

    # Simulate a high-conviction bullish signal
    mock_signal = {
        "symbol": "NIFTY 50",
        "score": 88,
        "setup_type": "LONG",
        "trend": "bullish",
    }

    print(f"\nScanner signal: Score {mock_signal['score']} | {mock_signal['setup_type']}")
    
    recommendation = analyzer.recommend_trade(mock_signal, capital=100000)
    
    if recommendation:
        if recommendation["action"] == "TRADE":
            print(f"\n✅ TRADE RECOMMENDATION:")
            print(f"   {recommendation['summary']}")
            print(f"\n   OI Sentiment: {recommendation['oi_analysis'].get('sentiment', 'N/A')}")
            print(f"   PCR: {recommendation['oi_analysis'].get('pcr', 'N/A')}")
            print(f"   Range: {recommendation['oi_analysis'].get('range', 'N/A')}")
            print(f"\n   Strategy Note: {recommendation['exit_levels']['strategy_note']}")
        else:
            print(f"\n⚠️ {recommendation['action']}: {recommendation.get('reason', '')}")
    
    print("\n✅ Demo complete!")
