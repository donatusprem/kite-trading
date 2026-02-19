#!/usr/bin/env python3
"""
KiteTicker WebSocket Streaming Service
---------------------------------------
Connects to Kite's WebSocket feed for real-time tick data.
Writes tick prices to a shared JSON file that dashboard_api.py reads
and broadcasts to the frontend via its own WebSocket endpoint.

Usage:
    python3 execution/live_ticker.py
"""
import json
import os
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
from kiteconnect import KiteConnect, KiteTicker

# ─── Paths ──────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TOKEN_FILE = SCRIPT_DIR / "kite_token.json"
DATA_DIR = PROJECT_ROOT / ".tmp"
TICK_FILE = DATA_DIR / "live_ticks.json"
CACHE_FILE = DATA_DIR / "live_cache.json"
LOG_FILE = SCRIPT_DIR / "ticker.log"
INSTRUMENTS_FILE = DATA_DIR / "instruments.json"

DATA_DIR.mkdir(exist_ok=True)

# ─── Globals ────────────────────────────────────────────────────
tick_store = {}          # {instrument_token: {symbol, ltp, change, volume, ...}}
token_to_symbol = {}     # {instrument_token: tradingsymbol}
symbol_to_token = {}     # {tradingsymbol: instrument_token}
kite = None
last_cache_write = 0

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

# ─── Instrument Resolution ─────────────────────────────────────
def resolve_instruments(kite_client):
    """
    Download instrument list and build token <-> symbol mappings.
    Caches to file to avoid re-downloading on every restart.
    """
    global token_to_symbol, symbol_to_token

    # Check for cached instruments (valid for same day)
    if INSTRUMENTS_FILE.exists():
        try:
            with open(INSTRUMENTS_FILE) as f:
                cached = json.load(f)
            if cached.get("date") == datetime.now().strftime("%Y-%m-%d"):
                token_to_symbol = {int(k): v for k, v in cached.get("token_to_symbol", {}).items()}
                symbol_to_token = cached.get("symbol_to_token", {})
                log(f"Loaded {len(token_to_symbol)} cached instruments")
                return
        except:
            pass

    log("Downloading instrument list from Kite (this may take a moment)...")
    try:
        instruments = kite_client.instruments("NFO") + kite_client.instruments("NSE")
        for inst in instruments:
            tok = inst["instrument_token"]
            sym = inst["tradingsymbol"]
            token_to_symbol[tok] = sym
            symbol_to_token[sym] = tok

        # Cache for today
        cache = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "token_to_symbol": {str(k): v for k, v in token_to_symbol.items()},
            "symbol_to_token": symbol_to_token
        }
        with open(INSTRUMENTS_FILE, "w") as f:
            json.dump(cache, f)
        log(f"Cached {len(token_to_symbol)} instruments")
    except Exception as e:
        log(f"WARNING: Failed to download instruments: {e}")

# ─── Get Tokens for Active Positions ───────────────────────────
def get_subscription_tokens():
    """
    Read live_cache.json to find active position symbols,
    then resolve them to instrument tokens for subscription.
    """
    tokens = set()

    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE) as f:
                cache = json.load(f)

            # Active positions
            for pos in cache.get("positions", []):
                sym = pos.get("symbol", "")
                if sym in symbol_to_token:
                    tokens.add(symbol_to_token[sym])

            # Holdings
            for h in cache.get("holdings", []):
                sym = h.get("tradingsymbol", "")
                if sym in symbol_to_token:
                    tokens.add(symbol_to_token[sym])
    except Exception as e:
        log(f"Error reading cache for tokens: {e}")

    # Always add NIFTY 50 index for sentiment
    nifty_token = symbol_to_token.get("NIFTY 50")
    if nifty_token:
        tokens.add(nifty_token)

    return list(tokens)

# ─── Write Tick Data ────────────────────────────────────────────
def write_ticks_to_file():
    """Atomically write tick_store to live_ticks.json"""
    global last_cache_write
    now = time.time()
    if now - last_cache_write < 0.5:  # Throttle to max 2 writes/sec
        return

    try:
        output = {
            "timestamp": datetime.now().isoformat(),
            "ticks": {}
        }
        for tok, data in tick_store.items():
            sym = token_to_symbol.get(tok, str(tok))
            output["ticks"][sym] = data

        tmp = TICK_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(output, f, default=str)
        os.replace(tmp, TICK_FILE)
        last_cache_write = now
    except Exception as e:
        log(f"Write error: {e}")

