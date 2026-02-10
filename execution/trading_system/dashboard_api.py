"""
AI Trading Dashboard API
- yfinance for historical OHLCV & chart data (free, no auth)
- Kite API for live intraday LTP & account data (via live_cache.json)
- Signal engine for institutional-grade indicator analysis
- Risk manager for portfolio-level risk metrics
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
from pathlib import Path
from datetime import datetime

app = FastAPI(title="AI Trading Dashboard API v2")

# Add scripts to path
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = str(BASE_DIR / "scripts")
EXECUTION_DIR = str(BASE_DIR.parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
if EXECUTION_DIR not in sys.path:
    sys.path.insert(0, EXECUTION_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = BASE_DIR.parent.parent
ALERTS_DIR = BASE_DIR / "alerts"
CACHE_DIR = ROOT_DIR / ".tmp"
JOURNALS_DIR = BASE_DIR / "journals"

ALERTS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
JOURNALS_DIR.mkdir(exist_ok=True)

CACHE_FILE = CACHE_DIR / "live_cache.json"


def read_cache() -> dict:
    """Read live Kite cache (positions, margins, account)."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading cache: {e}")
    return {}


# ─── Health / Status ────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "AI Trading Dashboard API", "status": "running", "timestamp": datetime.now().isoformat()}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status")
async def get_status():
    is_live = CACHE_FILE.exists()
    cache_age = None
    if is_live:
        cache_age = datetime.now().timestamp() - CACHE_FILE.stat().st_mtime
    return {
        "status": "online",
        "version": "4.0-yfinance",
        "is_live": is_live,
        "cache_age_seconds": cache_age,
    }


# ─── Scanner ────────────────────────────────────────────────────

@app.get("/scan/latest")
async def get_latest_scan():
    """Get the most recent scan result."""
    try:
        files = list(ALERTS_DIR.glob("*.json"))
        if not files:
            return {"message": "No scans found", "data": []}
        latest_file = max(files, key=os.path.getctime)
        with open(latest_file, "r") as f:
            data = json.load(f)
        return {"timestamp": latest_file.stat().st_mtime, "data": data}
    except Exception as e:
        return {"error": str(e), "data": []}


