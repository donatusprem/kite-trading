import random
from Nifty_Strategy_Engine import NiftyStrategyEngine

class NiftyBacktestSimulator:
    """
    Simulates Nifty market scenarios to backtest the Strategy Engine.
    Generates synthetic price, OI, and Volatility data.
    """
    
    def __init__(self):
        self.engine = NiftyStrategyEngine()
        self.results = []
        self.balance = 100000 # Starting hypothetical capital
        self.position = None # {'type': 'CE'/'PE', 'entry': 100, 'size': 50}
        
    def generate_scenario(self, scenario_type="BULL", minutes=375): # 375 mins in trading day
        """
        Generates a sequence of market data points.
        """
        data_stream = []
        
        # Initial Conditions
        price = 24500
        pe_oi = 1500000
        ce_oi = 1500000
        vix = 15.0
        pivot = 24500
        
        # Trend Bias
        if scenario_type == "BULL":
            price_drift = 0.5   # Upwards drift
            oi_drift = 1000     # PE OI increases (support building)
        elif scenario_type == "BEAR":
            price_drift = -0.6
            oi_drift = -1000    # PE OI unwinding (fear)
        else: # CHOP/RANGE
            price_drift = 0
            oi_drift = 0
            
        history = [price] * 50 # Seed history
        
        for m in range(minutes):
            # 1. Update Price (Random Walk with Drift)
            noise = random.uniform(-5, 5)
            price += price_drift + noise
            history.append(price)
            if len(history) > 50: history.pop(0) # Keep window sized
            
            # 2. Update OI (Sentiment)
            # Bullish: PE OI goes UP (Writing puts), CE OI stays flat or down
            # Bearish: CE OI goes UP (Writing calls), PE OI down
            if scenario_type == "BULL":
                pe_oi += random.randint(500, 2000)
                ce_oi += random.randint(-500, 500)
            elif scenario_type == "BEAR":
                ce_oi += random.randint(500, 2000)
                pe_oi += random.randint(-2000, 0) # Short covering or unwinding
            else:
                pe_oi += random.randint(-1000, 1000)
                ce_oi += random.randint(-1000, 1000)
                
            # 3. VIX behavior
            if scenario_type == "BEAR" and m % 30 == 0:
                vix += 0.1 # VIX rises in panic
            elif scenario_type == "BULL" and m % 60 == 0:
                vix -= 0.05 # VIX cools in rally
                
            market_data = {
                'time_step': m,
                'current_price': price,
                'historical_prices': list(history),
                'pe_oi_total': pe_oi,
                'ce_oi_total': ce_oi,
                'pivot_points': {'P': pivot, 'R1': pivot+100, 'S1': pivot-100},
                'vix': vix
            }
            data_stream.append(market_data)
            
        return data_stream

    def run_backtest(self, scenario_name, data_stream):
        print(f"\n--- Running Backtest: {scenario_name} ---")
        trades = 0
        wins = 0
        total_pl_points = 0
        
        for data in data_stream:
            # 1. Get Strategy Signal
            result = self.engine.calculate_nifty_conviction(data)
            score = result['total_score']
            price = data['current_price']
            
            # 2. Entry Logic
            if self.position is None:
                if score >= 40: # High Conviction Entry
                    direction = "BULL" if "BULLISH" in str(result['signals']) or data['pe_oi_total'] > data['ce_oi_total'] else "BEAR"
                    
                    self.position = {
                        'entry_price': price,
                        'direction': direction,
                        'time': data['time_step']
                    }
                    print(f"[{data['time_step']}m] ENTRY {direction} @ {price:.2f} | Score: {score}")

            # 3. Exit Logic (Simple Target/Stop)
            elif self.position:
                entry = self.position['entry_price']
                direction = self.position['direction']
                
                # Targets (Scalping Logic)
                target = 30 # points
                stop = 15   # points
                
                pl = 0
                exit_signal = False
                
                if direction == "BULL":
                    if price >= entry + target:
                        pl = target
                        exit_signal = True
                        print(f"[{data['time_step']}m] TARGET HIT (+{pl}) @ {price:.2f}")
                    elif price <= entry - stop:
                        pl = -stop
                        exit_signal = True
                        print(f"[{data['time_step']}m] STOP HIT ({pl}) @ {price:.2f}")
                else: # BEAR
                    if price <= entry - target:
                        pl = target # Short profit
                        exit_signal = True
                        print(f"[{data['time_step']}m] TARGET HIT (+{pl}) @ {price:.2f}")
                    elif price >= entry + stop:
                        pl = -stop
                        exit_signal = True
                        print(f"[{data['time_step']}m] STOP HIT ({pl}) @ {price:.2f}")

                if exit_signal:
                    trades += 1
                    if pl > 0: wins += 1
                    total_pl_points += pl
                    self.position = None # Reset
                    
        print(f"\nRESULTS for {scenario_name}:")
        print(f"Total Trades: {trades}")
        if trades > 0:
            print(f"Win Rate: {(wins/trades)*100:.1f}%")
        print(f"Total P&L Points: {total_pl_points}")
        print("-------------------------------")

if __name__ == "__main__":
    sim = NiftyBacktestSimulator()
    
    # 1. Bull Scenario
    bull_data = sim.generate_scenario("BULL")
    sim.run_backtest("Strong Bull Market", bull_data)
    
    # 2. Bear Scenario
    bear_data = sim.generate_scenario("BEAR")
    sim.run_backtest("Panic Crash", bear_data)
    
    # 3. Choppy Scenario
    chop_data = sim.generate_scenario("CHOP")
    sim.run_backtest("Sideways/Choppy", chop_data)

