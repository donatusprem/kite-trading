#!/usr/bin/env python3
"""
RISK MANAGER — Portfolio-Level Risk Management
Real-time portfolio heat, drawdown circuit breakers, Kelly Criterion
position sizing, correlation checks, and sector exposure limits.
"""

import sys
import json
import math
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EXECUTION_DIR))

from kite_client import KiteMCPClient

# Paths
DATA_DIR = SCRIPT_DIR.parent.parent.parent / "_tmp"
RISK_LOG = DATA_DIR / "risk_log.json"
TRADE_HISTORY = SCRIPT_DIR.parent / "journals" / "order_log.json"


# ══════════════════════════════════════════════════════════════════
# Sector Classification (NSE Top Stocks)
# ══════════════════════════════════════════════════════════════════

SECTOR_MAP = {
    # Banking & Financial
    "HDFCBANK": "BANKING", "ICICIBANK": "BANKING", "SBIN": "BANKING",
    "KOTAKBANK": "BANKING", "AXISBANK": "BANKING", "INDUSINDBK": "BANKING",
    "BANKBARODA": "BANKING", "PNB": "BANKING", "BANDHANBNK": "BANKING",
    "IDFCFIRSTB": "BANKING", "BAJFINANCE": "NBFC", "BAJAJFINSV": "NBFC",
    "HDFC": "NBFC", "CHOLAFIN": "NBFC",
    
    # IT
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT",
    "TECHM": "IT", "LTIM": "IT", "COFORGE": "IT", "MPHASIS": "IT",
    
    # Energy / Oil
    "RELIANCE": "ENERGY", "ONGC": "ENERGY", "IOC": "ENERGY",
    "BPCL": "ENERGY", "GAIL": "ENERGY", "ADANIGREEN": "ENERGY",
    "NTPC": "ENERGY", "POWERGRID": "ENERGY", "TATAPOWER": "ENERGY",
    
    # Auto
    "TATAMOTORS": "AUTO", "MARUTI": "AUTO", "M&M": "AUTO",
    "BAJAJ-AUTO": "AUTO", "HEROMOTOCO": "AUTO", "EICHERMOT": "AUTO",
    
    # Metals
    "TATASTEEL": "METALS", "HINDALCO": "METALS", "JSWSTEEL": "METALS",
    "VEDL": "METALS", "COALINDIA": "METALS", "NMDC": "METALS",
    
    # Pharma
    "SUNPHARMA": "PHARMA", "DRREDDY": "PHARMA", "CIPLA": "PHARMA",
    "DIVISLAB": "PHARMA", "APOLLOHOSP": "PHARMA",
    
    # FMCG
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG", "DABUR": "FMCG", "MARICO": "FMCG",
    
    # Index
    "NIFTY": "INDEX", "BANKNIFTY": "INDEX", "FINNIFTY": "INDEX",
}


def get_sector(symbol: str) -> str:
    """Get sector for a symbol. Strips option suffixes."""
    # Strip option-specific suffixes (e.g., NIFTY26FEB23000CE → NIFTY)
    base = symbol.upper()
    for idx_name in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
        if base.startswith(idx_name) and len(base) > len(idx_name):
            base = idx_name
            break
    return SECTOR_MAP.get(base, "OTHER")


# ══════════════════════════════════════════════════════════════════
# Risk Manager
# ══════════════════════════════════════════════════════════════════