@app.post("/scan/trigger")
async def trigger_scan():
    """Trigger a market scan — fetches live data from yfinance."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from market_scanner import run_scan
        results = run_scan()

        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "count": len(results),
            "data": results,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}


@app.get("/scan/live")
async def live_scan(universe: str = "quick", preset: str = None):
    """
    Live scan — returns results directly (Streak-like).
    ?universe=nifty50|banknifty|fno|quick
    &preset=rsi_oversold|volume_breakout|ema_crossover|supertrend_buy|...
    """
    try:
        from market_scanner import MarketScanner, SCANNER_PRESETS
        import os as _os

        config_path = str(BASE_DIR / "config" / "trading_rules.json")
        if not _os.path.exists(config_path):
            return {"status": "error", "error": "Config not found"}

        scanner = MarketScanner(config_path)
        results = scanner.live_scan(universe=universe, preset=preset)

        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "universe": universe,
            "preset": preset,
            "count": len(results),
            "data": results,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}


@app.get("/scan/presets")
async def get_presets():
    """Return available scanner presets (like Streak's scanner gallery)."""
    try:
        from market_scanner import SCANNER_PRESETS, UNIVERSES
        return {
            "presets": {
                key: {
                    "name": p["name"],
                    "description": p["description"],
                    "icon": p["icon"],
                    "conditions": p["conditions"],
                }
                for key, p in SCANNER_PRESETS.items()
            },
            "universes": {
                key: {"count": len(stocks), "stocks": list(stocks.keys())}
                for key, stocks in UNIVERSES.items()
            },
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/scan/custom")
async def custom_scan():
    """
    Run a scan with custom conditions.
    Body: {"universe": "nifty50", "conditions": [{"indicator": "RSI", "operator": ">", "value": 70}]}
    """
    try:
        from fastapi import Request
        # Read request body manually since we can't change the function signature
        import asyncio
        return {"status": "error", "error": "Use /scan/live with preset parameter instead"}
    except Exception as e:
        return {"error": str(e)}


# ─── Journal / Trade Log ───────────────────────────────────────

@app.get("/journal/trades")
async def get_journal_trades():
    """Get all trades from the trade logger with performance summary."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from trade_logger import TradeLogger
        logger = TradeLogger(journal_dir=str(JOURNALS_DIR))

        trades = logger.trades or []
        open_trades = logger.get_open_trades()
        closed_trades = logger.get_closed_trades()
        summary = logger.get_performance_summary()

        return {
            "trades": trades,
            "open_count": len(open_trades),
            "closed_count": len(closed_trades),
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"trades": [], "open_count": 0, "closed_count": 0, "summary": {}, "error": str(e)}


@app.get("/journal/activity")
async def get_journal_activity():
    """Read JSONL journal files and return activity grouped by date for heatmap."""
    try:
        activity: dict = {}
        if JOURNALS_DIR.exists():
            for jf in sorted(JOURNALS_DIR.glob("journal_*.jsonl")):
                with open(jf) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            ts = entry.get("timestamp", "")
                            date_key = ts[:10]  # YYYY-MM-DD
                            if date_key not in activity:
                                activity[date_key] = {"scans": 0, "trades": 0, "entries": []}
                            if entry.get("type") == "scan":
                                activity[date_key]["scans"] += 1
                            elif entry.get("type") in ("entry", "exit"):
                                activity[date_key]["trades"] += 1
                            activity[date_key]["entries"].append(entry)
                        except json.JSONDecodeError:
                            continue

        return {"activity": activity, "total_days": len(activity), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"activity": {}, "error": str(e)}


# ─── Chart Data (yfinance) ──────────────────────────────────────


@app.get("/chart/{symbol}")
async def get_chart_data(symbol: str, period: str = "6mo"):
    """Get OHLCV candlestick data from yfinance for lightweight-charts."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from market_scanner import fetch_ohlcv, WATCHLIST

        symbol_upper = symbol.upper()
        yf_ticker = WATCHLIST.get(symbol_upper, f"{symbol_upper}.NS")

        df = fetch_ohlcv(symbol_upper, yf_ticker, period=period)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol_upper}")

        candles = []
        volumes = []
        for _, row in df.iterrows():
            date_str = str(row["date"])[:10]
            candles.append({
                "time": date_str,
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
            })
            volumes.append({
                "time": date_str,
                "value": int(row.get("volume", 0)),
                "color": "rgba(6,182,212,0.3)" if row["close"] >= row["open"] else "rgba(239,68,68,0.3)",
            })

        return {"symbol": symbol_upper, "candles": candles, "volumes": volumes}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chart/{symbol}/analysis")
async def get_chart_analysis(symbol: str):
    """Get technical analysis overlays (EMA, S/R, FVG, patterns) from yfinance data."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from market_scanner import fetch_ohlcv, MarketScanner, WATCHLIST
        import pandas as pd

        symbol_upper = symbol.upper()
        yf_ticker = WATCHLIST.get(symbol_upper, f"{symbol_upper}.NS")

        df = fetch_ohlcv(symbol_upper, yf_ticker)
        if df.empty or len(df) < 50:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol_upper}")

        config_path = str(BASE_DIR / "config" / "trading_rules.json")
        scanner = MarketScanner(config_path)
        analysis = scanner.analyzer.analyze_stock(symbol_upper, df)

        if analysis is None:
            return {"symbol": symbol_upper, "error": "Insufficient data"}

        # EMA overlays
        ema20 = df["close"].ewm(span=20).mean()
        ema50 = df["close"].ewm(span=50).mean()

        ema20_data = []
        ema50_data = []
        for i, row in df.iterrows():
            date_str = str(row["date"])[:10]
            if not pd.isna(ema20.iloc[i]):
                ema20_data.append({"time": date_str, "value": round(float(ema20.iloc[i]), 2)})
            if not pd.isna(ema50.iloc[i]):
                ema50_data.append({"time": date_str, "value": round(float(ema50.iloc[i]), 2)})

        sr = analysis.get("sr_levels", {})

        fvgs = []
        for fvg in analysis.get("fvgs", []):
            fvgs.append({"type": fvg["type"], "high": round(fvg["high"], 2), "low": round(fvg["low"], 2)})

        patterns = analysis.get("patterns", [])
        pattern_markers = []
        if patterns:
            last_date = str(df.iloc[-1]["date"])[:10]
            for p in patterns:
                is_bullish = "bullish" in p or "hammer" in p or "morning" in p
                label = scanner.PATTERN_LABELS.get(p, p.replace("_", " ").title())
                pattern_markers.append({
                    "time": last_date,
                    "position": "aboveBar" if is_bullish else "belowBar",
                    "color": "#06b6d4" if is_bullish else "#ef4444",
                    "shape": "arrowUp" if is_bullish else "arrowDown",
                    "text": label,
                })

        return {
            "symbol": symbol_upper,
            "score": analysis["score"],
            "trend": analysis.get("trend", {}),
            "ema20": ema20_data,
            "ema50": ema50_data,
            "support": [round(s, 2) for s in sr.get("support", [])],
            "resistance": [round(r, 2) for r in sr.get("resistance", [])],
            "fvgs": fvgs,
            "patterns": pattern_markers,
            "setup_type": analysis.get("setup_type", "SKIP"),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/chart/symbols")
async def get_available_symbols():
    """Get list of symbols in the watchlist."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from market_scanner import WATCHLIST
        return {"symbols": list(WATCHLIST.keys())}
    except Exception:
        return {"symbols": []}


# ─── Account / Positions (Kite live cache) ──────────────────────

@app.get("/positions")
async def get_positions():
    try:
        data = read_cache()
        if not data:
            return {"positions": [], "pnl": 0.0, "is_live": False}
        positions = data.get("positions", [])
        total_pnl = data.get("session_pnl", sum(p.get("pnl", 0) for p in positions))
        return {"positions": positions, "pnl": total_pnl, "is_live": True, "last_update": data.get("timestamp")}
    except Exception as e:
        return {"error": str(e), "positions": [], "pnl": 0.0}


@app.get("/stats/market-pulse")
async def get_market_pulse():
    try:
        data = read_cache()
        if data:
            session_pnl = data.get("session_pnl", 0)
            if session_pnl > 5000:
                sentiment, trend = 85, "strongly bullish"
            elif session_pnl > 1000:
                sentiment, trend = 70, "bullish"
            elif session_pnl > 0:
                sentiment, trend = 60, "mildly bullish"
            elif session_pnl > -1000:
                sentiment, trend = 45, "neutral"
            else:
                sentiment, trend = 30, "bearish"
            return {
                "sentiment_score": sentiment, "trend": trend, "volatility": "moderate",
                "nifty_ltp": data.get("nifty_ltp", 0), "session_pnl": session_pnl,
                "total_realized": data.get("total_realized", 0),
                "total_unrealized": data.get("total_unrealized", 0), "is_live": True,
            }
        return {"sentiment_score": 50, "trend": "neutral", "volatility": "unknown", "is_live": False}
    except Exception as e:
        return {"error": str(e), "sentiment_score": 50, "trend": "error"}


@app.get("/account/profile")
async def get_profile():
    data = read_cache()
    account = data.get("account", {})
    return {
        "user_name": account.get("user_name", "Trader"),
        "user_shortname": account.get("user_shortname", ""),
        "user_id": account.get("user_id", ""),
        "broker": account.get("broker", ""),
        "is_live": bool(account),
    }


@app.get("/account/margins")
async def get_margins():
    data = read_cache()
    margins = data.get("margins", {})
    return {
        "net": margins.get("net", 0), "cash": margins.get("cash", 0),
        "collateral": margins.get("collateral", 0),
        "option_premium_used": margins.get("option_premium_used", 0),
        "is_live": bool(margins),
    }


@app.get("/account/holdings")
async def get_holdings():
    data = read_cache()
    return {"holdings": data.get("holdings", []), "is_live": True}


@app.get("/account/summary")
async def get_account_summary():
    data = read_cache()
    margins = data.get("margins", {})
    positions = data.get("positions", [])
    active = [p for p in positions if p.get("quantity", 0) != 0]
    closed = [p for p in positions if p.get("quantity", 0) == 0]
    return {
        "account": data.get("account", {}), "margins": margins,
        "positions": active, "closed_positions": closed,
        "holdings": data.get("holdings", []),
        "session_pnl": data.get("session_pnl", 0),
        "total_realized": data.get("total_realized", 0),
        "total_unrealized": data.get("total_unrealized", 0),
        "nifty_ltp": data.get("nifty_ltp", 0),
        "timestamp": data.get("timestamp"),
        "is_live": data.get("is_live", False),
    }

# ─── Signal Engine ──────────────────────────────────────────────

@app.get("/signal/{symbol}")
async def get_signal_analysis(symbol: str):
    """Run signal engine analysis (VWAP, RSI, Supertrend, etc.) on a symbol."""
    try:
        from signal_engine import SignalEngine
        from market_scanner import fetch_ohlcv, WATCHLIST

        symbol_upper = symbol.upper()
        yf_ticker = WATCHLIST.get(symbol_upper, f"{symbol_upper}.NS")

        df = fetch_ohlcv(symbol_upper, yf_ticker)
        if df.empty or len(df) < 20:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol_upper}")

        candles = []
        for _, row in df.tail(100).iterrows():
            candles.append({
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "volume": float(row["volume"]),
            })

        engine = SignalEngine()
        result = engine.analyze(candles, symbol_upper, "daily")

        return {"symbol": symbol_upper, "analysis": result}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# ─── Risk Manager ───────────────────────────────────────────────

