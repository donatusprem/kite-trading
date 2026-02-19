#!/usr/bin/env python3
import json
import os
import sys
import time
import traceback
import logging
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
# dashboard_api expects .tmp in root
DATA_DIR = PROJECT_ROOT / ".tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"
LOG_FILE = SCRIPT_DIR / "sync_error.log"

# Setup logging
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
console = logging.StreamHandler(sys.stdout)
logging.getLogger().addHandler(console)

def main():
    print(f"Starting Final Live Sync. Cache: {CACHE_FILE}")
    logging.info("Starting Service")
    
    try:
        DATA_DIR.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Error creating data dir: {e}")

    # Load Token
    try:
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
        api_key = token_data.get("api_key")
        access_token = token_data.get("access_token")
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logging.info(f"Kite Initialized for {token_data.get('user_name')}")
    except Exception as e:
        logging.error(f"Init Failed: {e}")
        return

    while True:
        try:
            # Fetch Data
            positions = kite.positions() # dict
            margins = kite.margins()     # dict
            try:
                holdings = kite.holdings()   # list
            except:
                holdings = []

            # Process Positions
            positions_list = []
            net = positions.get("net", [])
            day = positions.get("day", [])
            # Combine or just use Net? Net is usually sufficient for portfolio
            # Dashboard needs "Active" positions.
            
            total_realized = 0
            total_unrealized = 0
            
            for p in net:
                qty = p.get("quantity", 0)
                # pnl in 'exclude' positions? m2m?
                # Kite 'net' has 'm2m', 'unrealised', 'realised'.
                # 'pnl' field corresponds to 'unrealised' usually.
                
                if qty != 0:
                    positions_list.append({
                        "symbol": p.get("tradingsymbol"),
                        "quantity": qty,
                        "entry_price": p.get("average_price", 0),
                        "current_price": p.get("last_price", 0),
                        "pnl": p.get("m2m", 0), # Using m2m for daily view? Or unrealised?
                        # Use unrealised for total open pnl
                        "pnl_percent": 0, # frontend calc? or calc here
                        "product": p.get("product"),
                        "exchange": p.get("exchange"),
                        "type": "LONG" if qty > 0 else "SHORT"
                    })
                    total_unrealized += p.get("unrealised", 0)
                else:
                    total_realized += p.get("realised", 0)

            # Assemble data
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "is_live": True,
                "source": "DIRECT_FINAL",
                "account": {
                    "user_name": token_data.get("user_name"),
                    "status": "connected"
                },
                "positions": positions_list,
                "margins": {
                    "net": margins.get("equity", {}).get("net", 0),
                    "available": margins.get("equity", {}).get("available", {}).get("cash", 0)
                },
                "holdings": holdings,
                "session_pnl": total_realized + total_unrealized,
                "total_realized": total_realized,
                "total_unrealized": total_unrealized
            }
            
            # Atomic Write
            tmp = CACHE_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(cache_data, f, default=str)
            os.replace(tmp, CACHE_FILE)
            
            logging.info(f"Updated: {len(positions_list)} pos, PnL: {total_unrealized}")
            print(f"Updated: {len(positions_list)} pos", flush=True)
            
            time.sleep(2)
            
        except Exception as e:
            logging.error(f"Loop Error: {e}")
            logging.error(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    main()
