import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
DATA_DIR = PROJECT_ROOT / ".tmp"
INSTRUMENTS_FILE = DATA_DIR / "instruments_nfo.csv"

class KiteMCPClient:
    """
    Direct Kite Connect Client wrapper that mimics the old MCP Client interface.
    Used by dashboard_api.py, options_analyzer.py, etc.
    """

    def __init__(self):
        self.kite = None
        self.instruments_df = None
        self._load_token()

    def _load_token(self):
        try:
            if not TOKEN_FILE.exists():
                print(f"❌ Token file missing: {TOKEN_FILE}")
                return

            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
            
            self.kite = KiteConnect(api_key=data.get("api_key"))
            self.kite.set_access_token(data.get("access_token"))
            print("✅ Kite Direct Client Initialized")
        except Exception as e:
            print(f"❌ Failed to init Kite Client: {e}")

    def check_server(self):
        # Always true for direct mode
        return True
        
    def login(self):
        # Always true if token exists
        return self.kite is not None

    def get_profile(self):
        try:
            return self.kite.profile()
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def get_margins(self):
        try:
            return self.kite.margins()
        except Exception as e:
            print(f"Error fetching margins: {e}")
            return None

    def get_positions(self):
        try:
            return self.kite.positions()
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return None

    def get_orders(self):
        try:
            return self.kite.orders()
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return None

    def get_ltp(self, instruments: list):
        """
        Get LTP for list of instruments (e.g., ["NSE:INFY", "NFO:NIFTY23..."]).
        Returns dict keyed by instrument.
        """
        try:
            return self.kite.ltp(instruments)
        except Exception as e:
            print(f"Error fetching LTP: {e}")
            return {}

    def get_quotes(self, instruments: list):
        try:
            return self.kite.quote(instruments)
        except Exception as e:
            print(f"Error fetching quotes: {e}")
            return {}

    def get_ohlc(self, instruments: list):
        try:
            return self.kite.ohlc(instruments)
        except Exception as e:
            print(f"Error fetching OHLC: {e}")
            return {}

    def get_historical_data(self, instrument_token, from_date, to_date, interval, continuous=False, oi=False):
        try:
            return self.kite.historical_data(instrument_token, from_date, to_date, interval, continuous, oi)
        except Exception as e:
            print(f"Error fetching historical: {e}")
            return []

    # ─── Search Instruments (Crucial for Option Chain) ───

    def _ensure_instruments_loaded(self):
        if self.instruments_df is not None:
            return

        DATA_DIR.mkdir(exist_ok=True)
        
        # Check cache age (1 day)
        fetch_fresh = True
        if INSTRUMENTS_FILE.exists():
            mtime = datetime.fromtimestamp(INSTRUMENTS_FILE.stat().st_mtime)
            if mtime.date() == datetime.now().date():
                fetch_fresh = False
                print("Using cached instruments dump.")

        if fetch_fresh:
            print("Fetching fresh instruments dump (NFO)...")
            try:
                # specific exchange NFO to reduce size? Or all?
                # options_analyzer needs NFO.
                inst_list = self.kite.instruments("NFO")
                df = pd.DataFrame(inst_list)
                # Convert dates to string for CSV/Compat
                if 'expiry' in df.columns:
                    df['expiry'] = df['expiry'].astype(str)
                df.to_csv(INSTRUMENTS_FILE, index=False)
                self.instruments_df = df
            except Exception as e:
                print(f"Failed to fetch instruments: {e}")
                # Try loading cache even if old
                if INSTRUMENTS_FILE.exists():
                     self.instruments_df = pd.read_csv(INSTRUMENTS_FILE)
        else:
            self.instruments_df = pd.read_csv(INSTRUMENTS_FILE)
            
        # Also need NSE for Index Spot prices?
        # Analyzer maps UNDERLYING to 'NSE:NIFTY 50'.
        # This function search_instruments is usually called with "NFO:..." query.
        
    def search_instruments(self, query: str, filter_on: str = "id", limit: int = 10):
        """
        Mimics MCP search_instruments.
        Query: "NFO:NIFTY"
        Filter: "underlying" (usually)
        """
        self._ensure_instruments_loaded()
        if self.instruments_df is None:
            return []

        df = self.instruments_df
        
        # Parse query "NFO:NIFTY"
        exchange = None
        search_txt = query
        if ":" in query:
            parts = query.split(":")
            if parts[0] in ["NFO", "NSE", "BSE", "MCX"]:
                exchange = parts[0]
                search_txt = parts[1]

        # Filter
        # If caching only NFO, then ignore NSE exchange filter?
        # The code above only fetches NFO.
        # If query asks for NSE, we might return nothing.
        # But OptionsAnalyzer asks for "NFO:NIFTY".
        
        mask = pd.Series([True] * len(df))
        
        if exchange:
            mask &= (df["exchange"] == exchange)
            
        if filter_on == "underlying":
            # Underlying name match: "NIFTY" -> matches "NIFTY", "NIFTY 50"??
            # Kite 'name' field usually holds underlying symbol e.g. "NIFTY"
            mask &= (df["name"] == search_txt)
        elif filter_on == "name":
            mask &= (df["name"].str.contains(search_txt, case=False, na=False))
        elif filter_on == "tradingsymbol":
            mask &= (df["tradingsymbol"].str.contains(search_txt, case=False, na=False))

        results_df = df[mask]
        
        # Convert to list of dicts
        # Ensure 'expiry' is string YYYY-MM-DD
        records = results_df.to_dict(orient="records")
        # Handle nan
        clean_records = []
        for r in records:
            # clean nan
            r = {k: (v if pd.notna(v) else None) for k, v in r.items()}
            # Convert expiry to string if it matches 'NaT' or similar
            if 'expiry' in r and (r['expiry'] == 'nan' or r['expiry'] == 'NaT'):
                r['expiry'] = ""
            clean_records.append(r)
            
        return clean_records[:limit]

    def place_order(self, tradingsymbol, transaction_type, quantity, product, order_type, 
                    exchange="NSE", price=0.0, trigger_price=0.0, variety="regular", 
                    validity="DAY", disclosed_quantity=0, tag=""):
        
        try:
            order_id = self.kite.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price,
                validity=validity,
                disclosed_quantity=disclosed_quantity,
                tag=tag
            )
            return {"status": "success", "order_id": order_id}
        except Exception as e:
            print(f"Order Placement Error: {e}")
            return {"status": "error", "message": str(e)}

    # Helper for mcp compatibility
    def call_tool(self, name, args):
        print(f"Mocking call_tool: {name}")
        return None