@app.get("/risk/dashboard")
async def get_risk_dashboard():
    """Get real-time risk metrics: portfolio heat, drawdown, Kelly sizing."""
    try:
        from risk_manager import RiskManager

        data = read_cache()
        positions = data.get("positions", [])
        session_pnl = data.get("session_pnl", 0)
        margins = data.get("margins", {})

        capital = margins.get("net", 100000) or 100000
        rm = RiskManager(config={"total_capital": capital, "max_portfolio_heat": 10.0,
            "max_single_trade_risk": 2.0, "daily_loss_limit": 3.0,
            "weekly_loss_limit": 7.0, "max_consecutive_losses": 3,
            "max_sector_exposure_pct": 40, "max_correlated_positions": 2,
            "max_open_positions": 3, "max_open_options": 2})

        dashboard = rm.get_risk_dashboard(positions, session_pnl)
        return dashboard

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/risk/check/{symbol}")
async def pre_trade_risk_check(symbol: str, is_options: bool = False):
    """Pre-trade risk gate — checks all limits before allowing a trade."""
    try:
        from risk_manager import RiskManager

        data = read_cache()
        positions = data.get("positions", [])
        session_pnl = data.get("session_pnl", 0)
        capital = data.get("margins", {}).get("net", 100000) or 100000

        rm = RiskManager(config={"total_capital": capital, "max_portfolio_heat": 10.0,
            "max_single_trade_risk": 2.0, "daily_loss_limit": 3.0,
            "weekly_loss_limit": 7.0, "max_consecutive_losses": 3,
            "max_sector_exposure_pct": 40, "max_correlated_positions": 2,
            "max_open_positions": 3, "max_open_options": 2})

        result = rm.full_risk_check(symbol.upper(), positions, session_pnl, is_options=is_options)
        return result

    except Exception as e:
        return {"error": str(e)}


