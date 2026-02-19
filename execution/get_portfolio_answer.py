import json
import os
import sys
from pathlib import Path
from datetime import datetime
from kiteconnect import KiteConnect

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
User_CONFIG_FILE = SCRIPT_DIR / "user_config.json"
RESULT_FILE = SCRIPT_DIR / "portfolio_answer.txt"

def main():
    try:
        if not TOKEN_FILE.exists():
            with open(RESULT_FILE, "w") as f:
                f.write("ERROR: Token file missing")
            return

        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            
        api_key = token_data.get("api_key")
        access_token = token_data.get("access_token")
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Fetch Data
        holdings = kite.holdings()
        positions = kite.positions()
        margins = kite.margins()
        
        # Calculate
        holdings_val = sum(h['last_price'] * h['quantity'] for h in holdings)
        
        net_pos_unrealized = sum(p['unrealised'] for p in positions.get('net', []))
        net_pos_realized = sum(p['realised'] for p in positions.get('net', []))
        
        cash = margins.get('equity', {}).get('net', 0)
        
        current_value = cash + holdings_val + net_pos_unrealized
        
        # Config
        funds_added = 0
        if User_CONFIG_FILE.exists():
            with open(User_CONFIG_FILE, "r") as f:
                uconf = json.load(f)
                funds_added = uconf.get("total_funds_added", 0)
                
        gross_profit = current_value - funds_added
        
        # Write Answer
        with open(RESULT_FILE, "w") as f:
            f.write(f"Total Portfolio Value: {current_value}\n")
            f.write(f"Funds Added: {funds_added}\n")
            f.write(f"Gross Profit (Lifetime P&L): {gross_profit}\n")
            f.write(f"Ref: Cash={cash}, Holdings={holdings_val}, PosUnrealized={net_pos_unrealized}")
            
    except Exception as e:
        with open(RESULT_FILE, "w") as f:
            f.write(f"ERROR: {e}")

if __name__ == "__main__":
    main()
