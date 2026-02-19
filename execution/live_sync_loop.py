#!/usr/bin/env python3
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
DATA_DIR = PROJECT_ROOT / ".tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"
LOG_FILE = SCRIPT_DIR / "sync_loop.log"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} {msg}\n")
        f.flush()
        os.fsync(f.fileno())
    print(msg) # also stdout

def main():
    # Force immediate log
    with open(LOG_FILE, "a") as f:
        f.write(f"DEBUG START: {datetime.now()}\n")
    print(f"DEBUG START: {datetime.now()}")

    log("STARTING SYNC LOOP")
    
    try:
        log(f"Loading token from {TOKEN_FILE}")
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            
        api_key = token_data.get("api_key")
        access_token = token_data.get("access_token")
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        log("Kite Initialized")
        
    except Exception as e:
        log(f"FATAL INIT ERROR: {e}")
        return

    while True:
        try:
            # log("Fetching positions...") # too verbose? Only log errors or periodic
            positions = kite.positions()
            margins = kite.margins()
            # Fetch Holdings
            try:
                holdings = kite.holdings()
            except Exception as e:
                log(f"Error fetching holdings: {e}")
                holdings = []

            # Process Holdings (Equity vs MF)
            total_equity_value = 0
            total_mf_value = 0
            equity_holdings = []
            mf_holdings = []
            
            for h in holdings:
                # holdings response: 'last_price', 'quantity', 'pnl', 'average_price'
                # Determine type. Usually valid ISINs starting with INF... are equity/mf.
                # Simplistic check: If exchange is NSE/BSE -> Equity? 
                # Mutual funds in Zerodha Coin usually have 'product'='CNC' and exchange='BSE' or 'NSE'?
                # Better: Check if tradingsymbol ends with 'Growth' or look at ISIN?
                # Actually, standard kite holdings mix them.
                # We'll just separate everything that is NOT a derivative.
                
                # Check for "Mutual Fund" in name?
                # Or relying on 'exchange' might be enough? MFs are on BSE/NSE but often different series.
                # Let's just group them.
                
                # Logic: If item is in holdings, it's an asset.
                val = h.get("last_price", 0) * h.get("quantity", 0)
                
                # Create clean dict
                clean_h = {
                    "tradingsymbol": h.get("tradingsymbol"),
                    "quantity": h.get("quantity"),
                    "average_price": h.get("average_price"),
                    "last_price": h.get("last_price"),
                    "pnl": h.get("pnl"),
                    "value": val,
                    "exchange": h.get("exchange")
                }
                
                total_equity_value += val # Aggregate all for now
                equity_holdings.append(clean_h)

            # Process Positions (from previous block)
            positions_list = []
            net = positions.get("net", [])
            total_unrealized_positions = 0
            total_realized_positions = 0
            
            for p in net:
                qty = p.get("quantity", 0)
                unrealized = p.get("unrealised", 0) or p.get("m2m", 0)
                if qty != 0:
                    positions_list.append({
                        "symbol": p.get("tradingsymbol"),
                        "quantity": qty,
                        "entry_price": p.get("average_price", 0),
                        "current_price": p.get("last_price", 0),
                        "pnl": unrealized, # Dashboard expects 'pnl' field
                        "pnl_percent": 0,
                        "product": p.get("product"),
                        "exchange": p.get("exchange"),
                        "type": "LONG" if qty > 0 else "SHORT"
                    })
                    total_unrealized_positions += unrealized
                else:
                    total_realized_positions += p.get("realised", 0)

            # Load User Config for Funds Added
            funds_added = 0
            try:
                user_conf_path = SCRIPT_DIR / "user_config.json"
                if user_conf_path.exists():
                    with open(user_conf_path, "r") as f:
                        uconf = json.load(f)
                        funds_added = uconf.get("total_funds_added", 0)
            except Exception as e:
                log(f"Config Error: {e}")

            # Calculate Totals
            cash_margin = margins.get("equity", {}).get("net", 0)
            # Kite 'net' margin includes option premiums? 
            # Ideally:
            # Total Asset Value = Cash + Holdings Value + Option Premium Value (if long) - Option Liabilities (if short)
            # But 'net' margin usually accounts for realized PnL and cash.
            # Unrealized M2M of positions affects 'available' margin but usually not 'net' cash unless settled?
            # Simpler approach:
            # Current Account Value = Net Cash (from margins) + Holdings Value
            # (Ignoring Intraday positions M2M for 'Account Value' or including them?)
            # Let's include Unrealized M2M from positions to get "Liquidation Value".
            
            current_value = cash_margin + total_equity_value + total_unrealized_positions
            
            lifetime_pnl = current_value - funds_added

            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "is_live": True,
                "source": "SYNC_LOOP",
                "account": {
                    "user_name": token_data.get("user_name"), 
                    "status": "connected",
                    "funds_added": funds_added,
                    "current_value": current_value,
                    "lifetime_pnl": lifetime_pnl,
                    "lifetime_pnl_pct": (lifetime_pnl / funds_added * 100) if funds_added > 0 else 0
                },
                "positions": positions_list,
                "margins": {
                    "net": cash_margin,
                    "available": margins.get("equity", {}).get("available", {}).get("cash", 0)
                },
                "holdings": equity_holdings,
                "session_pnl": total_realized_positions + total_unrealized_positions,
                "total_realized": total_realized_positions,
                "total_unrealized": total_unrealized_positions
            }
            
            # Atomic Write
            tmp = CACHE_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(cache_data, f, default=str)
            os.replace(tmp, CACHE_FILE)
            
            # log(f"Updated cache. Pos: {len(positions_list)}")
            time.sleep(30)  # Account-level data only; ticks handled by live_ticker.py
            
        except Exception as e:
            log(f"LOOP ERROR: {e}")
            log(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    main()