# ─── Trade Recommendation ──────────────────────────────────────

@app.get("/trade/recommend/{symbol}")
async def get_trade_recommendation(symbol: str):
    """
    Full trade recommendation: scanner + signal engine + mode selector + risk check.
    This is the "one-click" analysis endpoint.
    """
    try:
        from signal_engine import SignalEngine
        from market_scanner import fetch_ohlcv, MarketScanner, WATCHLIST
        from mode_selector import ModeSelector
        from risk_manager import RiskManager
        import datetime as dt

        symbol_upper = symbol.upper()
        yf_ticker = WATCHLIST.get(symbol_upper, f"{symbol_upper}.NS")

        # 1. Fetch data
        df = fetch_ohlcv(symbol_upper, yf_ticker)
        if df.empty or len(df) < 50:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol_upper}")

        # 2. Scanner analysis
        config_path = str(BASE_DIR / "config" / "trading_rules.json")
        scanner = MarketScanner(config_path)
        analysis = scanner.analyzer.analyze_stock(symbol_upper, df)
        if analysis is None:
            return {"symbol": symbol_upper, "recommendation": "SKIP", "reason": "Insufficient data"}

        # 3. Signal engine
        candles = []
        for _, row in df.tail(100).iterrows():
            candles.append({"open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "volume": float(row["volume"])})

        engine = SignalEngine()
        signal = engine.analyze(candles, symbol_upper, "daily")

        # 4. Mode selection
        data = read_cache()
        margins = data.get("margins", {})
        cash = margins.get("cash", 50000) or 50000
        margin = margins.get("net", 50000) or 50000

        selector = ModeSelector()
        mode = selector.select_mode(
            score=analysis["score"],
            current_time=dt.datetime.now().time(),
            available_cash=cash,
            available_margin=margin,
            symbol=symbol_upper,
            trend_strength=signal.get("trend_strength", "moderate"),
        )

        # 5. Risk check
        positions = data.get("positions", [])
        rm = RiskManager(config={"total_capital": margin, "max_portfolio_heat": 10.0,
            "max_single_trade_risk": 2.0, "daily_loss_limit": 3.0,
            "weekly_loss_limit": 7.0, "max_consecutive_losses": 3,
            "max_sector_exposure_pct": 40, "max_correlated_positions": 2,
            "max_open_positions": 3, "max_open_options": 2})
        risk = rm.full_risk_check(symbol_upper, positions,
                                  data.get("session_pnl", 0),
                                  is_options=(mode["mode"] == "FNO_NRML"))

        return {
            "symbol": symbol_upper,
            "score": analysis["score"],
            "setup_type": analysis.get("setup_type", "SKIP"),
            "signal": {
                "direction": signal.get("direction", "NEUTRAL"),
                "confidence": signal.get("confidence", 50),
                "trend_strength": signal.get("trend_strength", "weak"),
                "signals": signal.get("signals", []),
            },
            "mode": mode,
            "risk": risk,
            "price": analysis.get("current_price"),
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# ─── Execution Engine ──────────────────────────────────────────

@app.post("/execute/order")
async def execute_order(request: Request):
    """
    Place a trade order via ExecutionEngine.
    Body: { symbol, direction, quantity?, dry_run? }
    """
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        body = await request.json()
        symbol = body.get("symbol", "")
        direction = body.get("direction", "BUY")
        quantity = body.get("quantity", 1)
        dry_run = body.get("dry_run", True)  # Default to dry-run for safety

        from execution_engine import ExecutionEngine
        from kite_client import KiteMCPClient

        client = KiteMCPClient()
        engine = ExecutionEngine(client, config={"dry_run": dry_run, "require_confirmation": False})

        trade_plan = {
            "action": "TRADE",
            "option": {"tradingsymbol": symbol, "exchange": "NSE"},
            "position": {"quantity": quantity, "total_cost": 0, "premium": 0, "product": "CNC"},
            "exit_levels": {},
            "direction": direction,
            "underlying": symbol,
            "score": body.get("score", 0),
        }

        # Pre-trade checks
        checks = engine.pre_trade_checks(trade_plan)
        if not checks["passed"]:
            return {"status": "BLOCKED", "reason": checks["reason"], "timestamp": datetime.now().isoformat()}

        result = engine.place_options_order(trade_plan)
        return {"status": result.get("status", "UNKNOWN"), "result": result, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}


@app.get("/execute/summary")
async def get_execution_summary():
    """Get today's execution summary — orders placed, success rate, P&L."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from execution_engine import ExecutionEngine
        from kite_client import KiteMCPClient

        client = KiteMCPClient()
        engine = ExecutionEngine(client)
        summary = engine.get_daily_summary()

        return {"summary": summary, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"summary": {}, "error": str(e)}


@app.post("/execute/pre-check")
async def pre_trade_check(request: Request):
    """Run pre-trade safety checks without placing an order."""
    try:
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        body = await request.json()
        from execution_engine import ExecutionEngine
        from kite_client import KiteMCPClient

        client = KiteMCPClient()
        engine = ExecutionEngine(client)

        trade_plan = {
            "action": "TRADE",
            "option": {"tradingsymbol": body.get("symbol", ""), "exchange": "NSE"},
            "position": {"quantity": body.get("quantity", 1), "total_cost": 0},
        }
        result = engine.pre_trade_checks(trade_plan)
        return {"checks": result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"checks": {"passed": False, "reason": str(e)}}

# ─── System Info ────────────────────────────────────────────────

@app.get("/system/modules")
async def get_module_status():
    """Check which modules are available and working."""
    modules = {}
    for mod_name in ["signal_engine", "risk_manager", "mode_selector",
                     "options_analyzer", "execution_engine", "market_scanner",
                     "exit_manager", "cost_tracker", "learning_engine"]:
        try:
            __import__(mod_name)
            modules[mod_name] = "✅ loaded"
        except Exception as e:
            modules[mod_name] = f"❌ {e}"
    return {"modules": modules, "timestamp": datetime.now().isoformat()}


# ─── Config Management ──────────────────────────────────────────

@app.get("/config")
async def get_config():
    """Read the current trading_rules.json config."""
    config_path = BASE_DIR / "config" / "trading_rules.json"
    try:
        with open(config_path) as f:
            config = json.load(f)
        return {"config": config, "path": str(config_path), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}


@app.put("/config")
async def update_config(request: Request):
    """Update trading_rules.json with new values. Merges top-level keys."""
    config_path = BASE_DIR / "config" / "trading_rules.json"
    try:
        body = await request.json()
        updates = body.get("config", body)

        # Load existing
        with open(config_path) as f:
            config = json.load(f)

        # Deep merge: for each section, update individual keys
        for section, values in updates.items():
            if isinstance(values, dict) and section in config and isinstance(config[section], dict):
                config[section].update(values)
            else:
                config[section] = values

        # Write back
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return {"status": "updated", "config": config, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("Starting AI Trading Dashboard API v2")
    print("  Charts/Scanner: yfinance (free)")
    print("  Signal Engine:  VWAP, RSI, Supertrend, multi-TF")
    print("  Risk Manager:   Portfolio heat, Kelly sizing")
    print("  Live Data:      Kite (via cache, free tier OK)")
    print("Serving on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
