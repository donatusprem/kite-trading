# Systematic Nifty Conviction Monitor — SOP

## What This Does

Runs a continuous conviction-scoring loop against Nifty using the `nifty_conviction_engine`.
- **Pre-market** (before 9:15 AM): No-options mode (technical + candlestick + price action only)
- **Market hours** (9:15 AM – 3:30 PM): Full mode (adds options chain — PCR, OI walls, Max Pain)
- **Alert trigger**: When |conviction_score| ≥ 5 (HIGH conviction threshold)

---

## Prerequisites

1. Ajay logs into Kite on Mac every morning — this writes `execution/kite_token.json`
2. Token is valid for the day (refreshed daily via `execution/authenticate_kite.py`)
3. Dependencies installed: `kiteconnect`, `pandas`, `pytz`, `numpy`, `ta`

---

## How to Run

```bash
# Standard daily start (before market opens):
python execution/run_monitor.py --loop --market-hours-only --no-options

# Full mode (during market hours, options included):
python execution/run_monitor.py --loop --market-hours-only

# One-shot analysis (no loop):
python execution/run_monitor.py

# Custom scan interval (default is 5 min):
python execution/run_monitor.py --loop --market-hours-only --interval 3
```

---

## Script Behavior

### Flags

| Flag | Behavior |
|------|----------|
| `--loop` | Keeps scanning every N minutes (default: 5) |
| `--market-hours-only` | Runs a one-shot pre-market scan at startup, then waits for 9:15 AM to loop; stops at 3:30 PM |
| `--no-options` | Starts in no-options mode (technical/candle/PA only); auto-upgrades to full mode at 9:15 AM |
| `--interval N` | Overrides the scan interval (minutes) |

### Timeline

```
Before 9:15 AM:
  → Run one pre-market conviction scan (no options)
  → Print report
  → Sleep until 9:15 AM

9:15 AM:
  → Auto-switch to FULL mode (options chain enabled)
  → Scan every 5 minutes

Every scan:
  → Fetch Nifty candles (5min / 15min / 60min / daily)
  → Fetch options chain (nearest weekly expiry, ATM ± 500)
  → Run ConvictionScorer
  → If |score| ≥ 5 → print ALERT + full report
  → Else → print brief one-liner

3:30 PM:
  → Stop (market closed)
```

---

## Alert Threshold Rules

From `nifty_conviction_engine/INSTRUCTIONS.md` (Ajay's trading rules):

| Score | Level | Action |
|-------|-------|--------|
| ≥ 5 or ≤ -5 | VERY_HIGH | **ALERT — Consider trading** |
| ≥ 3 or ≤ -3 | HIGH | Monitor closely |
| ≥ 2 or ≤ -2 | MODERATE | Watch, no action |
| < 2 | LOW/NEUTRAL | Sit on hands |

**Rule**: Only trade on HIGH (5+) or VERY_HIGH (7+) conviction. No exceptions.

---

## Output Format

```
🚨 ALERT — NIFTY CONVICTION REPORT [FULL]
═══════════════════════════════════════════════════
⏰  Time:       2026-03-05 10:23:00 IST
💹  Spot:       22,450.00
📊  Conviction: +6.20 / 10  [VERY_HIGH]
📈  Direction:  STRONG_BULLISH
🔥  Action:     BUY_CE
    Strike:     NIFTY 22450 CE
    SL:         Nifty 22200
    Target:     Nifty 22800
    R/R:        1:1.6
    Confidence: 62%

📐  Key Levels:
    Support:    22200
    Resistance: 22800
    VWAP:       22380
    Max Pain:   22400

📊  Layer Scores:
    Technical:    +3.10
    Candlestick:  +1.80
    Options:      +2.40  PCR=1.12
    Price Action: +2.20

⏰  Timeframes:
    5min  : BULLISH           (+1.80)
    15min : STRONG_BULLISH    (+3.40)
    60min : STRONG_BULLISH    (+4.10)
    daily : BULLISH           (+2.60)

⚠️  Risk Factors:
    - RSI overbought at 76.2 on 15min — reversal risk
═══════════════════════════════════════════════════
```

---

## Kite Token

The monitor reads from `execution/kite_token.json`:
```json
{
  "api_key": "...",
  "access_token": "..."
}
```

If missing or expired → error at startup. Ajay must re-authenticate.

---

## Instrument Token

Nifty 50 spot instrument token: `256265` (Zerodha standard, stable).
If this ever changes, update `NIFTY_INSTRUMENT_TOKEN` constant in `execution/run_monitor.py`.

---

## Known Issues & Edge Cases

- **Pre-market historical data**: Kite returns candles up to the previous day's close. This is expected.
- **NFO instrument dump**: Cached daily in `.tmp/instruments_nfo.csv`. First run of the day fetches fresh.
- **Options chain missing**: If no options data returned (e.g., expiry day), monitor falls back to no-options mode automatically.
- **Token expired mid-session**: Kite tokens expire daily. If error mid-day, Ajay needs to re-login.
- **ADX < 20**: Engine will warn about choppy market — conviction scores will naturally be low.

---

## Execution Script

`execution/run_monitor.py`

---

*Last Updated: 2026-03-05*
