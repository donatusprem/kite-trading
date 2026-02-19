# Trading Analysis & Rule-Based Framework
**Ajay — Discretionary Intraday Trader | Zerodha Kite | NSE EQ + FO**
*Analysis period: Dec 2025 – Feb 2026 | Generated: Feb 16, 2026*

---

## 1. Profile Snapshot

| Metric | EQ | FO | Combined |
|---|---|---|---|
| Round trips | 51 | 10 | 61 |
| Win rate | 53% | 60% | 54% |
| Realized P&L | ₹+9,235 | ₹+20,703 | ₹+29,938 |
| Capital deposited | — | — | ₹36,700 |
| Current balance | — | — | ₹30,971 |
| Total charges | — | — | ₹1,589 |
| Active days | 32 | 6 | 34 |

---

## 2. What's Working & What's Not (10 Bullets)

**Strengths:**

1. **Metal/commodity stocks are your edge.** NATIONALUM (+₹6,331), HINDALCO (+₹4,998), VEDL (+₹3,392), COALINDIA (+₹1,289) — these four alone account for ~₹16K of your ₹29K total. You read these sectors well.

2. **Overnight FO holds generate real alpha.** 4 overnight option trades produced +₹12,376 vs 6 intraday FO trades at +₹8,327. Your best single trade (NIFTY 25500CE, +₹10,254, +50%) was a 3-day hold. Patience pays.

3. **Afternoon EQ entries outperform.** Trades entered at 13:00–15:00 show 67–75% win rates and ₹+12,446 combined P&L. Morning 09:00 entries are net negative (–₹771, 52% WR). You make better decisions after the noise settles.

4. **You cut losers in FO.** M&M 3750CE was exited same-day at –18% and BANKNIFTY 60700PE at –4%. This discipline prevented bigger damage.

5. **Account grew from ₹5K to ₹31K.** Even after ₹22.5K in withdrawals and ₹1.6K in charges, you've built capital. The trajectory is real.

**Weaknesses / Risks:**

6. **Extreme concentration in FO.** SBIN 1160CE position was ₹71,550 deployed — that's 2.3x your entire account balance at the time. One bad gap and you're wiped. This is the single biggest risk in your trading.

7. **5 auto-square-offs costing ₹413.** This means positions hit broker risk limits or you forgot to close. Each one signals either over-leveraging or poor position monitoring.

8. **4 days with negative account balance.** Max drawdown hit –₹47,209 (Feb 10). The ledger went to –₹12,276. You were technically in margin debt. This is unsustainable.

9. **Morning EQ scalps are a drag.** 49 buy trades at 09:00 hour — highest volume, but net negative. The first 30 minutes have the worst risk/reward in your data.

10. **RECLTD was your worst EQ trade (–₹2,885).** Single stock, single day. No clear edge in this name — it was a one-off punt that went wrong.

---

## 3. Rule-Based Trading Framework (v1.0)

### 3A. Instrument Selection

| Rule | Type | Rationale |
|---|---|---|
| **Trade only your proven sectors: metals, PSU banks, energy.** Specifically: NATIONALUM, HINDALCO, VEDL, COALINDIA, TATASTEEL, SBIN, NTPC, BPCL, IOC, TATAPOWER. | HARD | These 10 names generated 85% of your EQ profits. Stick to what you know. |
| **FO: Only trade NIFTY/BANKNIFTY index options OR options on your proven stocks.** | HARD | Your edge in FO came from names you understand (NIFTY, SBIN, VEDL, HINDALCO). M&M and MARUTI — names outside your circle — were both losers. |
| **Avoid new/unfamiliar names unless you've paper-tracked them for ≥5 sessions.** | SOFT | RECLTD, GODREJCP, MTNL were one-off trades with no edge. Curiosity trades bleed capital. |

### 3B. Entry Rules

| Rule | Type | Rationale |
|---|---|---|
| **No new EQ entries before 09:45.** | HARD | Your 09:00 entries are net negative (–₹771, 52% WR). Wait for the opening range to establish. |
| **Preferred entry window: 10:00–14:00.** | SOFT | Your best P&L comes from 10:00+ and 13:00+ entries. Let the market show its hand. |
| **FO entries: require a directional thesis (written in 1 sentence before entry).** | HARD | Forces you to articulate why. "NIFTY gapping up, buying 25500CE for continuation" is valid. "Just feels right" is not. |
| **Only buy options with ≥3 days to expiry (unless intraday scalp with strict SL).** | SOFT | Your overnight winners all had ≥2 weeks to expiry. Near-expiry theta decay killed the BANKNIFTY PE trade. |

### 3C. Position Sizing — THE MOST CRITICAL SECTION

| Rule | Type | Rationale |
|---|---|---|
| **Max single position: 20% of account balance.** Current balance ~₹31K → max ₹6,200 per position. | HARD | Your SBIN 1160CE was 2.3x account. A 30% adverse move would have vaporized the account. 20% cap means max loss on any one trade is ~6% of account (with a 30% SL). |
| **Max total exposure: 50% of account in open positions.** | HARD | You hit negative balance 4 times. This means total open positions never exceed ~₹15,500. |
| **FO lot size check: if 1 lot > 20% of account, skip the trade.** | HARD | Some F&O lots (SBIN at ₹71K) are simply too large for a ₹31K account. No shame in skipping. |
| **Scale up only after 2 consecutive profitable weeks.** | SOFT | Prevents revenge-sizing after a loss. You earned the right to size up — don't give it back. |

