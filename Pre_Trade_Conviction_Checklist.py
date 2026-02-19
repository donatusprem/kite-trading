#!/usr/bin/env python3
"""
PRE-TRADE CONVICTION SCORING SYSTEM
Use this BEFORE entering any trade to determine position size
"""

class ConvictionScorer:
    """
    Score each trade 0-100 points
    75+ points = HIGH CONVICTION (1.5x size)
    50-74 points = MEDIUM CONVICTION (normal size)
    Below 50 = LOW CONVICTION (0.5x size or skip)
    """

    def __init__(self):
        self.score = 0
        self.reasons = []

    def check_symbol(self, symbol):
        """
        Category 1: SYMBOL EDGE (30 points max)
        Based on YOUR proven track record
        """
        # Your proven winners with 75%+ win rate
        HIGH_CONVICTION_SYMBOLS = ['SBIN', 'VEDL', 'JSWSTEEL', 'HINDALCO']

        # Symbols you've lost on
        AVOID_SYMBOLS = ['BANKNIFTY', 'MARUTI', 'M&M']

        if any(s in symbol for s in HIGH_CONVICTION_SYMBOLS):
            self.score += 30
            self.reasons.append(f"✓ Symbol is in your proven high-win list (+30)")
        elif any(s in symbol for s in AVOID_SYMBOLS):
            self.score -= 20
            self.reasons.append(f"⚠ Symbol has losing history for you (-20)")
        else:
            self.score += 10
            self.reasons.append(f"→ New symbol, proceed with caution (+10)")

        return self.score

    def check_timing(self, entry_hour, entry_minute):
        """
        Category 2: TIMING EDGE (20 points max)
        Based on YOUR winning time slots
        """
        # Your 100% win rate sessions
        BEST_SESSIONS = [(10, 12), (12, 14)]  # Morning & Midday

        # Your risky sessions
        RISKY_SESSIONS = [(9, 10), (14, 16)]  # Pre-market & Afternoon

        for start, end in BEST_SESSIONS:
            if start <= entry_hour < end:
                self.score += 20
                self.reasons.append(f"✓ Perfect timing! 10:00-14:00 is your sweet spot (+20)")
                return self.score

        for start, end in RISKY_SESSIONS:
            if start <= entry_hour < end:
                self.score += 5
                self.reasons.append(f"⚠ Risky timing. You have 50% or lower win rate in this session (+5)")
                return self.score

        self.score += 10
        self.reasons.append(f"→ Neutral timing (+10)")
        return self.score

    def check_day_of_week(self, day_name):
        """
        Category 3: DAY OF WEEK (10 points max)
        """
        BEST_DAYS = ['Monday', 'Friday']  # 100% win rate
        GOOD_DAYS = ['Tuesday']  # 66.7% win rate
        RISKY_DAYS = ['Wednesday', 'Thursday']  # 40-50% win rate

        if day_name in BEST_DAYS:
            self.score += 10
            self.reasons.append(f"✓ {day_name} is your best trading day (+10)")
        elif day_name in GOOD_DAYS:
            self.score += 6
            self.reasons.append(f"→ {day_name} is decent for you (+6)")
        else:
            self.score += 2
            self.reasons.append(f"⚠ {day_name} has mixed results (+2)")

        return self.score

    def check_option_type(self, option_type):
        """
        Category 4: CALL vs PUT (10 points max)
        """
        if option_type == 'CE':
            self.score += 10
            self.reasons.append(f"✓ Call options: 64% win rate for you (+10)")
        elif option_type == 'PE':
            self.score += 5
            self.reasons.append(f"→ Put options: 50% win rate for you (+5)")

        return self.score

    def check_market_indicators(self, volume_spike=False, breakout=False,
                                sector_momentum=False, index_support=False):
        """
        Category 5: REAL-TIME MARKET SIGNALS (30 points max)
        These you need to check manually or via API
        """
        points_earned = 0

        if volume_spike:
            points_earned += 10
            self.reasons.append(f"✓ Volume spike detected (+10)")

        if breakout:
            points_earned += 10
            self.reasons.append(f"✓ Price breakout confirmed (+10)")

        if sector_momentum:
            points_earned += 5
            self.reasons.append(f"✓ Sector showing momentum (+5)")

        if index_support:
            points_earned += 5
            self.reasons.append(f"✓ Index in your favor (+5)")

        if points_earned == 0:
            self.reasons.append(f"⚠ No strong market signals (+0)")

        self.score += points_earned
        return self.score

    def get_verdict(self):
        """Return final score and recommendation"""
        if self.score >= 75:
            return {
                'score': self.score,
                'verdict': 'HIGH CONVICTION',
                'position_size': '1.5x',
                'action': '🔥 GO BIG - This meets your proven criteria',
                'reasons': self.reasons
            }
        elif self.score >= 50:
            return {
                'score': self.score,
                'verdict': 'MEDIUM CONVICTION',
                'position_size': '1.0x',
                'action': '✓ NORMAL SIZE - Proceed with standard position',
                'reasons': self.reasons
            }
        else:
            return {
                'score': self.score,
                'verdict': 'LOW CONVICTION',
                'position_size': '0.5x or SKIP',
                'action': '⚠ REDUCE SIZE or SKIP - Not enough edge',
                'reasons': self.reasons
            }


