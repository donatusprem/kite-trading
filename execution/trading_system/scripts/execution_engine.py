#!/usr/bin/env python3
"""
EXECUTION ENGINE — Real Order Placement via Kite MCP
Bridges trade signals from the orchestrator/options analyzer to actual orders.
Includes safety checks, duplicate prevention, and order tracking.
"""

import sys
import json
import time
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(EXECUTION_DIR))

from kite_client import KiteMCPClient

# Paths
JOURNALS_DIR = SCRIPT_DIR.parent / "journals"
ORDER_LOG = JOURNALS_DIR / "order_log.json"
JOURNALS_DIR.mkdir(exist_ok=True)


class ExecutionEngine:
    """
    Handles real order placement with safety guardrails.
    Prevents duplicate orders, enforces daily limits, and logs everything.
    """

    def __init__(self, client: KiteMCPClient, config: Dict = None):
        self.client = client
        self.config = config or self._default_config()
        self.orders_today: List[Dict] = []
        self.daily_loss = 0.0
        self._load_order_log()

    def _default_config(self) -> Dict:
        return {
            "max_trades_per_day": 5,
            "max_loss_per_day": 5000,        # ₹5,000 max daily loss
            "max_position_value": 50000,      # ₹50,000 per position
            "require_confirmation": False,     # Set True for manual approval
            "allowed_exchanges": ["NSE", "NFO"],
            "allowed_products": ["CNC", "MIS", "NRML"],
            "dry_run": False,                 # Set True to simulate without placing
        }

    def _load_order_log(self):
        """Load today's orders from the journal."""
        try:
            if ORDER_LOG.exists():
                with open(ORDER_LOG, "r") as f:
                    all_orders = json.load(f)
                today_str = date.today().isoformat()
                self.orders_today = [
                    o for o in all_orders
                    if o.get("date") == today_str
                ]
        except Exception:
            self.orders_today = []

    def _save_order(self, order: Dict):
        """Append order to journal."""
        try:
            all_orders = []
            if ORDER_LOG.exists():
                with open(ORDER_LOG, "r") as f:
                    all_orders = json.load(f)

            all_orders.append(order)
            self.orders_today.append(order)

            with open(ORDER_LOG, "w") as f:
                json.dump(all_orders, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Could not save order log: {e}")

    # ── Safety Checks ──

    def pre_trade_checks(self, trade_plan: Dict) -> Dict:
        """
        Run all safety checks before placing an order.
        Returns: {passed: bool, reason: str}
        """
        # 1. Daily trade limit
        if len(self.orders_today) >= self.config["max_trades_per_day"]:
            return {"passed": False, "reason": f"Daily trade limit reached ({self.config['max_trades_per_day']})"}

        # 2. Daily loss limit
        if self.daily_loss >= self.config["max_loss_per_day"]:
            return {"passed": False, "reason": f"Daily loss limit reached (₹{self.daily_loss:,.0f})"}

        # 3. Position value check
        total_cost = trade_plan.get("position", {}).get("total_cost", 0)
        if total_cost > self.config["max_position_value"]:
            return {"passed": False, "reason": f"Position value ₹{total_cost:,.0f} exceeds limit ₹{self.config['max_position_value']:,.0f}"}

        # 4. Exchange check
        exchange = trade_plan.get("option", {}).get("exchange", "NFO")
        # For options, exchange is always NFO
        if "NFO" not in self.config["allowed_exchanges"]:
            return {"passed": False, "reason": f"Exchange NFO not in allowed list"}

        # 5. Duplicate check — same symbol in last 5 minutes
        tradingsymbol = trade_plan.get("option", {}).get("tradingsymbol", "")
        for order in self.orders_today[-5:]:
            if (order.get("tradingsymbol") == tradingsymbol and 
                order.get("status") in ("PLACED", "COMPLETE")):
                order_time = order.get("timestamp", "")
                if order_time:
                    try:
                        dt = datetime.fromisoformat(order_time)
                        if (datetime.now() - dt).total_seconds() < 300:
                            return {"passed": False, "reason": f"Duplicate: {tradingsymbol} ordered within last 5 min"}
                    except Exception:
                        pass

        # 6. Margin check
        try:
            margins = self.client.get_margins()
            if margins:
                equity = margins.get("equity", {})
                available = equity.get("available", {}).get("cash", 0) or equity.get("net", 0)
                if total_cost > available * 0.8:  # Don't use more than 80% of available
                    return {"passed": False, "reason": f"Insufficient margin: need ₹{total_cost:,.0f}, have ₹{available:,.0f}"}
        except Exception as e:
            print(f"⚠️ Could not verify margins: {e}")

        return {"passed": True, "reason": "All checks passed"}

    # ── Order Placement ──

    def place_options_order(self, trade_plan: Dict) -> Dict:
        """
        Place an options order based on the trade plan from OptionsAnalyzer.
        
        Args:
            trade_plan: Output from OptionsAnalyzer.recommend_trade()
            
        Returns:
            Order result dict
        """
        if trade_plan.get("action") != "TRADE":
            return {"status": "SKIPPED", "reason": trade_plan.get("reason", "No trade signal")}

        option = trade_plan.get("option", {})
        position = trade_plan.get("position", {})
        exits = trade_plan.get("exit_levels", {})

        tradingsymbol = option.get("tradingsymbol", "")
        quantity = position.get("quantity", 0)
        product = position.get("product", "NRML")

        if not tradingsymbol or quantity <= 0:
            return {"status": "ERROR", "reason": "Invalid symbol or quantity"}

        # --- Safety Checks ---
        checks = self.pre_trade_checks(trade_plan)
        if not checks["passed"]:
            print(f"❌ Pre-trade check failed: {checks['reason']}")
            return {"status": "BLOCKED", "reason": checks["reason"]}

        # --- Confirmation ---
        if self.config["require_confirmation"]:
            print(f"\n🔔 CONFIRM ORDER:")
            print(f"   BUY {tradingsymbol} × {quantity} ({product})")
            print(f"   Premium: ₹{position.get('premium', 0):.2f}")
            print(f"   Total: ₹{position.get('total_cost', 0):,.2f}")
            print(f"   SL: ₹{exits.get('stop_loss', 0):.2f} | T1: ₹{exits.get('target_1', 0):.2f}")
            confirm = input("   Type 'yes' to confirm: ").strip().lower()
            if confirm != "yes":
                return {"status": "CANCELLED", "reason": "User rejected"}

        # --- Place Order ---
        order_record = {
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "tradingsymbol": tradingsymbol,
            "exchange": "NFO",
            "transaction_type": "BUY",
            "quantity": quantity,
            "product": product,
            "order_type": "MARKET",
            "premium_at_entry": position.get("premium", 0),
            "total_cost": position.get("total_cost", 0),
            "exit_levels": exits,
            "signal_score": trade_plan.get("score", 0),
            "direction": trade_plan.get("direction", ""),
            "underlying": trade_plan.get("underlying", ""),
        }

        if self.config["dry_run"]:
            order_record["status"] = "DRY_RUN"
            order_record["order_id"] = f"DRY_{int(time.time())}"
            print(f"🏜️ DRY RUN: Would place BUY {tradingsymbol} × {quantity} @ MARKET ({product})")
            self._save_order(order_record)
            return order_record

        try:
            result = self.client.place_order(
                tradingsymbol=tradingsymbol,
                transaction_type="BUY",
                quantity=quantity,
                product=product,
                order_type="MARKET",
                exchange="NFO",
                variety="regular",
                validity="DAY"
            )

            if result:
                order_id = result.get("order_id", "unknown")
                order_record["status"] = "PLACED"
                order_record["order_id"] = order_id
                print(f"✅ Order Placed! ID: {order_id} | {tradingsymbol} × {quantity} ({product})")
            else:
                order_record["status"] = "FAILED"
                order_record["error"] = "No response from broker"
                print(f"❌ Order failed: No response")

        except Exception as e:
            order_record["status"] = "ERROR"
            order_record["error"] = str(e)
            print(f"❌ Order error: {e}")

        self._save_order(order_record)
        return order_record

    def place_exit_order(self, tradingsymbol: str, quantity: int,
                         product: str = "NRML", reason: str = "manual") -> Dict:
        """
        Place an exit (SELL) order for an existing position.
        """
        order_record = {
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "tradingsymbol": tradingsymbol,
            "exchange": "NFO",
            "transaction_type": "SELL",
            "quantity": quantity,
            "product": product,
            "order_type": "MARKET",
            "exit_reason": reason,
        }

        if self.config["dry_run"]:
            order_record["status"] = "DRY_RUN"
            print(f"🏜️ DRY RUN: Would SELL {tradingsymbol} × {quantity} ({reason})")
            self._save_order(order_record)
            return order_record

        try:
            result = self.client.place_order(
                tradingsymbol=tradingsymbol,
                transaction_type="SELL",
                quantity=quantity,
                product=product,
                order_type="MARKET",
                exchange="NFO",
                variety="regular",
                validity="DAY"
            )

            if result:
                order_id = result.get("order_id", "unknown")
                order_record["status"] = "PLACED"
                order_record["order_id"] = order_id
                print(f"✅ Exit Placed! ID: {order_id} | SELL {tradingsymbol} × {quantity} | Reason: {reason}")
            else:
                order_record["status"] = "FAILED"
                print(f"❌ Exit failed: No response")

        except Exception as e:
            order_record["status"] = "ERROR"
            order_record["error"] = str(e)
            print(f"❌ Exit error: {e}")

        self._save_order(order_record)
        return order_record

    # ── Position Monitoring ──

    def monitor_option_positions(self) -> List[Dict]:
        """
        Check all open option positions against their exit levels.
        Returns list of exit signals.
        """
        exit_signals = []

        try:
            positions = self.client.get_positions()
            if not positions:
                return []

            if isinstance(positions, dict) and "data" in positions:
                positions = positions["data"]

            for pos in positions:
                if not isinstance(pos, dict):
                    continue

                qty = pos.get("quantity", 0) or pos.get("net_quantity", 0)
                if qty == 0:
                    continue

                symbol = pos.get("tradingsymbol", "")
                ltp = pos.get("last_price", 0)
                entry = pos.get("average_price", 0)
                product = pos.get("product", "")
                exchange = pos.get("exchange", "")

                # Only manage NFO positions
                if exchange != "NFO":
                    continue

                # Find matching order in log for exit levels
                matching_order = None
                for order in reversed(self.orders_today):
                    if (order.get("tradingsymbol") == symbol and 
                        order.get("transaction_type") == "BUY" and
                        order.get("status") in ("PLACED", "COMPLETE", "DRY_RUN")):
                        matching_order = order
                        break

                if not matching_order:
                    continue

                exits = matching_order.get("exit_levels", {})
                sl = exits.get("stop_loss", 0)
                t1 = exits.get("target_1", 0)
                trail_activation = exits.get("trail_activation", 0)

                pnl_pct = ((ltp - entry) / entry * 100) if entry > 0 else 0

                # Check exit conditions
                if ltp <= sl:
                    exit_signals.append({
                        "symbol": symbol,
                        "quantity": abs(qty),
                        "product": product,
                        "reason": f"STOP LOSS hit (₹{ltp:.2f} ≤ ₹{sl:.2f})",
                        "ltp": ltp,
                        "entry": entry,
                        "pnl_pct": round(pnl_pct, 2),
                    })
                elif ltp >= trail_activation:
                    # Trailing stop logic
                    trail_pct = exits.get("trail_distance_pct", 20) / 100
                    trail_sl = ltp * (1 - trail_pct)
                    
                    # Update the trailing stop in the order record
                    if trail_sl > sl:
                        matching_order["exit_levels"]["stop_loss"] = round(trail_sl, 2)
                        print(f"📈 Trailing SL updated for {symbol}: ₹{sl:.2f} → ₹{trail_sl:.2f}")

                    exit_signals.append({
                        "symbol": symbol,
                        "quantity": abs(qty),
                        "product": product,
                        "reason": f"TRAILING (LTP ₹{ltp:.2f}, trail SL ₹{trail_sl:.2f})",
                        "ltp": ltp,
                        "entry": entry,
                        "pnl_pct": round(pnl_pct, 2),
                        "action": "UPDATE_SL",  # Don't exit yet, just update SL
                    })

        except Exception as e:
            print(f"⚠️ Position monitor error: {e}")

        return exit_signals

    # ── Summary ──

    def get_daily_summary(self) -> Dict:
        """Get today's trading summary."""
        placed = [o for o in self.orders_today if o.get("status") in ("PLACED", "COMPLETE")]
        total_deployed = sum(o.get("total_cost", 0) for o in placed if o.get("transaction_type") == "BUY")
        
        return {
            "date": date.today().isoformat(),
            "total_orders": len(self.orders_today),
            "placed": len(placed),
            "total_deployed": round(total_deployed, 2),
            "daily_loss": round(self.daily_loss, 2),
            "remaining_trades": self.config["max_trades_per_day"] - len(placed),
        }


# ──────────────────────────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  EXECUTION ENGINE — Demo (Dry Run)")
    print("=" * 60)

    # Demo with dry run enabled
    engine = ExecutionEngine(
        client=None,  # Would be KiteMCPClient() in real usage
        config={"dry_run": True, "max_trades_per_day": 5, "max_loss_per_day": 5000,
                "max_position_value": 50000, "require_confirmation": False,
                "allowed_exchanges": ["NSE", "NFO"], "allowed_products": ["CNC", "MIS", "NRML"]}
    )

    mock_trade_plan = {
        "action": "TRADE",
        "score": 88,
        "direction": "LONG",
        "product": "NRML",
        "underlying": "NIFTY",
        "option": {
            "tradingsymbol": "NIFTY26FEB23000CE",
            "instrument_token": 12345,
            "strike": 23000,
            "option_type": "CE",
            "lot_size": 25,
        },
        "position": {
            "lots": 2,
            "quantity": 50,
            "premium": 250.0,
            "total_cost": 12500.0,
        },
        "exit_levels": {
            "stop_loss": 175.0,
            "target_1": 375.0,
            "target_2": 500.0,
            "trail_activation": 350.0,
            "trail_distance_pct": 20,
        },
    }

    result = engine.place_options_order(mock_trade_plan)
    print(f"\nResult: {result['status']}")
    print(f"Summary: {engine.get_daily_summary()}")
    print("\n✅ Demo complete!")
