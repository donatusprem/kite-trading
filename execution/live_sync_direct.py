#!/usr/bin/env python3
"""
DIRECT KITE SYNC SERVICE
Uses official kiteconnect library with persistent token.
"""
import json
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LiveSyncDirect")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent 
# dashboard_api expects ROOT/.tmp/live_cache.json
# SCRIPT_DIR is 'execution'. Parent is 'AI Trading'.
DATA_DIR = PROJECT_ROOT / ".tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"

def load_token():
    if not TOKEN_FILE.exists():
        logger.error(f"Token file not found: {TOKEN_FILE}")
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading token: {e}")
        return None

def main():
    logger.info("Starting Direct Sync Service...")
    DATA_DIR.mkdir(exist_ok=True)

    # 1. Load Configuration
    token_data = load_token()
    if not token_data:
        sys.exit(1)

    api_key = token_data.get("api_key")
    access_token = token_data.get("access_token")
    
    if not api_key or not access_token:
        logger.error("Invalid token data")
        sys.exit(1)

    # 2. Initialize Kite
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logger.info(f"Initialized KiteConnect for user: {token_data.get('user_name')}")
    except Exception as e:
        logger.error(f"Kite Init Failed: {e}")
        sys.exit(1)

    # 3. Cache Data
    profile = {
        "user_name": token_data.get("user_name", "Trader"),
        "user_id": token_data.get("user_id", "Unknown"),
        "broker": "Zerodha (Direct)",
        "status": "connected"
    }

    # 4. Sync Loop
    while True:
        try:
            # Fetch Data
            # Note: KiteConnect methods raise exceptions on failure
            positions_raw = kite.positions()
            holdings_raw = kite.holdings()
            margins_raw = kite.margins()
            
            # --- Process Positions ---
            positions_data = []
            session_pnl = 0
            total_realized = 0
            total_unrealized = 0

            # Kite .positions() returns {'net': [], 'day': []}
            net_positions = positions_raw.get("net", [])
            
            for pos in net_positions:
                qty = pos.get("quantity", 0)
                
                # PnL
                pnl = pos.get("pnl", 0)
                m2m = pos.get("m2m", 0) 
                # realized usually not in 'net' unless explicit. 
                # 'net' contains open and closed positions for the day + carry forward.
                # realised pnl is in 'realised'.
                
                realized_pnl = pos.get("realised", 0)
                unrealized_pnl = pos.get("unrealised", 0) or m2m # m2m is usually unrealized for the day?
                
                # If quantity is 0, it's closed
                if qty == 0:
                    total_realized += realized_pnl
                    continue
                
                total_unrealized += unrealized_pnl
                
                positions_data.append({
                    "symbol": pos.get("tradingsymbol"),
                    "quantity": qty,
                    "entry_price": pos.get("average_price", 0),
                    "current_price": pos.get("last_price", 0),
                    "pnl": unrealized_pnl, # Dashboard expects open pnl here
                    "pnl_percent": 0, # Calculate if needed, but UI might compute it? 
                    # UI expects 'pnl_percent'.
                    # Let's calculate:
                    "type": "LONG" if qty > 0 else "SHORT",
                    "product": pos.get("product"),
                    "exchange": pos.get("exchange"),
                    "instrument_type": pos.get("instrument_type")
                })
                
                # Add pct calculation
                if positions_data[-1]["entry_price"] > 0:
                     diff = positions_data[-1]["current_price"] - positions_data[-1]["entry_price"]
                     pct = (diff / positions_data[-1]["entry_price"]) * 100
                     if qty < 0: pct = -pct
                     positions_data[-1]["pnl_percent"] = pct

            session_pnl = total_realized + total_unrealized

            # --- Process Margins ---
            equity = margins_raw.get("equity", {})
            margins_data = {
                "net": equity.get("net", 0),
                "available": equity.get("available", {}).get("cash", 0),
                "used": equity.get("utilised", {}).get("debits", 0)
            }

            # --- Process Holdings ---
            holdings_data = []
            for h in holdings_raw:
                holdings_data.append({
                    "symbol": h.get("tradingsymbol"),
                    "quantity": h.get("quantity", 0),
                    "average_price": h.get("average_price", 0),
                    "current_price": h.get("last_price", 0),
                    "pnl": h.get("pnl", 0)
                })

            # --- Assemble Cache ---
            data = {
                "timestamp": datetime.now().isoformat(),
                "is_live": True,
                "source": "KITE_CONNECT_DIRECT",
                "account": profile,
                "margins": margins_data,
                "positions": positions_data,
                "session_pnl": round(session_pnl, 2),
                "total_realized": round(total_realized, 2),
                "total_unrealized": round(total_unrealized, 2),
                "nifty_ltp": 0, 
                "holdings": holdings_data
            }
            
            # Atomic Write
            temp_file = CACHE_FILE.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(CACHE_FILE)
            
            logger.info(f"Updated cache | PnL: {session_pnl:.2f} | Pos: {len(positions_data)}")
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Sync Loop Error: {e}")
            # If token invalid, we should exit? Or retry?
            # User might need to re-login.
            # For now, sleep.
            time.sleep(5)

if __name__ == "__main__":
    main()