class RiskManager:
    """
    Portfolio-level risk management system.
    Monitors capital exposure, enforces limits, and calculates
    optimal position sizes using Kelly Criterion.
    """

    def __init__(self, client: Optional[KiteMCPClient] = None, config: Dict = None):
        self.client = client
        self.config = config or self._default_config()
        self._trade_history: List[Dict] = []
        self._load_trade_history()

    def _default_config(self) -> Dict:
        return {
            # Capital limits
            "total_capital": 100000,          # Total trading capital
            "max_portfolio_heat": 10.0,       # Max % of capital at risk at any time
            "max_single_trade_risk": 2.0,     # Max % per trade
            
            # Drawdown breakers
            "daily_loss_limit": 3.0,          # % of capital — pause trading
            "weekly_loss_limit": 7.0,         # % of capital — stop for the week
            "max_consecutive_losses": 3,       # Pause after N losses in a row
            
            # Sector limits
            "max_sector_exposure_pct": 40,     # Max % in one sector
            "max_correlated_positions": 2,     # Max positions in same sector
            
            # Position limits
            "max_open_positions": 3,
            "max_open_options": 2,
        }

    def _load_trade_history(self):
        """Load past trades for win rate / Kelly calculation."""
        try:
            if TRADE_HISTORY.exists():
                with open(TRADE_HISTORY, "r") as f:
                    self._trade_history = json.load(f)
        except Exception:
            self._trade_history = []

    # ── Portfolio Heat ──

    def calculate_portfolio_heat(self, positions: List[Dict]) -> Dict:
        """
        Portfolio heat = total capital at risk across all open positions.
        Heat > 10% = dangerous, Heat > 15% = circuit breaker territory.
        """
        total_capital = self.config["total_capital"]
        total_risk = 0
        position_risks = []

        for pos in positions:
            qty = abs(pos.get("quantity", 0))
            entry = pos.get("entry_price", 0) or pos.get("average_price", 0)
            sl = pos.get("stop_loss", entry * 0.97)  # Default 3% SL if unknown
            
            if qty == 0 or entry == 0:
                continue
            
            risk_per_unit = abs(entry - sl)
            total_position_risk = risk_per_unit * qty
            
            position_risks.append({
                "symbol": pos.get("symbol", "???"),
                "risk": round(total_position_risk, 2),
                "risk_pct": round(total_position_risk / total_capital * 100, 2),
                "entry": entry,
                "stop_loss": sl,
            })
            total_risk += total_position_risk

        heat_pct = total_risk / total_capital * 100 if total_capital > 0 else 0

        status = "SAFE" if heat_pct < 6 else (
            "ELEVATED" if heat_pct < 10 else (
            "DANGEROUS" if heat_pct < 15 else "CRITICAL"))

        return {
            "total_risk": round(total_risk, 2),
            "heat_pct": round(heat_pct, 2),
            "max_heat": self.config["max_portfolio_heat"],
            "status": status,
            "can_add_position": heat_pct < self.config["max_portfolio_heat"],
            "remaining_risk_budget": round(
                max(0, total_capital * self.config["max_portfolio_heat"] / 100 - total_risk), 2),
            "positions": position_risks,
        }

    # ── Drawdown Circuit Breaker ──

    def check_drawdown(self, session_pnl: float = 0, weekly_pnl: float = 0) -> Dict:
        """
        Check if drawdown limits have been hit.
        Returns trading permission status.
        """
        total_capital = self.config["total_capital"]
        
        daily_loss_pct = abs(min(0, session_pnl)) / total_capital * 100
        weekly_loss_pct = abs(min(0, weekly_pnl)) / total_capital * 100
        
        # Check consecutive losses
        recent_trades = [t for t in self._trade_history[-10:]
                        if t.get("status") in ("PLACED", "COMPLETE")]
        consecutive_losses = 0
        for t in reversed(recent_trades):
            pnl = t.get("realized_pnl", t.get("pnl", 0))
            if pnl is not None and pnl < 0:
                consecutive_losses += 1
            else:
                break

        breakers = []
        can_trade = True
        
        if daily_loss_pct >= self.config["daily_loss_limit"]:
            breakers.append(f"🛑 DAILY LOSS LIMIT: -{daily_loss_pct:.1f}% (limit: {self.config['daily_loss_limit']}%)")
            can_trade = False
            
        if weekly_loss_pct >= self.config["weekly_loss_limit"]:
            breakers.append(f"🛑 WEEKLY LOSS LIMIT: -{weekly_loss_pct:.1f}% (limit: {self.config['weekly_loss_limit']}%)")
            can_trade = False
            
        if consecutive_losses >= self.config["max_consecutive_losses"]:
            breakers.append(f"🛑 CONSECUTIVE LOSSES: {consecutive_losses} (limit: {self.config['max_consecutive_losses']})")
            can_trade = False

        return {
            "can_trade": can_trade,
            "daily_loss_pct": round(daily_loss_pct, 2),
            "weekly_loss_pct": round(weekly_loss_pct, 2),
            "consecutive_losses": consecutive_losses,
            "breakers": breakers,
            "status": "TRADING_ALLOWED" if can_trade else "TRADING_PAUSED",
        }

    # ── Kelly Criterion Position Sizing ──

    def kelly_position_size(self, win_rate: float = None,
                            avg_win: float = None,
                            avg_loss: float = None,
                            premium: float = 0,
                            lot_size: int = 25) -> Dict:
        """
        Kelly Criterion: f* = (bp - q) / b
        where b = avg_win/avg_loss, p = win_rate, q = 1-p
        
        Uses historical trade data if win_rate/avg_win/avg_loss not provided.
        Returns optimal position size (half-Kelly for safety).
        """
        # Calculate from history if not provided
        if win_rate is None or avg_win is None or avg_loss is None:
            stats = self._calculate_trade_stats()
            win_rate = stats.get("win_rate", 0.5)
            avg_win = stats.get("avg_win", 1000)
            avg_loss = stats.get("avg_loss", 500)

        if avg_loss == 0:
            avg_loss = 1  # Prevent division by zero

        b = avg_win / avg_loss  # Win/loss ratio
        p = win_rate
        q = 1 - p

        # Kelly fraction
        kelly_full = (b * p - q) / b
        
        # Half Kelly (safer — reduces variance by 50%, only reduces returns by ~25%)
        kelly_half = kelly_full / 2
        kelly_half = max(0, min(kelly_half, 0.10))  # Cap at 10% of capital

        total_capital = self.config["total_capital"]
        optimal_risk = total_capital * kelly_half
        
        # Convert to lots
        if premium > 0 and lot_size > 0:
            cost_per_lot = premium * lot_size
            optimal_lots = max(1, int(optimal_risk / cost_per_lot))
        else:
            optimal_lots = 1
            cost_per_lot = 0

        return {
            "kelly_full": round(kelly_full * 100, 2),
            "kelly_half": round(kelly_half * 100, 2),
            "optimal_risk": round(optimal_risk, 2),
            "optimal_lots": optimal_lots,
            "total_cost": round(optimal_lots * cost_per_lot, 2) if cost_per_lot > 0 else 0,
            "inputs": {
                "win_rate": round(win_rate, 3),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "win_loss_ratio": round(b, 2),
            },
            "note": (
                "Using Half-Kelly for safety. "
                f"At {win_rate*100:.0f}% win rate and {b:.1f}:1 reward/risk, "
                f"optimal risk is {kelly_half*100:.1f}% of capital per trade."
            )
        }

    def _calculate_trade_stats(self) -> Dict:
        """Calculate win rate and avg win/loss from trade history."""
        completed = [t for t in self._trade_history 
                    if t.get("status") in ("PLACED", "COMPLETE") and
                    "realized_pnl" in t or "pnl" in t]

        if len(completed) < 5:
            # Not enough data — use conservative defaults
            return {"win_rate": 0.50, "avg_win": 1000, "avg_loss": 600,
                    "total_trades": len(completed)}

        wins = []
        losses = []
        for t in completed:
            pnl = t.get("realized_pnl", t.get("pnl", 0))
            if pnl is None:
                continue
            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(abs(pnl))

        total = len(wins) + len(losses)
        win_rate = len(wins) / total if total > 0 else 0.5
        avg_win = sum(wins) / len(wins) if wins else 1000
        avg_loss = sum(losses) / len(losses) if losses else 600

        return {
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "total_trades": total,
            "total_wins": len(wins),
            "total_losses": len(losses),
        }

    # ── Sector / Correlation Check ──

    def check_sector_exposure(self, current_positions: List[Dict],
                               new_symbol: str) -> Dict:
        """
        Check if adding a new position would exceed sector concentration limits.
        Prevents entering 3 banking stocks simultaneously.
        """
        new_sector = get_sector(new_symbol)
        
        sector_counts = defaultdict(int)
        sector_values = defaultdict(float)
        
        for pos in current_positions:
            symbol = pos.get("symbol", "")
            qty = abs(pos.get("quantity", 0))
            price = pos.get("current_price", pos.get("entry_price", 0))
            
            if qty == 0:
                continue
                
            sector = get_sector(symbol)
            sector_counts[sector] += 1
            sector_values[sector] += qty * price

        total_value = sum(sector_values.values())
        
        # Check count limit
        current_count = sector_counts.get(new_sector, 0)
        max_correlated = self.config["max_correlated_positions"]
        
        count_ok = current_count < max_correlated
        
        # Check value limit
        current_pct = (sector_values.get(new_sector, 0) / total_value * 100) if total_value > 0 else 0
        max_pct = self.config["max_sector_exposure_pct"]
        
        value_ok = current_pct < max_pct

        allowed = count_ok and value_ok

        return {
            "allowed": allowed,
            "new_symbol": new_symbol,
            "new_sector": new_sector,
            "current_count": current_count,
            "max_allowed": max_correlated,
            "sector_exposure_pct": round(current_pct, 1),
            "max_exposure_pct": max_pct,
            "reason": (
                "OK — sector exposure within limits" if allowed else
                f"BLOCKED — already {current_count} positions in {new_sector} "
                f"(limit: {max_correlated})" if not count_ok else
                f"BLOCKED — {new_sector} exposure at {current_pct:.0f}% (limit: {max_pct}%)"
            ),
            "all_sectors": dict(sector_counts),
        }

    # ── Position Count Check ──

    def check_position_limits(self, current_positions: List[Dict],
                                is_options: bool = False) -> Dict:
        """Check if we can open a new position."""
        equity_positions = [p for p in current_positions 
                          if p.get("exchange", "NSE") == "NSE" and p.get("quantity", 0) != 0]
        options_positions = [p for p in current_positions 
                           if p.get("exchange", "") == "NFO" and p.get("quantity", 0) != 0]

        total_open = len(equity_positions) + len(options_positions)
        
        if is_options:
            can_open = len(options_positions) < self.config["max_open_options"]
            reason = (
                f"Options: {len(options_positions)}/{self.config['max_open_options']}"
                if can_open else
                f"Max options positions reached ({self.config['max_open_options']})"
            )
        else:
            can_open = total_open < self.config["max_open_positions"]
            reason = (
                f"Positions: {total_open}/{self.config['max_open_positions']}"
                if can_open else
                f"Max positions reached ({self.config['max_open_positions']})"
            )

        return {
            "can_open": can_open,
            "equity_open": len(equity_positions),
            "options_open": len(options_positions),
            "total_open": total_open,
            "reason": reason,
        }

    # ── Full Pre-Trade Risk Check ──

    def full_risk_check(self, new_symbol: str, 
                         positions: List[Dict],
                         session_pnl: float = 0,
                         weekly_pnl: float = 0,
                         is_options: bool = False) -> Dict:
        """
        Run ALL risk checks before allowing a new trade.
        Returns a single pass/fail with all check results.
        """
        checks = {}
        all_passed = True

        # 1. Drawdown breaker
        dd = self.check_drawdown(session_pnl, weekly_pnl)
        checks["drawdown"] = dd
        if not dd["can_trade"]:
            all_passed = False

        # 2. Portfolio heat
        heat = self.calculate_portfolio_heat(positions)
        checks["portfolio_heat"] = heat
        if not heat["can_add_position"]:
            all_passed = False

        # 3. Position limits
        pos_check = self.check_position_limits(positions, is_options)
        checks["position_limits"] = pos_check
        if not pos_check["can_open"]:
            all_passed = False

        # 4. Sector exposure
        sector = self.check_sector_exposure(positions, new_symbol)
        checks["sector_exposure"] = sector
        if not sector["allowed"]:
            all_passed = False

        return {
            "approved": all_passed,
            "status": "✅ APPROVED" if all_passed else "❌ BLOCKED",
            "symbol": new_symbol,
            "checks": checks,
            "blockers": [
                check_name for check_name, result in checks.items()
                if not result.get("can_trade", result.get("can_add_position",
                       result.get("can_open", result.get("allowed", True)))) == True
            ] if not all_passed else [],
        }

    # ── Risk Dashboard Data ──

    def get_risk_dashboard(self, positions: List[Dict],
                           session_pnl: float = 0,
                           weekly_pnl: float = 0) -> Dict:
        """Compile all risk metrics for the dashboard."""
        heat = self.calculate_portfolio_heat(positions)
        drawdown = self.check_drawdown(session_pnl, weekly_pnl)
        trade_stats = self._calculate_trade_stats()
        kelly = self.kelly_position_size()
        pos_limits = self.check_position_limits(positions)

        return {
            "timestamp": datetime.now().isoformat(),
            "portfolio_heat": heat,
            "drawdown": drawdown,
            "trade_stats": trade_stats,
            "kelly": kelly,
            "position_limits": pos_limits,
            "capital": self.config["total_capital"],
        }


