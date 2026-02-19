import os
import sys

# Use relative path
log_file = "diagnostic_log.txt"

def log(msg):
    try:
        with open(log_file, "a") as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

try:
    log("Starting diagnostics (retry)...")
    cwd = os.getcwd()
    log(f"Current Working Directory: {cwd}")
    
    # Try listing current directory
    try:
        files = os.listdir(".")
        log(f"Listing contents of current dir ({cwd}):")
        for f in files:
            log(f" - {f}")
    except Exception as e:
        log(f"Error listing dir: {e}")

    # Check Nifty Strategy specific files
    sim_file = "Nifty_Backtest_Simulator.py"
    if os.path.exists(sim_file):
        log(f"{sim_file} found!")
        try:
            # Try running the test
            import Nifty_Backtest_Simulator
            log("Import successful! Running Test Scenarios...")
            
            sim = Nifty_Backtest_Simulator.NiftyBacktestSimulator()
            
            # Simple run without capture first to test execution
            sim.generate_scenario("BULL")
            log("Scenario generation works.")
            
            # Run full backtest logic
            log("--- SIMULATION OUTPUT START ---")
            
            # Since we can't redirect stdout easily inside, let's modify how we run it or just print to log
            # Or just run it and hope prints go to stdout which we might see?
            # Actually, let's redefine print
            import builtins
            original_print = builtins.print
            def new_print(*args, **kwargs):
                msg = " ".join(map(str, args))
                log(msg)
                # original_print(*args, **kwargs) # detailed output
            
            builtins.print = new_print
            
            bull_data = sim.generate_scenario("BULL")
            sim.run_backtest("Strong Bull Market", bull_data)
            
            bear_data = sim.generate_scenario("BEAR")
            sim.run_backtest("Panic Crash", bear_data)
            
            chop_data = sim.generate_scenario("CHOP")
            sim.run_backtest("Sideways/Choppy", chop_data)
            
            builtins.print = original_print
            log("--- SIMULATION OUTPUT END ---")
            
        except Exception as e:
            log(f"Error running simulation: {e}")
            import traceback
            log(traceback.format_exc())
    else:
        log(f"{sim_file} NOT found.")

except Exception as e:
    log(f"Fatal error: {e}")
