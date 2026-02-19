from Nifty_Strategy_Engine import NiftyStrategyEngine

def test_nifty_strategy():
    print("Testing Nifty Strategy Engine...")
    engine = NiftyStrategyEngine()
    
    # Test Case 1: Strong Bullish
    bullish_data = {
        'current_price': 24500,
        'historical_prices': [24100, 24200, 24300, 24400, 24500],
        'pe_oi_total': 2000000,
        'ce_oi_total': 1000000, # PCR = 2.0 (Bullish)
        'pivot_points': {'P': 24400, 'R1': 24600, 'S1': 24300},
        'vix': 14
    }
    result = engine.calculate_nifty_conviction(bullish_data)
    print("\nTest Case 1 (Bullish):")
    print(f"Score: {result['total_score']}")
    print(f"Verdict: {result['verdict']}")
    assert result['verdict'] == 'HIGH', "Expected HIGH conviction for bullish case"
    
    # Test Case 2: Bearish
    bearish_data = {
        'current_price': 24000,
        'historical_prices': [24400, 24300, 24200, 24100, 24000],
        'pe_oi_total': 1000000,
        'ce_oi_total': 2000000, # PCR = 0.5 (Bearish)
        'pivot_points': {'P': 24100, 'R1': 24200, 'S1': 23900},
        'vix': 22 # High VIX
    }
    result = engine.calculate_nifty_conviction(bearish_data)
    print("\nTest Case 2 (Bearish):")
    print(f"Score: {result['total_score']}")
    print(f"Verdict: {result['verdict']}")
    # Adjust assertion based on scoring logic. Bearish trend & PCR should give points.
    # Current logic gives +20 for pattern? 
    # Logic in engine: 
    # Technicals: Bearish -> +20
    # PCR: <0.8 -> +15
    # Price Action: Below Pivot -> +10
    # Total: 45 -> HIGH
    assert result['verdict'] == 'HIGH', "Expected HIGH conviction for bearish case"

    print("\nAll tests passed!")

if __name__ == "__main__":
    test_nifty_strategy()