# ─── Also Update live_cache.json Prices ─────────────────────────
def update_cache_prices():
    """
    Merge tick prices back into live_cache.json so the existing
    REST API endpoints serve fresh prices too.
    """
    try:
        if not CACHE_FILE.exists():
            return

        with open(CACHE_FILE) as f:
            cache = json.load(f)

        updated = False

        # Update position prices
        for pos in cache.get("positions", []):
            sym = pos.get("symbol", "")
            tok = symbol_to_token.get(sym)
            if tok and tok in tick_store:
                tick = tick_store[tok]
                new_price = tick.get("ltp", pos.get("current_price", 0))
                if new_price != pos.get("current_price"):
                    pos["current_price"] = new_price
                    entry = pos.get("entry_price", 0)
                    qty = pos.get("quantity", 0)
                    pos["pnl"] = round((new_price - entry) * qty, 2)
                    updated = True

        # Update holdings prices
        for h in cache.get("holdings", []):
            sym = h.get("tradingsymbol", "")
            tok = symbol_to_token.get(sym)
            if tok and tok in tick_store:
                tick = tick_store[tok]
                new_price = tick.get("ltp", h.get("last_price", 0))
                if new_price != h.get("last_price"):
                    h["last_price"] = new_price
                    h["value"] = new_price * h.get("quantity", 0)
                    updated = True

        if updated:
            cache["timestamp"] = datetime.now().isoformat()
            cache["source"] = "TICKER_LIVE"
            tmp = CACHE_FILE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(cache, f, default=str)
            os.replace(tmp, CACHE_FILE)
    except Exception as e:
        log(f"Cache update error: {e}")

# ─── KiteTicker Callbacks ──────────────────────────────────────
def on_ticks(ws, ticks):
    """Called on every tick batch from KiteTicker."""
    for tick in ticks:
        tok = tick.get("instrument_token")
        if tok is None:
            continue

        ohlc = tick.get("ohlc", {})
        tick_store[tok] = {
            "ltp": tick.get("last_price", 0),
            "volume": tick.get("volume_traded", 0),
            "change": tick.get("change", 0),
            "open": ohlc.get("open", 0),
            "high": ohlc.get("high", 0),
            "low": ohlc.get("low", 0),
            "close": ohlc.get("close", 0),
            "last_trade_time": str(tick.get("last_trade_time", "")),
            "oi": tick.get("oi", 0),
            "updated_at": datetime.now().isoformat()
        }

    # Write to shared file for dashboard_api
    write_ticks_to_file()

    # Also merge into live_cache.json
    update_cache_prices()

def on_connect(ws, response):
    log(f"WebSocket connected: {response}")
    tokens = get_subscription_tokens()
    if tokens:
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_QUOTE, tokens)
        log(f"Subscribed to {len(tokens)} instruments")
    else:
        log("WARNING: No instruments to subscribe to. Is live_cache.json populated?")

def on_close(ws, code, reason):
    log(f"WebSocket closed: {code} - {reason}")

def on_error(ws, code, reason):
    log(f"WebSocket error: {code} - {reason}")

def on_reconnect(ws, attempts_count):
    log(f"Reconnecting... attempt {attempts_count}")

def on_noreconnect(ws):
    log("MAX RECONNECT ATTEMPTS REACHED. Restarting in 30s...")
    time.sleep(30)
    main()  # Restart

# ─── Periodic Re-subscription ──────────────────────────────────
def resubscribe_loop(kws):
    """
    Every 60s, check if new positions have appeared and subscribe.
    This handles new trades opened during the session.
    """
    while True:
        time.sleep(60)
        try:
            tokens = get_subscription_tokens()
            currently_subscribed = set(tick_store.keys())
            new_tokens = [t for t in tokens if t not in currently_subscribed]
            if new_tokens:
                kws.subscribe(new_tokens)
                kws.set_mode(kws.MODE_QUOTE, new_tokens)
                log(f"Re-subscribed to {len(new_tokens)} new instruments")
        except Exception as e:
            log(f"Resubscribe error: {e}")

# ─── Main ───────────────────────────────────────────────────────
def main():
    global kite

    log("=" * 50)
    log("STARTING KITETICKER STREAMING SERVICE")
    log("=" * 50)

    # Load credentials
    try:
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        api_key = token_data["api_key"]
        access_token = token_data["access_token"]
        log(f"Loaded credentials for {token_data.get('user_name', 'Unknown')}")
    except Exception as e:
        log(f"FATAL: Cannot load token: {e}")
        return

    # Init KiteConnect for instrument resolution
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # Resolve instruments (symbol <-> token mapping)
    resolve_instruments(kite)

    # Init KiteTicker
    kws = KiteTicker(api_key, access_token)
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close
    kws.on_error = on_error
    kws.on_reconnect = on_reconnect
    kws.on_noreconnect = on_noreconnect

    # Start re-subscription thread
    resub_thread = threading.Thread(target=resubscribe_loop, args=(kws,), daemon=True)
    resub_thread.start()

    log("Connecting to KiteTicker WebSocket...")
    kws.connect(threaded=False)  # Blocking — keeps the process alive

if __name__ == "__main__":
    main()