### 3D. Exit Rules

| Rule | Type | Rationale |
|---|---|---|
| **EQ intraday: exit by 15:10 unless deliberately holding overnight.** | HARD | Auto-square-offs cost ₹59–118 each and signal poor planning. Decide before 15:00: close or hold. |
| **FO stop-loss: 25% of premium paid, no exceptions.** | HARD | Your M&M loss was –18.4% — within tolerance. But without a rule, the next one could be –50%. 25% SL caps max loss at 5% of account (with 20% position sizing). |
| **FO profit target: 40–50% of premium (for overnight holds).** | SOFT | NIFTY 25500CE hit +50%, SBIN 1160CE hit +52%. Your winners cluster around 40–50% return. Take profits there. |
| **Trailing stop for FO: once +25% in profit, move SL to breakeven.** | SOFT | Protects capital on winners while letting them run. |
| **Daily loss limit: ₹1,500 (5% of account).** Stop trading for the day if hit. | HARD | Prevents tilt-trading. Your worst single day wasn't catastrophic, but without a rule it eventually will be. |
| **Weekly loss limit: ₹3,000 (10% of account).** Reduce size by 50% if hit. | HARD | Two bad days shouldn't cascade into a bad month. |

---

## 4. Daily Workflow (Using Kite MCP)

### Morning Routine (08:45–09:15)

**Goal:** Set the stage. Know what you're looking for before the market opens.

1. **Check account balance and margin** — `get_margins`. Confirm available capital.
2. **Review open positions** — `get_positions`. Any overnight holds? What's the P&L?
3. **Check watchlist quotes** — `get_ltp` for your 10 proven instruments. Note pre-market direction.
4. **Scan for gap opens** — Compare LTP to previous close (`get_ohlc`). Gaps > 1% are actionable.
5. **Write 1-sentence market bias.** Example: "Metals strong, Nifty flat, might look for HINDALCO CE if 920+ breaks."
6. **Set risk budget for the day.** E.g., "Max loss today: ₹1,500. Max positions: 2."

### Intraday (09:45–15:00)

**Goal:** Execute only high-conviction setups within your rules.

1. **Wait until 09:45** before any entries. Use 09:15–09:45 to observe opening range.
2. **Before every entry, answer 3 questions:**
   - Is this instrument on my approved list? (If no → skip)
   - Is position size ≤ 20% of account? (If no → reduce size or skip)
   - Can I write my thesis in 1 sentence? (If no → skip)
3. **After entry, immediately set stop-loss** — either in Kite or as a mental note with an alarm.
4. **Check P&L every 30 min** — `get_positions`. If daily loss limit approached, stop new entries.
5. **At 14:30, review all open positions.** Decide: close before 15:10, or hold overnight (and why).

### End-of-Day (15:15–15:30)

**Goal:** Learn from today. Update your journal.

1. **Pull today's orders** — `get_orders`. Review fills, slippage, any auto-square-offs.
2. **Calculate day's P&L.** Note: winning trades, losing trades, charges.
3. **Score yourself on rule compliance:**
   - Did I avoid 09:00–09:45 entries? ✓/✗
   - Was every position ≤ 20% of account? ✓/✗
   - Did I write a thesis before each FO entry? ✓/✗
   - Did I stay within daily loss limit? ✓/✗
4. **Log 1 lesson.** "HINDALCO CE worked because metals had momentum + I waited for 10:15 breakout."
5. **Check balance** — `get_margins`. Confirm no margin shortfall overnight.

### Weekly Review (Saturday/Sunday, 15 min)

1. Pull the week's trades and sum P&L.
2. Count rule violations. If > 3 violations, next week trade at 50% size.
3. Review your instrument list — add or remove names based on recent conviction.
4. Set next week's capital allocation.

---

## 5. Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│         AJAY'S TRADING RULES — v1.0             │
├─────────────────────────────────────────────────┤
│ INSTRUMENTS: Metals + PSU banks + energy only   │
│ NO ENTRIES before 09:45                         │
│ MAX POSITION: 20% of account (₹6,200)          │
│ MAX EXPOSURE: 50% of account (₹15,500)         │
│ FO STOP-LOSS: 25% of premium                   │
│ FO TARGET: 40-50% of premium                   │
│ DAILY LOSS LIMIT: ₹1,500 → stop trading        │
│ WEEKLY LOSS LIMIT: ₹3,000 → half size          │
│ EXIT by 15:10 or DECIDE to hold overnight       │
│ WRITE THESIS before every FO entry              │
└─────────────────────────────────────────────────┘
```

---

*This is v1.0 — designed to be iterated on. After 2 weeks of following these rules, review what works and what feels too tight or too loose. Adjust the soft rules first, keep the hard rules for at least a month.*
