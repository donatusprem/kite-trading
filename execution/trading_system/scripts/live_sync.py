#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - LIVE SYNC (REAL KITE VERSION)
Bridges Kite MCP Server with Dashboard by updating live_cache.json
Uses KiteMCPClient for real account data, falls back to mock if unavailable.
"""

import json
import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LiveSync")

# Add execution directory to path so we can import kite_client
SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTION_DIR = SCRIPT_DIR.parent.parent  # trading_system/scripts -> trading_system -> execution
sys.path.insert(0, str(EXECUTION_DIR))

from kite_client import KiteMCPClient

# Paths
ROOT_DIR = EXECUTION_DIR.parent  # execution -> project root
DATA_DIR = ROOT_DIR / "_tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"


# ──────────────────────────────────────────────────────────────────
# Real Kite Data Provider
# ──────────────────────────────────────────────────────────────────

class KiteLiveProvider:
    """Fetches real account data via the Kite MCP Server."""

    def __init__(self, client: KiteMCPClient):
        self.client = client
        self._profile = None
        self._last_full_fetch = 0
        self._cached_holdings = []

    def fetch_profile_once(self):
        """Profile rarely changes, cache it."""
        if not self._profile:
            try:
                self._profile = self.client.get_profile() or {}
                logger.info(f"Profile loaded: {self._profile.get('user_name')} ({self._profile.get('user_id')})")
            except Exception as e:
                logger.warning(f"Could not fetch profile: {e}")
                self._profile = {"user_name": "Unknown", "user_id": "N/A"}
        return self._profile

    def generate(self):
        """
        Fetch ALL live data from Kite and return a unified dict
        that dashboard_api.py can consume from live_cache.json.
        """
        profile = self.fetch_profile_once()

        # --- Margins ---
        margins_data = {"net": 0, "available": 0, "used": 0}
        try:
            margins_raw = self.client.get_margins()
            if margins_raw:
                equity = margins_raw.get("equity", {})
                commodity = margins_raw.get("commodity", {})
                
                eq_available = equity.get("available", {})
                eq_utilised = equity.get("utilised", {})
                
                net = eq_available.get("live_balance", 0) or equity.get("net", 0)
                available = eq_available.get("cash", 0) or net
                used = sum(v for k, v in eq_utilised.items() if isinstance(v, (int, float)))
                
                margins_data = {
                    "net": round(net, 2),
                    "available": round(available, 2),
                    "used": round(used, 2)
                }
        except Exception as e:
            logger.warning(f"Margins fetch error: {e}")

        # --- Positions ---
        positions_data = []
        session_pnl = 0
        total_unrealized = 0
        total_realized = 0
        try:
            positions_raw = self.client.get_positions()
            if positions_raw and isinstance(positions_raw, list):
                for pos in positions_raw:
                    qty = pos.get("quantity", 0) or pos.get("net_quantity", 0)
                    if qty == 0:
                        # Closed position, only has realized PnL
                        total_realized += pos.get("pnl", 0) or pos.get("realised", 0)
                        continue

                    entry = pos.get("average_price", 0)
                    ltp = pos.get("last_price", 0)
                    pnl = pos.get("pnl", 0) or pos.get("unrealised", 0)
                    
                    if entry > 0 and abs(qty) > 0:
                        pnl_pct = ((ltp - entry) / entry) * 100 if entry > 0 else 0
                        if qty < 0:
                            pnl_pct = -pnl_pct
                    else:
                        pnl_pct = 0

                    total_unrealized += pnl

                    positions_data.append({
                        "symbol": pos.get("tradingsymbol", "???"),
                        "quantity": qty,
                        "entry_price": round(entry, 2),
                        "current_price": round(ltp, 2),
                        "pnl": round(pnl, 2),
                        "pnl_percent": round(pnl_pct, 2),
                        "type": "LONG" if qty > 0 else "SHORT",
                        "product": pos.get("product", ""),
                        "exchange": pos.get("exchange", ""),
                        "instrument_type": pos.get("instrument_type", "EQ"),
                    })
                    
                session_pnl = total_realized + total_unrealized
        except Exception as e:
            logger.warning(f"Positions fetch error: {e}")

        # --- Holdings (fetch less frequently, every 60s) ---
        now = time.time()
        if now - self._last_full_fetch > 60:
            try:
                holdings_raw = self.client.get_holdings()
                if holdings_raw and isinstance(holdings_raw, list):
                    self._cached_holdings = []
                    for h in holdings_raw:
                        self._cached_holdings.append({
                            "symbol": h.get("tradingsymbol", ""),
                            "quantity": h.get("quantity", 0),
                            "average_price": round(h.get("average_price", 0), 2),
                            "current_price": round(h.get("last_price", 0), 2),
                            "pnl": round(h.get("pnl", 0), 2),
                        })
                self._last_full_fetch = now
            except Exception as e:
                logger.warning(f"Holdings fetch error: {e}")

        # --- NIFTY 50 LTP ---
        nifty_ltp = 0
        try:
            ltp_data = self.client.get_ltp(["NSE:NIFTY 50"])
            if ltp_data:
                nifty_ltp = ltp_data.get("NSE:NIFTY 50", {}).get("last_price", 0)
        except Exception as e:
            logger.warning(f"NIFTY LTP fetch error: {e}")

        # --- Assemble Cache ---
        data = {
            "timestamp": datetime.now().isoformat(),
            "is_live": True,
            "source": "KITE_MCP_SERVER",
            "account": {
                "user_name": profile.get("user_name", ""),
                "user_id": profile.get("user_id", ""),
                "broker": "Zerodha",
                "status": "connected"
            },
            "margins": margins_data,
            "positions": positions_data,
            "session_pnl": round(session_pnl, 2),
            "total_realized": round(total_realized, 2),
            "total_unrealized": round(total_unrealized, 2),
            "nifty_ltp": round(nifty_ltp, 2),
            "holdings": self._cached_holdings,
        }
        return data


# ──────────────────────────────────────────────────────────────────
# Mock Data Generator (Fallback)
# ──────────────────────────────────────────────────────────────────

class MockDataGenerator:
    def __init__(self):
        self.base_pnl = 0
        self.positions = [
            {"symbol": "RELIANCE", "qty": 10, "entry": 2450.0, "type": "LONG"},
            {"symbol": "TATASTEEL", "qty": 100, "entry": 145.50, "type": "LONG"},
            {"symbol": "INFY", "qty": -15, "entry": 1620.0, "type": "SHORT"}
        ]
        
    def generate(self):
        total_pnl = 0
        pos_data = []
        
        for p in self.positions:
            change = random.uniform(-0.005, 0.005)
            current_price = p["entry"] * (1 + change + ((random.random() - 0.5) * 0.02))
            
            pnl = (current_price - p["entry"]) * p["qty"]
            if p["type"] == "SHORT":
                pnl = (p["entry"] - current_price) * abs(p["qty"])
                
            total_pnl += pnl
            
            pos_data.append({
                "symbol": p["symbol"],
                "quantity": p["qty"],
                "entry_price": p["entry"],
                "current_price": round(current_price, 2),
                "pnl": round(pnl, 2),
                "pnl_percent": round((pnl / (p["entry"] * abs(p["qty"]))) * 100, 2),
                "type": p["type"],
                "product": "MIS",
                "exchange": "NSE"
            })

        nifty_ltp = 22150.0 + (random.random() * 100 - 50)

        data = {
            "timestamp": datetime.now().isoformat(),
            "is_live": False,
            "source": "MOCK_SIMULATION",
            "account": {
                "user_name": "Demo User",
                "user_id": "DEMO01",
                "broker": "Zerodha (Simulated)",
                "status": "simulated"
            },
            "margins": {"net": 150000.0, "available": 125000.0, "used": 25000.0},
            "positions": pos_data,
            "session_pnl": round(total_pnl, 2),
            "total_realized": 0,
            "total_unrealized": round(total_pnl, 2),
            "nifty_ltp": round(nifty_ltp, 2),
            "holdings": []
        }
        return data


# ──────────────────────────────────────────────────────────────────
# Main Sync Logic
# ──────────────────────────────────────────────────────────────────

def write_cache(data):
    """Atomic write to cache file."""
    DATA_DIR.mkdir(exist_ok=True)
    temp_file = CACHE_FILE.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(data, f, indent=2)
    temp_file.replace(CACHE_FILE)


def main():
    logger.info("=" * 50)
    logger.info("  LIVE SYNC SERVICE — Starting")
    logger.info("=" * 50)

    DATA_DIR.mkdir(exist_ok=True)
    provider = None

    # --- Try connecting to real Kite MCP ---
    try:
        client = KiteMCPClient()
        
        if not client.check_server():
            logger.info("MCP Server not running. Attempting to start...")
            if not client.start_server():
                raise ConnectionError("Could not start MCP server")

        if not client.login():
            raise ConnectionError("Authentication failed")
        
        provider = KiteLiveProvider(client)
        logger.info("✅ Connected to LIVE Kite via MCP")
        
    except Exception as e:
        logger.warning(f"Could not connect to Kite: {e}")
        logger.warning("⚠️  Falling back to MOCK DATA MODE")
        provider = MockDataGenerator()

    # --- Sync Loop ---
    update_interval = 2  # seconds
    error_count = 0
    MAX_ERRORS = 10

    while True:
        try:
            data = provider.generate()
            write_cache(data)
            
            source = data.get("source", "unknown")
            pnl = data.get("session_pnl", 0)
            n_pos = len(data.get("positions", []))
            logger.info(
                f"[{source}] Updated | PnL: ₹{pnl:,.2f} | "
                f"Positions: {n_pos} | {datetime.now().strftime('%H:%M:%S')}"
            )
            
            error_count = 0  # Reset on success
            time.sleep(update_interval)
            
        except KeyboardInterrupt:
            logger.info("Stopping Sync...")
            break
        except Exception as e:
            error_count += 1
            logger.error(f"Sync error ({error_count}/{MAX_ERRORS}): {e}")
            
            if error_count >= MAX_ERRORS:
                logger.error("Too many consecutive errors. Switching to mock mode.")
                provider = MockDataGenerator()
                error_count = 0
            
            time.sleep(5)


if __name__ == "__main__":
    main()