# ==============================================================================
# EXAMPLE USAGE - TEST DIFFERENT SCENARIOS
# ==============================================================================

def test_scenario(name, symbol, hour, minute, day, option_type,
                  volume_spike=False, breakout=False, sector_momentum=False, index_support=False):
    """Test a trade scenario"""

    scorer = ConvictionScorer()

    print("\n" + "="*80)
    print(f"SCENARIO: {name}")
    print("="*80)
    print(f"\nTrade Details:")
    print(f"  Symbol: {symbol}")
    print(f"  Entry Time: {hour:02d}:{minute:02d}")
    print(f"  Day: {day}")
    print(f"  Option Type: {option_type}")
    print(f"  Volume Spike: {'YES' if volume_spike else 'NO'}")
    print(f"  Breakout: {'YES' if breakout else 'NO'}")
    print(f"  Sector Momentum: {'YES' if sector_momentum else 'NO'}")
    print(f"  Index Support: {'YES' if index_support else 'NO'}")

    # Run scoring
    scorer.check_symbol(symbol)
    scorer.check_timing(hour, minute)
    scorer.check_day_of_week(day)
    scorer.check_option_type(option_type)
    scorer.check_market_indicators(volume_spike, breakout, sector_momentum, index_support)

    result = scorer.get_verdict()

    print(f"\n{'─'*80}")
    print(f"CONVICTION SCORE: {result['score']}/100")
    print(f"VERDICT: {result['verdict']}")
    print(f"POSITION SIZE: {result['position_size']}")
    print(f"ACTION: {result['action']}")
    print(f"\nREASONING:")
    for reason in result['reasons']:
        print(f"  {reason}")


if __name__ == "__main__":
    print("="*80)
    print("PRE-TRADE CONVICTION SCORING SYSTEM")
    print("OUTSMART THE MARKET BY TRADING WHEN YOU HAVE THE EDGE")
    print("="*80)

    # Scenario 1: Perfect high-conviction setup
    test_scenario(
        name="SBIN Call at 11:00 AM on Friday with all signals",
        symbol="SBIN26FEB1160CE",
        hour=11, minute=0,
        day="Friday",
        option_type="CE",
        volume_spike=True,
        breakout=True,
        sector_momentum=True,
        index_support=True
    )

    # Scenario 2: Good symbol, wrong timing
    test_scenario(
        name="SBIN Call at 2:30 PM (afternoon - risky time)",
        symbol="SBIN26FEB1160CE",
        hour=14, minute=30,
        day="Friday",
        option_type="CE",
        volume_spike=False,
        breakout=False,
        sector_momentum=False,
        index_support=False
    )

    # Scenario 3: Weak symbol, good timing
    test_scenario(
        name="M&M Call at 10:30 AM (good time, weak symbol)",
        symbol="M&M26FEB3750CE",
        hour=10, minute=30,
        day="Monday",
        option_type="CE",
        volume_spike=True,
        breakout=True,
        sector_momentum=False,
        index_support=True
    )

    # Scenario 4: New symbol with strong signals
    test_scenario(
        name="RELIANCE Call at 11:00 AM with strong market signals",
        symbol="RELIANCE26FEB3000CE",
        hour=11, minute=0,
        day="Tuesday",
        option_type="CE",
        volume_spike=True,
        breakout=True,
        sector_momentum=True,
        index_support=True
    )

    # Scenario 5: Put option (lower win rate)
    test_scenario(
        name="NIFTY Put at 10:00 AM",
        symbol="NIFTY26FEB25500PE",
        hour=10, minute=0,
        day="Monday",
        option_type="PE",
        volume_spike=True,
        breakout=False,
        sector_momentum=False,
        index_support=False
    )

    print("\n" + "="*80)
    print("HOW TO USE THIS SYSTEM DAILY:")
    print("="*80)
    print("""
1. BEFORE entering any trade, run this checklist
2. Input your trade details (symbol, time, day, etc.)
3. Check real-time indicators:
   - Volume: Is today's volume 1.5x+ higher than average?
   - Breakout: Did price break a key level (resistance/support)?
   - Sector: Check if the sector index is up 0.5%+ today
   - Index: Is NIFTY/BANKNIFTY trending in your option's direction?

4. Get your score:
   - 75+ = USE 1.5X SIZE (High conviction)
   - 50-74 = USE NORMAL SIZE
   - <50 = USE 0.5X SIZE or SKIP

5. This system codifies YOUR proven edge
   - Not random signals from "gurus"
   - Not emotional decisions
   - Pure data from YOUR winning trades
""")

    print("\n" + "="*80)
    print("NEXT LEVEL: AUTOMATE WITH KITE API")
    print("="*80)
    print("""
We can build an automated version that:
✓ Fetches live volume data from Kite
✓ Checks sector performance automatically
✓ Sends you alerts when high-conviction setups appear
✓ Calculates position size automatically

Want me to build that next?
""")
