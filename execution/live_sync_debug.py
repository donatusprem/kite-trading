#!/usr/bin/env python3
import json
import os
import sys
import traceback
from pathlib import Path
from kiteconnect import KiteConnect

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
LOG_FILE = SCRIPT_DIR / "debug_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{msg}\n")
    print(msg)

def main():
    try:
        # Clear log
        with open(LOG_FILE, "w") as f:
            f.write("STARTING DEBUG SYNC\n")
            
        log(f"Loading token from {TOKEN_FILE}")
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            
        api_key = token_data.get("api_key")
        access_token = token_data.get("access_token")
        
        log(f"API Key: {api_key}, Access Token: {access_token[:5]}...")
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        log("Fetching positions...")
        positions = kite.positions()
        log(f"Positions Raw Type: {type(positions)}")
        log(f"Positions Raw: {positions}")
        
        log("Fetching margins...")
        margins = kite.margins()
        log(f"Margins Raw: {margins}")
        
        log("SUCCESS")
        
    except Exception as e:
        log("ERROR")
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
