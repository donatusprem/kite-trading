import datetime

class NiftyStrategyEngine:
    """
    Dedicated engine for Nifty 50 Options Strategy.
    Combines Technicals, Open Interest (OI), and Price Action for High Conviction.
    """

    def __init__(self):
        self.conviction_score = 0
        self.signals = []
        
    def analyze_technicals(self, prices, period_short=20, period_long=50):
        """
        Analyze EMA trends and RSI.
        Args:
            prices (list/pd.Series): List of closing prices.
        """
        # Placeholder for actual technical calculation
        # In a real scenario, use pandas_ta or ta-lib
        # Simple logic for demonstration if no library:
        if len(prices) < period_long:
            return "NEUTRAL", 0
            
        current_price = prices[-1]
        # Mock calculation
        ema_short = sum(prices[-period_short:]) / period_short # Very rough SMA/EMA approx
        ema_long = sum(prices[-period_long:]) / period_long
        
        trend = "NEUTRAL"
        score = 0
        
        if ema_short > ema_long and current_price > ema_short:
            trend = "BULLISH"
            score = 20
        elif ema_short < ema_long and current_price < ema_short:
            trend = "BEARISH"
            score = 20
            
        return trend, score

    def analyze_oi_pcr(self, pe_oi, ce_oi):
        """
        Analyze Put-Call Ratio (PCR).
        PCR = Total PE OI / Total CE OI
        > 1.2 : Bullish (Puts selling > Calls selling => Support building)
        < 0.8 : Bearish (Calls selling > Puts selling => Resistance building)
        """
        if ce_oi == 0:
            return "NEUTRAL", 0
            
        pcr = pe_oi / ce_oi
        
        sentiment = "NEUTRAL"
        score = 0
        
        if pcr > 1.2:
            sentiment = "BULLISH"
            score = 15
        elif pcr < 0.8:
            sentiment = "BEARISH"
            score = 15
        elif 0.8 <= pcr <= 1.2:
            sentiment = "RANGE_BOUND"
            score = 5
            
        return sentiment, score, pcr

    def analyze_price_action(self, current_price, pivot_points):
        """
        Check relationship with Pivot Points.
        pivot_points = {'R1': ..., 'R2': ..., 'S1': ..., 'S2': ..., 'P': ...}
        """
        behavior = "NEUTRAL"
        score = 0
        
        if current_price > pivot_points['P']:
            if current_price > pivot_points['R1']:
                behavior = "BREAKOUT_R1"
                score = 15 # Strong Bullish
            else:
                behavior = "ABOVE_PIVOT"
                score = 10 # Bullish bias
        elif current_price < pivot_points['P']:
            if current_price < pivot_points['S1']:
                behavior = "BREAKDOWN_S1"
                score = 15 # Strong Bearish
            else:
                behavior = "BELOW_PIVOT"
                score = 10 # Bearish bias
                
        return behavior, score

    def calculate_nifty_conviction(self, market_data):
        """
        Master function to aggregate all analysis.
        market_data expected keys:
        - 'current_price'
        - 'historical_prices' (list)
        - 'pe_oi_total'
        - 'ce_oi_total'
        - 'pivot_points' (dict)
        - 'vix' (volatility index)
        """
        self.conviction_score = 0
        self.signals = []
        
        # 1. Technical Analysis (Trend)
        trend, trend_score = self.analyze_technicals(market_data.get('historical_prices', []))
        self.conviction_score += trend_score
        self.signals.append(f"Trend: {trend} (+{trend_score})")
        
        # 2. Open Interest (Sentiment)
        oi_sentiment, oi_score, pcr = self.analyze_oi_pcr(
            market_data.get('pe_oi_total', 0), 
            market_data.get('ce_oi_total', 1)
        )
        self.conviction_score += oi_score
        self.signals.append(f"PCR: {pcr:.2f} ({oi_sentiment}) (+{oi_score})")
        
        # 3. Price Action (Levels)
        pa_behavior, pa_score = self.analyze_price_action(
            market_data.get('current_price', 0), 
            market_data.get('pivot_points', {'P': 0, 'R1': 0, 'S1': 0}) # Default safe
        )
        self.conviction_score += pa_score
        self.signals.append(f"Price Action: {pa_behavior} (+{pa_score})")
        
        # 4. VIX (Volatility Confirmation)
        # If VIX is rising, option buying is favorable. If falling/low, selling is better.
        vix = market_data.get('vix', 15)
        if 12 <= vix <= 20:
             self.signals.append("VIX: Normal (Good for directional)")
        elif vix > 20:
             self.signals.append("VIX: High (High premiums, caution needed)")
             
        return {
            "total_score": self.conviction_score,
            "signals": self.signals,
            "verdict": "HIGH" if self.conviction_score >= 40 else "MEDIUM" if self.conviction_score >= 20 else "LOW"
        }

# Example Usage
if __name__ == "__main__":
    engine = NiftyStrategyEngine()
    
    # Mock Data for Nifty
    mock_nifty_data = {
        'current_price': 24500,
        'historical_prices': [24100, 24200, 24300, 24400, 24450, 24500], # Bullish trend
        'pe_oi_total': 1500000, # High Put Writing (Support)
        'ce_oi_total': 1000000,
        'pivot_points': {'P': 24400, 'R1': 24550, 'S1': 24300},
        'vix': 14.5
    }
    
    result = engine.calculate_nifty_conviction(mock_nifty_data)
    print(f"Nifty Conviction Score: {result['total_score']}")
    print(f"Verdict: {result['verdict']}")
    for sig in result['signals']:
        print(f"- {sig}")
