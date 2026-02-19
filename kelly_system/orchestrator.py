import logging
import time
import datetime
import sys
from kelly_system.config import *
from kelly_system.market_data import MarketDataManager
from kelly_system.strategy_engine import StrategyEngine, KellySolver, SignalGenerator
from kelly_system.order_manager import OrderManager

# Setup Logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kelly_system/trading.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_trading_workflow(dry_run=True):
    logger.info("xxx Starting Morning Trading Workflow xxx")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    # 1. Initialize Components
    try:
        dm = MarketDataManager()
        engine = StrategyEngine()
        kelly = KellySolver()
        signal_gen = SignalGenerator(dm, engine, kelly)
        order_mgr = OrderManager(dm)
    except Exception as e:
        logger.critical(f"Initialization Failed: {e}")
        return

    # 2. Run Analysis & Generate Signal
    logger.info("Running Strategy Analysis...")
    result = signal_gen.run_analysis()
    
    if not result:
        logger.error("Analysis failed to produce a result.")
        return
        
    logger.info(f"Analysis Result: {result}")
    
    # 3. Execute Signal
    signal = result['signal']
    allocation = result['allocation']
    
    if signal == "HOLD":
        logger.info("Strategy says HOLD. No trades today.")
    else:
        logger.info(f"Conviction Buy Signal: {signal} with {allocation*100}% Capital")
        if not dry_run:
            order_mgr.execute_strategy_signal(result)
        else:
            logger.info("[DRY RUN] Order Execution Skipped.")
            
    logger.info("xxx Workflow Complete xxx")

if __name__ == "__main__":
    # Simple scheduler loop or run-once
    # Ideally run via Windows Task Scheduler or Cron
    # Here we default to running once immediately for testing
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help="Execute real orders")
    args = parser.parse_args()
    
    run_trading_workflow(dry_run=not args.live)
