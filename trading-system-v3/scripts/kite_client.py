#!/usr/bin/env python3
"""
Kite Connect Client - Direct API access via kiteconnect SDK
Handles authentication, token management, and all Kite API calls.

Usage:
    from scripts.kite_client import KiteClient
    client = KiteClient()
    client.login()  # Opens browser for Zerodha OAuth
    print(client.get_positions())
"""

import os
import json
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

TOKEN_FILE = PROJECT_ROOT / ".kite_token"


class KiteClient:
    """Direct Kite Connect API client using kiteconnect SDK."""

    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")
        self.api_secret = os.getenv("KITE_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "KITE_API_KEY and KITE_API_SECRET must be set in .env file.\n"
                "Copy .env.example to .env and fill in your credentials."
            )

        self.kite = KiteConnect(api_key=self.api_key)
        self.authenticated = False
        self._try_load_token()

    def _try_load_token(self):
        """Try to load a saved access token from today's session."""
        if not TOKEN_FILE.exists():
            return

        try:
            data = json.loads(TOKEN_FILE.read_text())
            saved_date = data.get("date")
            token = data.get("access_token")

            if saved_date == datetime.now().strftime("%Y-%m-%d") and token:
                self.kite.set_access_token(token)
                self.authenticated = True
                print(f"  Loaded saved token for today ({saved_date})")
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_token(self, access_token: str):
        """Save access token for today's session."""
        TOKEN_FILE.write_text(json.dumps({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "access_token": access_token
        }))

    def get_login_url(self) -> str:
        """Get the Zerodha login URL for OAuth."""
        return self.kite.login_url()

    def login(self, request_token: str = None):
        """
        Authenticate with Kite Connect.

        If request_token is provided, use it directly.
        Otherwise, open browser for OAuth and prompt for the token.
        """
        if self.authenticated:
            print("  Already authenticated for today's session.")
            return True

        if not request_token:
            login_url = self.get_login_url()
            print(f"\n  Opening browser for Zerodha login...")
            print(f"  URL: {login_url}\n")
            webbrowser.open(login_url)
            print("  After logging in, you'll be redirected to a URL like:")
            print("  https://your-redirect-url?request_token=XXXXXX&action=login\n")
            request_token = input("  Paste the request_token from the redirect URL: ").strip()

        if not request_token:
            print("  No request_token provided. Authentication failed.")
            return False

        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.kite.set_access_token(data["access_token"])
            self._save_token(data["access_token"])
            self.authenticated = True
            print(f"  Logged in as: {data.get('user_name', 'Unknown')}")
            return True
        except Exception as e:
            print(f"  Login failed: {e}")
            return False

    def _check_auth(self):
        """Ensure we're authenticated before making API calls."""
        if not self.authenticated:
            raise RuntimeError("Not authenticated. Call client.login() first.")

    # ──────────────────────────────────────────────
    # Account
    # ──────────────────────────────────────────────

    def get_profile(self) -> dict:
        """Get user profile."""
        self._check_auth()
        return self.kite.profile()

    def get_margins(self, segment: str = "equity") -> dict:
        """Get account margins. segment: 'equity' or 'commodity'."""
        self._check_auth()
        return self.kite.margins(segment)

    # ──────────────────────────────────────────────
    # Positions & Holdings
    # ──────────────────────────────────────────────

    def get_positions(self) -> dict:
        """Get all positions (day + net)."""
        self._check_auth()
        return self.kite.positions()

    def get_holdings(self) -> list:
        """Get holdings (delivery stocks)."""
        self._check_auth()
        return self.kite.holdings()

    # ──────────────────────────────────────────────
    # Market Data
    # ──────────────────────────────────────────────

    def get_ltp(self, instruments: List[str]) -> dict:
        """
        Get last traded price for instruments.
        instruments: List like ["NSE:RELIANCE", "NSE:NIFTY 50", "NFO:NIFTY26FEB25500CE"]
        """
        self._check_auth()
        return self.kite.ltp(instruments)

    def get_quote(self, instruments: List[str]) -> dict:
        """Get full quote (OHLC, volume, bid/ask) for instruments."""
        self._check_auth()
        return self.kite.quote(instruments)

    def get_ohlc(self, instruments: List[str]) -> dict:
        """Get OHLC data for instruments."""
        self._check_auth()
        return self.kite.ohlc(instruments)

    def get_historical_data(self, instrument_token: int, from_date: str,
                            to_date: str, interval: str) -> pd.DataFrame:
        """
        Get historical candle data.

        instrument_token: Numeric instrument token (use search_instruments to find)
        from_date: "2026-01-01" or datetime
        to_date: "2026-02-10" or datetime
        interval: "minute", "3minute", "5minute", "15minute", "30minute",
                  "60minute", "day", "week", "month"
        """
        self._check_auth()
        data = self.kite.historical_data(instrument_token, from_date, to_date, interval)
        if data:
            df = pd.DataFrame(data)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
            return df
        return pd.DataFrame()

    # ──────────────────────────────────────────────
    # Instruments
    # ──────────────────────────────────────────────

    def search_instruments(self, exchange: str = "NSE", query: str = "") -> pd.DataFrame:
        """
        Search for instruments.
        exchange: "NSE", "BSE", "NFO", "BFO", "MCX"
        query: Filter by name (case-insensitive substring match)
        """
        self._check_auth()
        instruments = self.kite.instruments(exchange)
        df = pd.DataFrame(instruments)
        if query:
            mask = (
                df["tradingsymbol"].str.contains(query, case=False, na=False) |
                df["name"].str.contains(query, case=False, na=False)
            )
            df = df[mask]
        return df

    # ──────────────────────────────────────────────
    # Orders (use with caution)
    # ──────────────────────────────────────────────

    def place_order(self, exchange: str, tradingsymbol: str, transaction_type: str,
                    quantity: int, product: str = "MIS", order_type: str = "MARKET",
                    price: float = None, trigger_price: float = None) -> str:
        """
        Place an order. Returns order_id.

        transaction_type: "BUY" or "SELL"
        product: "MIS" (intraday), "CNC" (delivery), "NRML" (F&O normal)
        order_type: "MARKET", "LIMIT", "SL", "SL-M"
        """
        self._check_auth()
        params = {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "product": product,
            "order_type": order_type,
            "variety": self.kite.VARIETY_REGULAR,
        }
        if price is not None:
            params["price"] = price
        if trigger_price is not None:
            params["trigger_price"] = trigger_price

        return self.kite.place_order(**params)

    def get_orders(self) -> list:
        """Get all orders for today."""
        self._check_auth()
        return self.kite.orders()

    def cancel_order(self, order_id: str) -> str:
        """Cancel an order."""
        self._check_auth()
        return self.kite.cancel_order(
            variety=self.kite.VARIETY_REGULAR,
            order_id=order_id
        )
