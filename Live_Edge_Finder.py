#!/usr/bin/env python3
"""
LIVE EDGE FINDER - Automated High-Conviction Setup Scanner
Connects to Kite API and alerts you when your proven edge appears

This scans the market EVERY MINUTE for setups matching your winning patterns
"""

# NOTE: This requires the Kite MCP server to be running
# You can call this via Claude using the mcp__kite tools

class LiveEdgeFinder:
    """
    Scans for high-conviction setups based on YOUR proven patterns
    """

    # Your proven high-conviction symbols
    WATCHLIST = [
        'SBIN',      # 80% win rate, your specialty
        'VEDL',      # 100% win (1 trade)
        'JSWSTEEL',  # 100% win (1 trade)
        'HINDALCO',  # 100% win (1 trade)
        'NIFTY',     # Your big winner potential
    ]

    def __init__(self):
        """Initialize scanner"""
        self.high_conviction_setups = []
        self.alerts = []

    def check_volume_spike(self, symbol, current_volume, avg_volume):
        """
        Check if volume is 1.5x+ higher than average
        Returns: True if volume spike detected
        """
        if avg_volume == 0:
            return False

        volume_ratio = current_volume / avg_volume

        if volume_ratio >= 1.5:
            return True, volume_ratio
        return False, volume_ratio

    def check_price_breakout(self, current_price, resistance_level, support_level):
        """
        Check if price broke key levels
        Returns: True if breakout confirmed
        """
        # Breakout above resistance (bullish)
        if current_price > resistance_level:
            return True, 'BULLISH', (current_price - resistance_level) / resistance_level * 100

        # Breakdown below support (bearish)
        if current_price < support_level:
            return True, 'BEARISH', (support_level - current_price) / support_level * 100

        return False, 'NEUTRAL', 0

    def check_sector_momentum(self, sector_change_pct):
        """
        Check if sector is showing momentum (>0.5% move)
        """
        if abs(sector_change_pct) >= 0.5:
            return True, sector_change_pct
        return False, sector_change_pct

    def check_index_alignment(self, option_type, index_change_pct):
        """
        Check if index is moving in favor of your option
        CE (Call) needs index up, PE (Put) needs index down
        """
        if option_type == 'CE' and index_change_pct > 0:
            return True, index_change_pct
        elif option_type == 'PE' and index_change_pct < 0:
            return True, abs(index_change_pct)

        return False, index_change_pct

    def calculate_conviction_score(self, symbol, hour, minute, day_of_week,
                                   option_type, volume_spike, breakout,
                                   sector_momentum, index_alignment):
        """
        Calculate conviction score using the same system as Pre_Trade_Conviction_Checklist
        """
        score = 0

        # Symbol score (30 points)
        if symbol in ['SBIN', 'VEDL', 'JSWSTEEL', 'HINDALCO']:
            score += 30
        elif symbol in ['BANKNIFTY', 'MARUTI', 'M&M']:
            score -= 20
        else:
            score += 10

        # Timing score (20 points)
        if 10 <= hour < 14:  # Your best sessions
            score += 20
        elif hour < 10 or hour >= 14:
            score += 5
        else:
            score += 10

        # Day of week (10 points)
        if day_of_week in ['Monday', 'Friday']:
            score += 10
        elif day_of_week == 'Tuesday':
            score += 6
        else:
            score += 2

        # Option type (10 points)
        if option_type == 'CE':
            score += 10
        else:
            score += 5

        # Market signals (30 points)
        if volume_spike:
            score += 10
        if breakout:
            score += 10
        if sector_momentum:
            score += 5
        if index_alignment:
            score += 5

        return score

    def scan_for_setups(self, market_data):
        """
        Main scanner function
        Takes market data dict and returns high-conviction setups

        market_data format:
        {
            'SBIN': {
                'ltp': 1160.50,
                'volume': 150000,
                'avg_volume': 100000,
                'resistance': 1165,
                'support': 1150,
                'sector_change_pct': 0.8,
                'index_change_pct': 0.3,
            },
            ...
        }
        """
        from datetime import datetime
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        day_of_week = now.strftime('%A')

        self.high_conviction_setups = []

        for symbol, data in market_data.items():
            # Skip if not in watchlist
            if symbol not in self.WATCHLIST:
                continue

            # Special Handling for NIFTY
            if symbol == 'NIFTY':
                from Nifty_Strategy_Engine import NiftyStrategyEngine
                nifty_engine = NiftyStrategyEngine()
                
                # Nifty Engine expects specific data keys
                nifty_data = {
                    'current_price': data['ltp'],
                    'historical_prices': data.get('history', []), 
                    'pe_oi_total': data.get('pe_oi', 0),
                    'ce_oi_total': data.get('ce_oi', 0),
                    'pivot_points': data.get('pivots', {'P': data['ltp'], 'R1': data['ltp']*1.01, 'S1': data['ltp']*0.99}),
                    'vix': data.get('vix', 15)
                }
                
                nifty_result = nifty_engine.calculate_nifty_conviction(nifty_data)
                
                if nifty_result['total_score'] >= 20: # Threshold for Nifty
                    setup = {
                        'symbol': symbol,
                        'score': nifty_result['total_score'],
                        'ltp': data['ltp'],
                        'option_type': 'CE' if 'BULLISH' in str(nifty_result['signals']) else 'PE', # Simplified logic
                        'direction': nifty_result['verdict'],
                        'time': f"{current_hour:02d}:{current_minute:02d}",
                        'signals': {
                            'strategy': 'Nifty Special',
                            'details': nifty_result['signals']
                        },
                        'position_size': '1.5x (NIFTY SPECIAL)'
                    }
                    self.high_conviction_setups.append(setup)
                continue

            # Check all signals for other symbols
            volume_spike, vol_ratio = self.check_volume_spike(
                symbol, data['volume'], data['avg_volume']
            )

            breakout, direction, breakout_pct = self.check_price_breakout(
                data['ltp'], data.get('resistance', data['ltp'] * 1.01),
                data.get('support', data['ltp'] * 0.99)
            )

            sector_momentum, sector_pct = self.check_sector_momentum(
                data.get('sector_change_pct', 0)
            )

            # Determine option type based on direction
            if direction == 'BULLISH' or data.get('index_change_pct', 0) > 0:
                option_type = 'CE'
            else:
                option_type = 'PE'

            index_alignment, index_pct = self.check_index_alignment(
                option_type, data.get('index_change_pct', 0)
            )

            # Calculate conviction score
            score = self.calculate_conviction_score(
                symbol, current_hour, current_minute, day_of_week,
                option_type, volume_spike, breakout,
                sector_momentum, index_alignment
            )

            # Only alert on high-conviction setups (75+)
            if score >= 75:
                setup = {
                    'symbol': symbol,
                    'score': score,
                    'ltp': data['ltp'],
                    'option_type': option_type,
                    'direction': direction,
                    'time': f"{current_hour:02d}:{current_minute:02d}",
                    'signals': {
                        'volume_spike': f"{vol_ratio:.1f}x" if volume_spike else "No",
                        'breakout': f"{direction} {breakout_pct:.1f}%" if breakout else "No",
                        'sector_momentum': f"{sector_pct:+.1f}%" if sector_momentum else "No",
                        'index_alignment': f"{index_pct:+.1f}%" if index_alignment else "No",
                    },
                    'position_size': '1.5x (HIGH CONVICTION)'
                }

                self.high_conviction_setups.append(setup)

        return self.high_conviction_setups

    def generate_alert(self, setup):
        """Generate alert message for high-conviction setup"""
        alert = f"""
🔥 HIGH CONVICTION ALERT! Score: {setup['score']}/100

Symbol: {setup['symbol']}
Current Price: ₹{setup['ltp']:.2f}
Suggested Option: {setup['option_type']} ({"Call" if setup['option_type'] == 'CE' else "Put"})
Direction: {setup['direction']}
Time: {setup['time']}

SIGNALS:
  Volume: {setup['signals']['volume_spike']}
  Breakout: {setup['signals']['breakout']}
  Sector: {setup['signals']['sector_momentum']}
  Index: {setup['signals']['index_alignment']}

POSITION SIZE: {setup['position_size']}

This matches your proven winning pattern!
        """
        return alert.strip()


