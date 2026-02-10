#!/usr/bin/env python3
import time
import json
from datetime import datetime, timedelta
from kite_client import KiteMCPClient

def print_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")

def main():
    client = KiteMCPClient()
    
    print_section("Kite MCP Demo")

    # 1. Start Server
    if not client.check_server():
        if not client.start_server():
            print("❌ Failed to start server.")
            return
    else:
        print("✅ Server is already running.")

    # 2. Authenticate
    if not client.login():
        print("❌ Authentication failed.")
        return

    # 3. Get Profile & Margins
    print_section("User Info")
    
    try:
        profile = client.get_profile()
        print(f"Name: {profile.get('user_name')}")
        print(f"ID:   {profile.get('user_id')}")
        print(f"Role: {profile.get('user_type')}")
        
        margins = client.get_margins()
        if margins:
            equity = margins.get("equity", {})
            print(f"\nAvailable Cash (Equity): ₹{equity.get('net', 0):,.2f}")
            print(f"Utilized Margin:       ₹{equity.get('utilised', {}).get('debits', 0):,.2f}")
    except Exception as e:
        print(f"❌ Error fetching user info: {e}")

    # 4. Search Instrument
    print_section("Instrument Search")
    instrument_token = None
    try:
        query = "RELIANCE"
        print(f"Searching for '{query}'...")
        results = client.search_instruments(query=query, filter_on="tradingsymbol", limit=5)
        
        if results:
            # results is a list of instrument dicts inside the content
            # The client.search_instruments returns the parsed JSON list directly
            
            # Find NSE equity
            for instr in results:
                print(f" - {instr.get('exchange')}:{instr.get('tradingsymbol')} (Token: {instr.get('instrument_token')})")
                if instr.get('exchange') == 'NSE' and instr.get('tradingsymbol') == 'RELIANCE':
                    instrument_token = instr.get('instrument_token')
            
            if not instrument_token and results:
                instrument_token = results[0].get('instrument_token')
                
    except Exception as e:
        print(f"❌ Error searching: {e}")

    # 5. Live Quote
    print_section("Live Quote")
    try:
        instruments = ["NSE:RELIANCE", "NSE:NIFTY 50"]
        quotes = client.get_quotes(instruments)
        
        if quotes:
            for symbol, data in quotes.items():
                print(f"{symbol}:")
                print(f"  LTP: ₹{data.get('last_price')}")
                print(f"  OHLC: {data.get('ohlc')}")
                print(f"  Depth (Buy/Sell 1): {data.get('depth', {}).get('buy', [{}])[0].get('price')} / {data.get('depth', {}).get('sell', [{}])[0].get('price')}")
                print("-" * 30)
    except Exception as e:
         print(f"❌ Error fetching quotes: {e}")


    # 6. Historical Data
    if instrument_token:
        print_section(f"Historical Data (Token: {instrument_token})")
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5)
            
            fmt = "%Y-%m-%d %H:%M:%S"
            print(f"Fetching candles from {from_date.strftime(fmt)} to {to_date.strftime(fmt)}")
            
            candles = client.get_historical_data(
                instrument_token=instrument_token,
                from_date=from_date.strftime(fmt),
                to_date=to_date.strftime(fmt),
                interval="day"
            )
            
            if candles:
                print(f"Received {len(candles)} candles:")
                print("Timestamp            |   Open |   High |    Low |  Close | Volume")
                print("-" * 75)
                for c in candles[:5]: # Print first 5
                     # Candle format: [timestamp, open, high, low, close, volume, oi]
                     ts = c[0]
                     print(f"{ts:<20} | {c[1]:6.2f} | {c[2]:6.2f} | {c[3]:6.2f} | {c[4]:6.2f} | {c[5]}")
            else:
                print("No candles returned.")

        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")

    print("\n✅ Demo Complete.")
    # Stop server? maybe keep it running for repeated tests
    # client.stop_server()

if __name__ == "__main__":
    main()
