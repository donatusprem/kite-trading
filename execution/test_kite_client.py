import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from kite_client import KiteMCPClient

def test():
    print("Initializing Client...")
    c = KiteMCPClient()
    if not c.login():
        print("FAIL: Login")
        return

    print("Fetching Profile...")
    p = c.get_profile()
    if p:
        print(f"PASS: Profile {p.get('user_name')}")
    else:
        print("FAIL: Profile")

    print("Searching Instruments (This triggers download)...")
    # First run might be slow
    res = c.search_instruments("NFO:NIFTY", filter_on="underlying", limit=5)
    print(f"Found {len(res)} instruments")
    for r in res:
        print(f" - {r.get('tradingsymbol')} {r.get('expiry')}")

    if not res:
        print("FAIL: Search returned empty (maybe NFO download failed?)")
        return

    print("Fetching Positions...")
    pos = c.get_positions()
    if pos:
        print(f"PASS: Positions ({len(pos.get('net', []))} net)")
    else:
        print("FAIL: Positions")

    print("Fetching LTP for owned symbol...")
    # Try fetching one from positions if available
    inst = "NSE:INFY" # Fallback
    if pos and pos.get("net"):
        p = pos["net"][0]
        inst = f"{p['exchange']}:{p['tradingsymbol']}"
    
    print("Fetching Orders...")
    orders = c.get_orders()
    if orders is not None:
        print(f"PASS: Orders ({len(orders)} orders)")
    else:
        print("FAIL: Orders")
        
test()