# ==============================================================================
# EXAMPLE USAGE WITH KITE API
# ==============================================================================

def example_usage():
    """
    Example of how to use this with live Kite data
    In practice, you'd call this every minute during market hours
    """

    print("="*80)
    print("LIVE EDGE FINDER - Scanning for High-Conviction Setups")
    print("="*80)

    # Example: Simulate market data
    # In real usage, fetch this from Kite API using:
    # - get_stock_quotes() for prices
    # - get_stock_bars() for volume
    # - get_ohlc() for resistance/support

    mock_market_data = {
        'SBIN': {
            'ltp': 1162.50,
            'volume': 180000,
            'avg_volume': 100000,  # 1.8x volume spike!
            'resistance': 1160,
            'support': 1150,
            'sector_change_pct': 0.9,  # Banking sector up
            'index_change_pct': 0.4,   # NIFTY up
        },
        'VEDL': {
            'ltp': 688.20,
            'volume': 140000,
            'avg_volume': 120000,  # 1.17x (no spike)
            'resistance': 685,
            'support': 680,
            'sector_change_pct': -0.2,
            'index_change_pct': 0.4,
        },
        'M&M': {  # Should not trigger (losing symbol)
            'ltp': 3755.00,
            'volume': 200000,
            'avg_volume': 100000,
            'resistance': 3750,
            'support': 3700,
            'sector_change_pct': 0.8,
            'index_change_pct': 0.4,
        },
        'NIFTY': { # New Nifty Strategy Test
            'ltp': 24500,
            'volume': 1000000,
            'avg_volume': 800000,
            'pe_oi': 2000000, # High Put OI (Bullish)
            'ce_oi': 1200000,
            'vix': 14,
            'history': [24300, 24350, 24400, 24450, 24500], # Up trend
            'pivots': {'P': 24400, 'R1': 24550, 'S1': 24300}
        }
    }

    scanner = LiveEdgeFinder()
    setups = scanner.scan_for_setups(mock_market_data)

    if setups:
        print(f"\n🎯 Found {len(setups)} HIGH-CONVICTION setups:\n")
        for setup in setups:
            print(scanner.generate_alert(setup))
            print("\n" + "-"*80 + "\n")
    else:
        print("\n⏳ No high-conviction setups right now. Keep scanning...\n")

    print("="*80)
    print("INTEGRATION WITH YOUR WORKFLOW:")
    print("="*80)
    print("""
STEP 1: Set up alerts (one-time)
  - Run this scanner every minute during market hours (9:15 AM - 3:30 PM)
  - Get alerts via Telegram/WhatsApp when score >= 75

STEP 2: When alert fires
  - Check TradingView for chart confirmation
  - Verify the signals match what you see
  - Enter trade with 1.5x size

STEP 3: Track performance
  - Log every trade in your Excel tracker
  - Review weekly to refine the scoring

STEP 4: Iterate
  - As you gather more data, update the scoring weights
  - Your edge compounds over time!

Want me to build the automated version that:
1. Fetches live data from Kite API every minute
2. Sends you Telegram/WhatsApp alerts
3. Auto-calculates exact strike and quantity?
    """)


if __name__ == "__main__":
    example_usage()
