#!/usr/bin/env python3
"""
TRADING SYSTEM V3 - LIVE SYNC
Bridges Kite Connect with Dashboard by updating live_cache.json
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
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("LiveSync")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # execution/trading_system/scripts -> execution/trading_system -> execution -> root
# Note: In production this might need adjustment, ensure relative path is correct
# Current file: root/execution/trading_system/scripts/live_sync.py
# .parent -> scripts
# .parent.parent -> trading_system
# .parent.parent.parent -> execution
# .parent.parent.parent.parent -> root

# Let's be safer and use exact relative steps:
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent 
DATA_DIR = ROOT_DIR / "_tmp"
CACHE_FILE = DATA_DIR / "live_cache.json"

# Mock Data Generator (Fallback if no Kite connection)
class MockDataGenerator:
    def __init__(self):
        self.base_pnl = 0
        self.positions = [
            {"symbol": "RELIANCE", "qty": 10, "entry": 2450.0, "type": "LONG"},
            {"symbol": "TATASTEEL", "qty": 100, "entry": 145.50, "type": "LONG"},
            {"symbol": "INFY", "qty": -15, "entry": 1620.0, "type": "SHORT"}
        ]
        
    def generate(self):
        # Simulate price movements
        total_pnl = 0
        pos_data = []
        
        for p in self.positions:
            # Random volatility
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

        # Nifty movement
        nifty_ltp = 22150.0 + (random.random() * 100 - 50)

        data = {
            "timestamp": datetime.now().isoformat(),
            "is_live": True,  # Pretend it's live
            "source": "MOCK_SIMULATION",
            "account": {
                "user_name": "Demo User",
                "user_id": "DEMO01",
                "broker": "Zerodha (Simulated)",
                "status": "connected"
            },
            "margins": {
                "net": 150000.0,
                "available": 125000.0,
                "used": 25000.0
            },
            "positions": pos_data,
            "session_pnl": round(total_pnl, 2),
            "total_realized": 1250.0,
            "total_unrealized": round(total_pnl, 2),
            "nifty_ltp": round(nifty_ltp, 2),
            "holdings": [
                {"symbol": "HDFCBANK", "quantity": 50, "average_price": 1450.0, "current_price": 1460.0, "pnl": 500.0}
            ]
        }
        return data

# Main Sync Logic
def main():
    logger.info("Starting Live Sync Service...")
    DATA_DIR.mkdir(exist_ok=True)
    
    # Try to connect to Kite (Placeholder for now)
    try:
        # TODO: Implement actual Kite Connect here
        # import kiteconnect
        # kite = kiteconnect.KiteConnect(api_key="...")
        raise ImportError("Kite Connect not configured")
    except Exception as e:
        logger.warning(f"Could not connect to Kite: {e}")
        logger.info("Switching to MOCK DATA MODE")
        generator = MockDataGenerator()
        
        while True:
            try:
                data = generator.generate()
                
                # Write to Atomic File
                temp_file = CACHE_FILE.with_suffix(".tmp")
                with open(temp_file, "w") as f:
                    json.dump(data, f, indent=2)
                temp_file.replace(CACHE_FILE)
                
                logger.info(f"Updated cache: PnL {data['session_pnl']} | Time: {datetime.now().strftime('%H:%M:%S')}")
                
                time.sleep(2) # Update every 2 seconds
                
            except KeyboardInterrupt:
                logger.info("Stopping Sync...")
                break
            except Exception as e:
                logger.error(f"Sync error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    main()
