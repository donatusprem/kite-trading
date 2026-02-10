#!/usr/bin/env python3
"""
Kite Authentication Helper
Run this once each morning to authenticate with Zerodha.
Token is saved for the day — other scripts will reuse it.

Usage:
  python3 authenticate_kite.py
  python3 authenticate_kite.py --token YOUR_REQUEST_TOKEN
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "trading-system-v3"))

from scripts.kite_client import KiteClient


def main():
    print("=" * 50)
    print("  Kite Connect - Daily Authentication")
    print("=" * 50)

    client = KiteClient()

    if client.authenticated:
        print("\n  Already authenticated for today!")
        profile = client.get_profile()
        print(f"  User: {profile.get('user_name')} ({profile.get('user_id')})")
        print(f"  Broker: {profile.get('broker')}")
        return

    # Check if request_token passed as argument
    request_token = None
    if "--token" in sys.argv:
        idx = sys.argv.index("--token")
        if idx + 1 < len(sys.argv):
            request_token = sys.argv[idx + 1]

    success = client.login(request_token=request_token)

    if success:
        print("\n  Authentication successful!")
        profile = client.get_profile()
        print(f"  User: {profile.get('user_name')} ({profile.get('user_id')})")
        print(f"  Broker: {profile.get('broker')}")
        print("\n  Token saved. All scripts will use this session today.")
    else:
        print("\n  Authentication failed. Please try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
