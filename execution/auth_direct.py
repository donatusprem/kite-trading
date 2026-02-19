#!/usr/bin/env python3
import os
import sys
import json
import logging
from kiteconnect import KiteConnect

# Configure detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
# Ideally load from .env, but for now we expect env vars or hardcoded fallback (not recommended for prod)
# We will use the env vars exported during run
API_KEY = os.environ.get("KITE_API_KEY")
API_SECRET = os.environ.get("KITE_API_SECRET")

if not API_KEY or not API_SECRET:
    logger.error("Please set KITE_API_KEY and KITE_API_SECRET environment variables.")
    sys.exit(1)

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Save token in execution root or config dir
TOKEN_FILE = os.path.join(SCRIPT_DIR, "kite_token.json")

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Request token from redirect URL")
    args = parser.parse_args()

    kite = KiteConnect(api_key=API_KEY)

    print("="*50)
    print("DIRECT KITE CONNECT AUTHENTICATION")
    print("="*50)

    # 1. Generate Login URL
    login_url = kite.login_url()
    
    if not args.token:
        print(f"\n1. Open this URL in your browser:\n\n{login_url}\n")
        print("2. Login and copy the 'request_token' from the redirect URL.")
        print("3. Run this script again with: python3 auth_direct.py --token <REQUEST_TOKEN>")
        return

    # 2. Process Token
    raw_input = args.token.strip()
    if "request_token=" in raw_input:
        import urllib.parse
        parsed = urllib.parse.urlparse(raw_input)
        qs = urllib.parse.parse_qs(parsed.query)
        request_token = qs.get("request_token", [""])[0]
    else:
        request_token = raw_input

    if not request_token:
        print("Error: Empty token.")
        sys.exit(1)

    # 3. Generate Session
    try:
        print("\n3. Generating Session...")
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]
        
        # 4. Save Token
        token_data = {
            "api_key": API_KEY,
            "access_token": access_token,
            "public_token": data.get("public_token"),
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name"),
            "login_time": data.get("login_time")
        }
        
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=4, default=str)
            
        print(f"\n✅ SUCCESS! Token saved to: {TOKEN_FILE}")
        print(f"User: {token_data.get('user_name')} ({token_data.get('user_id')})")
        
    except Exception as e:
        print(f"\n❌ Authentication Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
