#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR
DATA_DIR = ROOT_DIR / "_tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"

# Config
MCP_PORT = os.environ.get("APP_PORT", "8080")
MCP_URL = f"http://localhost:{MCP_PORT}/mcp"
# Hardcoded from previous KeepAlive run
SESSION_ID = "kitemcp-1d751f13-7b7d-436d-9a56-c28f29f8d4e5" 

print(f"DEBUG: STARTING SIMPLE SYNC. PORT={MCP_PORT}, DIR={ROOT_DIR}, SESSION={SESSION_ID}", flush=True)

def call_mcp(method, params, session_id=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
    
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
        
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"MCP Call Error: {e}", flush=True)
        return None

def get_positions(session_id):
    res = call_mcp("tools/call", {"name": "get_positions", "arguments": {}}, session_id)
    if res and "result" in res:
        content = res["result"].get("content", [{}])[0].get("text", "[]")
        try:
            data = json.loads(content)
            # Handle list or dict
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("net", []) # Prefer net positions
        except:
            pass
    return []

def get_margins(session_id):
    res = call_mcp("tools/call", {"name": "get_margins", "arguments": {}}, session_id)
    if res and "result" in res:
        content = res["result"].get("content", [{}])[0].get("text", "{}")
        try:
            data = json.loads(content)
            # Format: {equity: {net: ..., available: {cash: ...}}}
            equity = data.get("equity", {})
            return {
                "net": equity.get("net", 0),
                "available": equity.get("available", {}).get("cash", 0),
                "used": equity.get("utilised", {}).get("debits", 0) # simplification
            }
        except:
            pass
    return {"net": 0, "available": 0, "used": 0}

def get_profile(session_id):
    res = call_mcp("tools/call", {"name": "get_profile", "arguments": {}}, session_id)
    if res and "result" in res:
        content = res["result"].get("content", [{}])[0].get("text", "{}")
        try:
            return json.loads(content)
        except:
            pass
    return {}

def main():
    DATA_DIR.mkdir(exist_ok=True)
    
    print(f"Using Session ID: {SESSION_ID}", flush=True)
    
    while True:
        try:
            positions_raw = get_positions(SESSION_ID)
            profile = get_profile(SESSION_ID)
            margins = get_margins(SESSION_ID)
            
            # --- Process Positions ---
            positions_data = []
            session_pnl = 0
            total_realized = 0
            total_unrealized = 0
            
            print(f"Raw Positions Count: {len(positions_raw)}", flush=True)

            for pos in positions_raw:
                qty = pos.get("quantity", 0)
                if qty == 0: qty = pos.get("net_quantity", 0)
                
                # Check realized PnL even if closed
                pnl_real = pos.get("pnl", 0) if qty == 0 else 0
                total_realized += pnl_real
                
                if qty != 0:
                    entry = pos.get("average_price", 0)
                    ltp = pos.get("last_price", 0)
                    pnl = pos.get("pnl", 0) # usually unrealized for open pos
                    
                    # Calculate PnL %
                    pnl_pct = 0
                    if entry > 0:
                        pnl_pct = ((ltp - entry) / entry) * 100
                        if qty < 0: pnl_pct = -pnl_pct # Short logic
                    
                    total_unrealized += pnl
                    
                    positions_data.append({
                        "symbol": pos.get("tradingsymbol", "?"),
                        "quantity": qty,
                        "entry_price": entry,
                        "current_price": ltp,
                        "pnl": pnl,
                        "pnl_percent": pnl_pct,
                        "type": "LONG" if qty > 0 else "SHORT",
                        "product": pos.get("product", "MIS"),
                        "exchange": pos.get("exchange", "NSE"),
                        "instrument_type": pos.get("instrument_type", "EQ")
                    })

            session_pnl = total_realized + total_unrealized

            # --- Assemble Cache ---
            data = {
                "timestamp": datetime.now().isoformat(),
                "is_live": True,
                "source": "KITE_MCP_SERVER",
                "account": {
                    "user_name": profile.get("user_name", "Trader"),
                    "user_id": profile.get("user_id", "Unknown"),
                    "broker": "Zerodha",
                    "status": "connected"
                },
                "margins": margins,
                "positions": positions_data,
                "session_pnl": round(session_pnl, 2),
                "total_realized": round(total_realized, 2),
                "total_unrealized": round(total_unrealized, 2),
                "nifty_ltp": 0, # TODO: fetch if needed
                "holdings": []  # TODO: fetch
            }
            
            # Atomic Write
            temp_file = CACHE_FILE.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(CACHE_FILE)
            
            print(f"Updated cache | PnL: {session_pnl} | Positions: {len(positions_data)}", flush=True)
            time.sleep(2)
            
        except Exception as e:
            print(f"Sync Loop Error: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
