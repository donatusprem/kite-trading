#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
DATA_DIR = PROJECT_ROOT / ".tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"

def main():
    print(f"Loading token from {TOKEN_FILE}")
    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)
        
    api_key = token_data.get("api_key")
    access_token = token_data.get("access_token")
    
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    
    print("Starting Loop...")
    while True:
        try:
            # print("Fetching...")
            positions = kite.positions()
            margins = kite.margins()
            
            # Process
            positions_list = []
            net = positions.get("net", [])
            total_unrealized = 0
            total_realized = 0
            
            for p in net:
                qty = p.get("quantity", 0)
                unrealized = p.get("unrealised", 0) or p.get("m2m", 0)
                if qty != 0:
                    positions_list.append({
                        "symbol": p.get("tradingsymbol"),
                        "quantity": qty,
                        "entry_price": p.get("average_price", 0),
                        "current_price": p.get("last_price", 0),
                        "pnl": unrealized,
                        "pnl_percent": 0,
                        "product": p.get("product"),
                        "exchange": p.get("exchange"),
                        "type": "LONG" if qty > 0 else "SHORT"
                    })
                    total_unrealized += unrealized
                else:
                    total_realized += p.get("realised", 0)

            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "is_live": True,
                "source": "SYNC_LOOP_V2",
                "account": {"user_name": token_data.get("user_name"), "status": "connected"},
                "positions": positions_list,
                "margins": {
                    "net": margins.get("equity", {}).get("net", 0),
                    "available": margins.get("equity", {}).get("available", {}).get("cash", 0)
                },
                "holdings": [],
                "session_pnl": total_realized + total_unrealized,
                "total_realized": total_realized,
                "total_unrealized": total_unrealized
            }
            
            # Atomic Write
            tmp = CACHE_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(cache_data, f, default=str)
            os.replace(tmp, CACHE_FILE)
            
            # print(f"Updated {len(positions_list)}")
            with open(SCRIPT_DIR / "heartbeat.txt", "w") as f:
                f.write(datetime.now().isoformat())
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
