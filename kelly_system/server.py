from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import threading
import time
import datetime
import os
from contextlib import asynccontextmanager
from kelly_system.orchestrator import run_trading_workflow, logger
from kelly_system.market_data import MarketDataManager
from kelly_system.order_manager import OrderManager
from kelly_system.config import *

# Global State for Dashboard
dashboard_state = {
    "last_run": None,
    "signal": "WAITING",
    "allocation": 0.0,
    "win_prob": 0.0,
    "win_loss_ratio": 0.0,
    "price": 0.0,
    "status": "Idle"
}

# Background Runner
def background_scheduler():
    last_strategy_run = 0
    strategy_interval = 300 # 5 Minutes
    
    while True:
        try:
            try:
                # 1. Fast Update: Live Price & Portfolio
                dm = MarketDataManager()
                
                # Fetch Live Nifty Price
                try:
                    ltp_data = dm.kite.ltp("NSE:NIFTY 50")
                    if "NSE:NIFTY 50" in ltp_data:
                        live_price = ltp_data["NSE:NIFTY 50"]["last_price"]
                        dashboard_state["price"] = live_price
                        dashboard_state["last_update"] = datetime.datetime.now().strftime("%H:%M:%S")
                except BaseException as e:
                    # Fallback to yfinance if Kite LTP fails (Insufficient Permission) or any other error
                    # logger.warning(f"Kite LTP Failed: {e}. Switching to yfinance fallback.")
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker("^NSEI")
                        todays_data = ticker.history(period="1d")
                        if not todays_data.empty:
                            live_price = todays_data['Close'].iloc[-1]
                            dashboard_state["price"] = live_price
                            dashboard_state["last_update"] = datetime.datetime.now().strftime("%H:%M:%S")
                    except Exception as yf_e:
                        logger.error(f"Live Price Fetch Failed (Kite & YF): {yf_e}")
                        
            except BaseException as outer_e:
                import traceback
                logger.error(f"Critical Scheduler Error: {outer_e}\n{traceback.format_exc()}")
                dashboard_state["status"] = f"Error: See Logs"
            
            # 2. Slow Update: Strategy Analysis
            if time.time() - last_strategy_run > strategy_interval:
                logger.info("Dashboard Scheduler: Running Strategy Analysis...")
                dashboard_state["status"] = "Analyzing..."
                
                # We import other classes here to avoid circulars if any
                from kelly_system.strategy_engine import StrategyEngine, KellySolver, SignalGenerator
                
                engine = StrategyEngine()
                kelly = KellySolver()
                signal_gen = SignalGenerator(dm, engine, kelly)
                
                result = signal_gen.run_analysis()
                
                if result:
                    # Update all fields EXCEPT price (to avoid overwriting live price with old one if lag)
                    # Actually result['price'] is snapshot, live_price is newer.
                    dashboard_state.update(result)
                    
                    # Calculate Suggestion (Order Ticket)
                    # Re-calculate suggestion based on NEW price/margin?
                    # Ideally yes, but sticking to strategy snapshot is safer for consistency.
                    from kelly_system.order_manager import OrderManager
                    ord_mgr = OrderManager(dm)
                    suggestion = ord_mgr.calculate_suggestion(result)
                    dashboard_state["suggestion"] = suggestion
                    
                    dashboard_state["last_run"] = datetime.datetime.now().isoformat()
                    dashboard_state["status"] = "Active"
                else:
                     dashboard_state["status"] = "Error (No Result)"
                
                last_strategy_run = time.time()
            
            # Update Status text if idle
            if dashboard_state["status"] == "Analyzing..." and time.time() - last_strategy_run > 10:
                 dashboard_state["status"] = "Live Monitoring"

        except Exception as e:
            logger.error(f"Dashboard Scheduler Error: {e}")
            dashboard_state["status"] = f"Error: {str(e)}"
            
        # Fast Sleep (5 seconds)
        time.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Background Thread
    t = threading.Thread(target=background_scheduler, daemon=True)
    t.start()
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Setup Templates (We will create a 'templates' dir)
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

app.mount("/static", StaticFiles(directory=templates_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/state")
async def get_state():
    return dashboard_state

@app.get("/api/portfolio")
async def get_portfolio():
    try:
        dm = MarketDataManager()
        return dm.fetch_portfolio()
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/execute_trade")
async def execute_trade():
    """
    Executes the current signal immediately.
    """
    try:
        logger.info("One-Click Trade Execution Requested from Dashboard")
        dm = MarketDataManager()
        # Re-import to ensure fresh order manager
        from kelly_system.order_manager import OrderManager
        ord_mgr = OrderManager(dm)
        
        # Use current state signal
        if dashboard_state.get('signal') == "WAITING" or not dashboard_state.get('signal'):
            return {"status": "error", "message": "No Signal to Execute"}
            
        # Execute
        result = ord_mgr.execute_strategy_signal(dashboard_state)
        if result:
             return {"status": "success", "order_id": result}
        else:
             return {"status": "error", "message": "Execution Failed (Check Logs)"}
             
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