# ══════════════════════════════════════════════════════════════════
# Demo
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  RISK MANAGER — Demo")
    print("=" * 60)

    rm = RiskManager(config={
        "total_capital": 100000,
        "max_portfolio_heat": 10.0,
        "max_single_trade_risk": 2.0,
        "daily_loss_limit": 3.0,
        "weekly_loss_limit": 7.0,
        "max_consecutive_losses": 3,
        "max_sector_exposure_pct": 40,
        "max_correlated_positions": 2,
        "max_open_positions": 3,
        "max_open_options": 2,
    })

    # Mock positions
    positions = [
        {"symbol": "NIFTY26FEB23000CE", "quantity": 50, "entry_price": 250, 
         "current_price": 310, "stop_loss": 175, "exchange": "NFO"},
        {"symbol": "RELIANCE", "quantity": 10, "entry_price": 2450,
         "current_price": 2480, "stop_loss": 2400, "exchange": "NSE"},
    ]

    # Portfolio Heat
    heat = rm.calculate_portfolio_heat(positions)
    print(f"\n🌡️ Portfolio Heat: {heat['heat_pct']}% ({heat['status']})")
    print(f"   Total risk: ₹{heat['total_risk']:,.0f} | Remaining budget: ₹{heat['remaining_risk_budget']:,.0f}")

    # Drawdown
    dd = rm.check_drawdown(session_pnl=-1500, weekly_pnl=-4000)
    print(f"\n📉 Drawdown: {dd['status']}")
    print(f"   Daily: -{dd['daily_loss_pct']}% | Weekly: -{dd['weekly_loss_pct']}%")
    if dd["breakers"]:
        for b in dd["breakers"]:
            print(f"   {b}")

    # Kelly
    kelly = rm.kelly_position_size(win_rate=0.58, avg_win=1200, avg_loss=600, premium=250, lot_size=25)
    print(f"\n📊 Kelly Sizing:")
    print(f"   Full Kelly: {kelly['kelly_full']}% | Half Kelly: {kelly['kelly_half']}%")
    print(f"   Optimal: {kelly['optimal_lots']} lots (₹{kelly['total_cost']:,.0f})")
    print(f"   {kelly['note']}")

    # Sector check
    sector = rm.check_sector_exposure(positions, "HDFCBANK")
    print(f"\n🏢 Sector Check for HDFCBANK: {'✅' if sector['allowed'] else '❌'} {sector['reason']}")

    # Full pre-trade check
    full = rm.full_risk_check("BANKNIFTY26FEB45000CE", positions, 
                               session_pnl=-1500, weekly_pnl=-4000, is_options=True)
    print(f"\n🔒 Full Risk Check: {full['status']}")
    if full["blockers"]:
        print(f"   Blockers: {full['blockers']}")

    print("\n✅ Demo complete!")
