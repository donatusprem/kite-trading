# Nifty Direction Conviction Engine — Daily Usage Guide

## What This System Does

A multi-layer technical analysis system that produces a high-conviction directional call for Nifty, designed for **intraday ATM options trading**. The goal: buy ATM options that move ITM for profit.

**4 Analysis Layers:**
- **Layer 1 — Technical Analysis**: EMA (9/21/50), RSI, MACD, ADX, Supertrend, VWAP, Bollinger, ATR, Stochastic, OBV
- **Layer 2 — Candlestick Patterns**: 15 patterns including Engulfing, Hammer, Doji, Morning/Evening Star, Three White Soldiers/Black Crows
- **Layer 3 — Options Intelligence**: PCR ratio, Max Pain, OI walls (support/resistance from option chain), OI buildup analysis
- **Layer 4 — Price Action**: Support/Resistance levels, trend structure (HH/HL/LH/LL), breakouts, volume profile, divergence, pivot points

**Multi-Timeframe Analysis**: 5min (15%), 15min (30%), 60min (35%), Daily (20%) — weighted combination with alignment bonus.

**Output**: Conviction score from -10 to +10 with clear BUY CE / BUY PE / NO TRADE recommendation.

---

## How to Use (Step-by-Step for Claude)

When Ajay asks for the day's Nifty direction analysis, follow these steps:

### Step 1: Fetch Nifty Candle Data from Kite

```
1. search_instruments(query="NIFTY 50") → get instrument_token for NSE:NIFTY 50
2. Fetch candles:
   - 5min:  get_historical_data(token, "5minute",  from=2 days ago, to=now)
   - 15min: get_historical_data(token, "15minute", from=5 days ago, to=now)
   - 60min: get_historical_data(token, "60minute", from=20 days ago, to=now)
   - Daily:  get_historical_data(token, "day",      from=60 days ago, to=now)
3. get_ltp(instruments=["NSE:NIFTY 50"]) → current spot price
```

### Step 2: Fetch Options Chain Data from Kite

```
1. search_instruments(query="NIFTY") → filter for NFO options with nearest weekly expiry
2. ATM strike = round(spot / 50) * 50
3. Get quotes for ATM ± 500 points (10 CE + 10 PE strikes):
   get_quotes(instruments=["NFO:NIFTY{expiry}{strike}CE", ...])
4. Extract: OI, volume, LTP, bid, ask from each quote
5. For change_oi: compare with previous day's OI if available (else use 0)
```

### Step 3: Run the Conviction Engine

```python
import sys
sys.path.insert(0, '/path/to/AI Trading/nifty_conviction_engine')

# Must use package import
from nifty_conviction_engine.conviction_scorer import ConvictionScorer

# Format candles as: [{date, open, high, low, close, volume}, ...]
# Format options as: [{strike, type:"CE"/"PE", oi, volume, ltp, bid, ask, change_oi}, ...]

scorer = ConvictionScorer(
    candles_5min=candles_5min,
    candles_15min=candles_15min,
    candles_60min=candles_60min,
    candles_daily=candles_daily,
    spot_price=current_ltp,
    options_data=options_chain_data  # can be None if unavailable
)

result = scorer.compute_final_conviction()
```

### Step 4: Present Results to Ajay

Format like this:

```
🎯 NIFTY CONVICTION REPORT — [Date] [Time]
═══════════════════════════════════════════

📊 CONVICTION: [X.X] / 10 ([LEVEL])
📈 DIRECTION:  [STRONG_BULLISH / BULLISH / NEUTRAL / BEARISH / STRONG_BEARISH]

🔥 RECOMMENDATION: [BUY CE / BUY PE / NO TRADE]
   Strike: NIFTY [XXXXX] [CE/PE] (ATM)
   Confidence: [XX]%

📐 KEY LEVELS:
   Support:    [XXXXX]
   Resistance: [XXXXX]
   VWAP:       [XXXXX]
   Pivot:      [XXXXX]
   Max Pain:   [XXXXX]

💰 TRADE PLAN:
   Entry: Near current levels
   Stop Loss: Nifty [XXXXX]
   Target: Nifty [XXXXX]
   Risk/Reward: 1:[X.X]

📊 LAYER SCORES:
   Technical:    [±X.X] / 5
   Candlestick:  [±X.X] / 3
   Options:      [±X.X] / 3
   Price Action: [±X.X] / 2

⏰ TIMEFRAMES:
   5min:  [direction] ([score])
   15min: [direction] ([score])
   60min: [direction] ([score])
   Daily: [direction] ([score])

⚠️ RISK FACTORS:
   [list any warnings]
```

### Step 5: Discuss with Ajay

- Does conviction meet threshold? (Trade only on HIGH 5+ or VERY_HIGH 7+)
- Which strike to pick
- Entry timing (wait for VWAP pullback? market order?)
- Exit plan (target hit, or time-based by 2:30 PM?)

---

## Trading Rules (Ajay's Preferences)

1. **Trade ONLY on HIGH (5+) or VERY_HIGH (7+) conviction** — NO exceptions
2. **Buy ATM options** targeting ITM moves
3. **Mostly intraday** — exit same day by 3:00 PM unless swing (1-2 days max)
4. **Stop loss is MANDATORY** — use engine's SL level, cut losses fast
5. **Max 1-2 trades per day** — avoid overtrading
6. **NEUTRAL or LOW score = NO TRADE** — sit on hands, capital preservation
7. **Re-run analysis** if market moves 100+ points from initial reading
8. **Best trading window**: 10:15 AM – 2:30 PM IST (avoid first 15 min)

---

## Quick Commands

| Command | What It Does |
|---------|-------------|
| "Morning analysis" | Full conviction report with all layers |
| "What's the setup?" | Quick score + direction + recommendation |
| "Should I buy CE or PE?" | Direction + specific option |
| "Update" | Re-run with latest data |
| "How's my trade?" | Check P&L vs target/SL |
| "Exit check" | Should I hold or book? |

---

## Module Files

| File | Purpose |
|------|---------|
| `__init__.py` | Package init |
| `technical_analysis.py` | Layer 1: 12 technical indicators + scoring |
| `candlestick_patterns.py` | Layer 2: 15 candlestick patterns + scoring |
| `options_intelligence.py` | Layer 3: PCR, Max Pain, OI analysis |
| `price_action.py` | Layer 4: S/R, trend, breakout, volume, pivots |
| `conviction_scorer.py` | Master scorer combining all layers |
| `INSTRUCTIONS.md` | This file |

---

## Important Notes

- This is a **decision support tool**, not auto-trading
- Always consider market news/global cues alongside engine output
- Global factors (US markets, FII/DII, RBI policy) can override technicals
- Engine works best in **trending markets** (ADX > 25)
- In sideways/choppy markets (ADX < 20), conviction will naturally be lower
- **Re-run if conditions change** — markets are dynamic
