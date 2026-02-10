"""
AI Trading Dashboard API - Live Kite Integration
FastAPI backend that connects to Kite MCP for real-time data
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(title="AI Trading Dashboard API - Live")

# Allow CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent
ALERTS_DIR = BASE_DIR / "alerts"
DATA_DIR = BASE_DIR / "data"
JOURNALS_DIR = BASE_DIR / "journals"

# Ensure directories exist
ALERTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
JOURNALS_DIR.mkdir(exist_ok=True)

CACHE_FILE = DATA_DIR / "live_cache.json"


def read_cache() -> dict:
    """Read the live cache file."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading cache: {e}")
    return {}


@app.get("/")
async def root():
    return {
        "message": "AI Trading Dashboard API - LIVE",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status")
async def get_status():
    """Check system health and connection status."""
    is_live = CACHE_FILE.exists()
    cache_age = None
    if is_live:
        cache_age = datetime.now().timestamp() - CACHE_FILE.stat().st_mtime

    return {
        "status": "online",
        "version": "3.1-live",
        "is_live": is_live,
        "cache_age_seconds": cache_age,
        "directories": {
            "alerts": ALERTS_DIR.exists(),
            "data": DATA_DIR.exists(),
            "journals": JOURNALS_DIR.exists()
        }
    }


@app.get("/scan/latest")
async def get_latest_scan():
    """Get the most recent scan result/alert."""
    try:
        if not ALERTS_DIR.exists():
            return {"error": "Alerts directory not found", "data": []}

        files = list(ALERTS_DIR.glob("*.json"))
        if not files:
            return {"message": "No scans found", "data": []}

        latest_file = max(files, key=os.path.getctime)

        with open(latest_file, "r") as f:
            data = json.load(f)

        return {"timestamp": latest_file.stat().st_mtime, "data": data}

    except Exception as e:
        return {"error": str(e)}


@app.get("/positions")
async def get_positions():
    """Get active positions from live cache."""
    try:
        data = read_cache()
        if not data:
            return {"positions": [], "pnl": 0.0, "is_live": False}

        positions = data.get("positions", [])
        total_pnl = data.get("session_pnl", sum(p.get("pnl", 0) for p in positions))

        return {
            "positions": positions,
            "pnl": total_pnl,
            "is_live": True,
            "last_update": data.get("timestamp")
        }

    except Exception as e:
        return {"error": str(e), "positions": [], "pnl": 0.0}


@app.get("/stats/market-pulse")
async def get_market_pulse():
    """Get market pulse from live data."""
    try:
        data = read_cache()

        if data:
            nifty_price = data.get("nifty_ltp", 0)
            session_pnl = data.get("session_pnl", 0)
            total_realized = data.get("total_realized", 0)
            total_unrealized = data.get("total_unrealized", 0)

            # Sentiment based on session performance
            if session_pnl > 5000:
                sentiment = 85
                trend = "strongly bullish"
            elif session_pnl > 1000:
                sentiment = 70
                trend = "bullish"
            elif session_pnl > 0:
                sentiment = 60
                trend = "mildly bullish"
            elif session_pnl > -1000:
                sentiment = 45
                trend = "neutral"
            else:
                sentiment = 30
                trend = "bearish"

            return {
                "sentiment_score": sentiment,
                "trend": trend,
                "volatility": "moderate",
                "nifty_ltp": nifty_price,
                "session_pnl": session_pnl,
                "total_realized": total_realized,
                "total_unrealized": total_unrealized,
                "is_live": True
            }

        return {
            "sentiment_score": 50,
            "trend": "neutral",
            "volatility": "unknown",
            "is_live": False
        }

    except Exception as e:
        return {"error": str(e), "sentiment_score": 50, "trend": "error"}


@app.get("/account/profile")
async def get_profile():
    """Get user profile from live cache."""
    data = read_cache()
    account = data.get("account", {})
    return {
        "user_name": account.get("user_name", "Trader"),
        "user_shortname": account.get("user_shortname", ""),
        "user_id": account.get("user_id", ""),
        "broker": account.get("broker", ""),
        "is_live": bool(account)
    }


@app.get("/account/margins")
async def get_margins():
    """Get account margins from live cache."""
    data = read_cache()
    margins = data.get("margins", {})
    return {
        "net": margins.get("net", 0),
        "cash": margins.get("cash", 0),
        "collateral": margins.get("collateral", 0),
        "option_premium_used": margins.get("option_premium_used", 0),
        "is_live": bool(margins)
    }


@app.get("/account/holdings")
async def get_holdings():
    """Get holdings from live cache."""
    data = read_cache()
    return {
        "holdings": data.get("holdings", []),
        "is_live": True
    }


@app.get("/account/summary")
async def get_account_summary():
    """Get full account summary - all data in one call."""
    data = read_cache()

    margins = data.get("margins", {})
    positions = data.get("positions", [])
    holdings = data.get("holdings", [])
    account = data.get("account", {})

    active_positions = [p for p in positions if p.get("quantity", 0) != 0]
    closed_positions = [p for p in positions if p.get("quantity", 0) == 0]

    return {
        "account": account,
        "margins": margins,
        "positions": active_positions,
        "closed_positions": closed_positions,
        "holdings": holdings,
        "session_pnl": data.get("session_pnl", 0),
        "total_realized": data.get("total_realized", 0),
        "total_unrealized": data.get("total_unrealized", 0),
        "nifty_ltp": data.get("nifty_ltp", 0),
        "timestamp": data.get("timestamp"),
        "is_live": data.get("is_live", False)
    }


@app.post("/scan/trigger")
async def trigger_scan():
    """Trigger a market scan using real OHLCV data."""
    try:
        # Add scripts directory to path so we can import the scanner
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from market_scanner import run_scan
        results = run_scan()

        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "count": len(results),
            "data": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    print("Starting AI Trading Dashboard API (LIVE)")
    print("Serving on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
