# 🚀 DUAL-MODE SYSTEM - Quick Reference Card

## 📊 AT A GLANCE

```
┌─────────────────────────────────────────────────────────┐
│         MIS (INTRADAY)      vs      CNC (DELIVERY)      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Uses: ₹15k Margin              Uses: ₹10k Cash         │
│  Threshold: 85+                 Threshold: 75+          │
│  Stop: 0.5%                     Stop: 1.5%              │
│  Target: 1.0%                   Target: 2.5%            │
│  Hold: Max 3:15 PM              Hold: 1-2 days          │
│  Costs: ₹40 round-trip          Costs: ₹15.34 per sell  │
│  Risk: Higher                   Risk: Lower             │
│  History: Lost ₹870 (manual)    History: Made ₹3,028 ✅ │
│  Status: NEEDS VALIDATION       Status: PROVEN          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🎯 DECISION TREE

```
Signal Received (Score: X, Time: T, Cash: C, Margin: M)
    ↓
┌───────────────────────┐
│  Is Score < 75?       │ YES → SKIP ❌
└───────────────────────┘
    ↓ NO
┌───────────────────────┐
│  Is Time > 2:30 PM?   │ YES → ┌─────────────────┐
└───────────────────────┘       │ Has Cash (₹10k)?│
    ↓ NO                        └─────────────────┘
┌───────────────────────┐             ↓
│  Is Score ≥ 90?       │       YES → CNC ✅
└───────────────────────┘       NO  → SKIP ❌
    ↓ YES
┌─────────────────────────────────┐
│ Has Margin (₹15k)?              │ YES → MIS ✅
└─────────────────────────────────┘
    ↓ NO
┌─────────────────────────────────┐
│ Has Cash (₹10k)?                │ YES → CNC ✅
└─────────────────────────────────┘       NO  → SKIP ❌
    ↓
Score 85-89:
    Has Cash? → CNC ✅
    Has Margin? → MIS ✅
    Neither? → SKIP ❌

Score 75-84:
    Has Cash? → CNC ONLY ✅
    No Cash? → SKIP ❌
```

## ⚡ MODE SELECTION EXAMPLES

| Scenario | Score | Time | Cash | Margin | **Decision** | Why |
|----------|-------|------|------|--------|--------------|-----|
| Morning Exceptional | 95 | 10:30 | ✅ | ✅ | **MIS** | Quick profit opportunity |
| Morning Exceptional | 93 | 10:45 | ✅ | ❌ | **CNC** | No margin, use cash |
| Good Setup | 87 | 11:00 | ✅ | ✅ | **CNC** | Prefer safer delivery |
| Good Setup | 85 | 12:30 | ❌ | ✅ | **MIS** | Only margin available |
| Late Day | 88 | 14:45 | ✅ | ✅ | **CNC** | Too late for MIS |
| Marginal | 78 | 10:00 | ✅ | ✅ | **CNC** | Score too low for MIS |
| Weak Signal | 72 | 11:00 | ✅ | ✅ | **SKIP** | Below threshold |
| No Capital | 95 | 10:00 | ❌ | ❌ | **SKIP** | No funds |

## 🔧 MODE RULES COMPARISON

| Feature | MIS (Intraday) | CNC (Delivery) |
|---------|---------------|----------------|
| **Entry Window** | 9:20 AM - 2:00 PM | 9:20 AM - 3:00 PM |
| **Min Score** | 85 | 75 |
| **Position Size** | ₹15,000 max | ₹10,000 max |
| **Stop Loss** | 0.5% (₹75 on ₹15k) | 1.5% (₹150 on ₹10k) |
| **Target** | 1.0% (₹150 on ₹15k) | 2.5% (₹250 on ₹10k) |
| **R:R Ratio** | 2:1 | 1.67:1 |
| **Force Close** | 3:15 PM SHARP ⚠️ | No (can hold) |
| **Hold Time** | Max 6 hours | 1-2 days |
| **Partial Exit** | No (full exit) | No (full exit) |
| **Trailing Stop** | No | Yes (after T1) |
| **Cost/Trade** | ₹40 (₹20×2) | ₹15.34 (DP only) |
| **Max Trades/Day** | 2 | 3 |
| **Max Loss/Day** | ₹300 | ₹500 |
| **Automation** | STRICT ⚠️ | Standard |

## 💰 COST BREAKDOWN

### MIS (Intraday)
```
Buy:  ₹20 brokerage (or 0.03% if lower)
Sell: ₹20 brokerage (or 0.03% if lower)
Total: ₹40 per round-trip
Break-even: 0.27% on ₹15k position

Example on ₹15k:
₹150 target (1%) - ₹40 costs = ₹110 net
```

### CNC (Delivery)
```
Buy:  ₹0 (free!)
Sell: ₹15.34 (DP charge)
Total: ₹15.34 per round-trip
Break-even: 0.15% on ₹10k position

Example on ₹10k:
₹250 target (2.5%) - ₹15.34 costs = ₹234.66 net
```

### Cost Savings from Optimization
```
OLD System (Your History):
├── Auto square-offs: ₹354 (4 times)
├── Multiple exits: ₹348 (22 DP charges)
└── Total wasted: ₹702

NEW System:
├── Auto square-offs: ₹0 (3:15 PM force close)
├── Multiple exits: ₹0 (single exit only)
└── Savings: ₹702 → ₹0 ✅

Monthly Savings: ~₹646
Annual Savings: ~₹7,756
```

## 🎯 RISK PER TRADE

### MIS (₹15k position)
```
Risk: ₹75 (0.5% stop)
Reward: ₹150 (1% target)
R:R: 2:1
Capital at risk: 0.5% of ₹15k margin
```

### CNC (₹10k position)
```
Risk: ₹150 (1.5% stop)
Reward: ₹250 (2.5% target)
R:R: 1.67:1
Capital at risk: 1.5% of ₹10k cash
```

## 📊 PERFORMANCE TARGETS

### Minimum Viable
```
MIS: 55% win rate, 1.3 profit factor
CNC: 50% win rate, 1.2 profit factor
Status: Break-even to small profit
```

### Target Performance
```
MIS: 60% win rate, 1.5 profit factor
CNC: 55% win rate, 1.3 profit factor
Status: Consistent profitability
```

### Excellent Performance
```
MIS: 65% win rate, 2.0 profit factor
CNC: 60% win rate, 1.5 profit factor
Status: Strong edge validated
```

## ⏱️ TIMING RULES

### MIS Critical Times
```
09:15 ────────── Market Open
09:20 ────────── Entry Window Opens
    ↓
   ... Trading Window ...
    ↓
14:00 ────────── Last Entry Time
    ↓
   ... Exit Window ...
    ↓
15:15 ────────── FORCE CLOSE (NO EXCEPTIONS!)
15:20 ────────── Zerodha Auto Square-off (₹59 charge)
15:30 ────────── Market Close
```

### CNC Timing
```
09:15 ────────── Market Open
09:20 ────────── Entry Window Opens
    ↓
   ... Trading Window ...
    ↓
15:00 ────────── Last Entry Time
15:30 ────────── Market Close
    ↓
Next Day(s) ───── Can Hold Position
    ↓
Target/Stop ───── Exit When Hit
```

## 🚦 DAILY LIMITS

| Limit | MIS | CNC | Total |
|-------|-----|-----|-------|
| **Max Trades** | 2 | 3 | 4 |
| **Max Loss** | ₹300 | ₹500 | ₹800 |
| **Max Positions** | 1 | 1 | 1* |
| **Loss Streak Stop** | 2 | 2 | 2 |

*Never run MIS and CNC simultaneously with current capital

## 🔄 WORKFLOW EXAMPLE

### Morning Scenario: RELIANCE @ ₹1450, Score 88, Time 10:30 AM

```
1. SCANNER DETECTS
   └→ RELIANCE: Score 88, Pullback Long
       Price: ₹1450, Support: ₹1440, Resistance: ₹1465

2. MODE SELECTOR DECIDES
   └→ Input: Score 88, Time 10:30, Cash ₹10k, Margin ₹15k
   └→ Decision: CNC (Good setup, prefer safer delivery)
   └→ Confidence: 80%

3. ORCHESTRATOR CALCULATES
   └→ Position: 6 shares @ ₹1450 = ₹8,700
   └→ Stop: ₹1428.25 (1.5%) = Risk ₹130
   └→ Target: ₹1486.25 (2.5%) = Reward ₹217
   └→ Costs: ₹15.34 DP charge
   └→ Net Reward: ₹201.66

4. COST CHECK
   └→ Expected: ₹217 profit
   └→ Costs: ₹15.34
   └→ Net: ₹201.66 ✅ VIABLE

5. ALERT GENERATED
   └→ "CNC entry alert: RELIANCE 6 shares @ ₹1450"
   └→ Stop: ₹1428 | Target: ₹1486
   └→ Risk: ₹130 | Reward: ₹201 (net)
   └→ ⏳ AWAITING YOUR APPROVAL

6. YOU APPROVE
   └→ ✅ "Yes, take trade"

7. SYSTEM EXECUTES
   └→ BUY 6 RELIANCE @ ₹1450
   └→ Position OPEN, monitoring...

8. TARGET HIT NEXT DAY
   └→ Price reaches ₹1486
   └→ SELL 6 RELIANCE @ ₹1486
   └→ P&L: ₹217 - ₹15.34 = ₹201.66 ✅
```

## 📁 FILES YOU NEED

### To Run Backtest
```bash
demo_backtest_dual_mode.py  # ← Run this!
```

### To Understand System
```bash
DUAL_MODE_SYSTEM_GUIDE.md   # Complete guide
CORRECTED_ANALYSIS.md       # Your actual P&L
```

### Configuration Files
```bash
config/trading_rules_mis.json  # MIS rules
config/trading_rules_cnc.json  # CNC rules
```

### System Code
```bash
scripts/mode_selector.py       # Mode decision
scripts/dual_orchestrator.py   # Coordination
scripts/cost_tracker.py        # Cost monitoring
scripts/trade_logger.py        # Trade logging
```

## ⚡ QUICK COMMANDS

```bash
# Navigate
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"

# Run backtest
python3 demo_backtest_dual_mode.py

# Test mode selector
python3 scripts/mode_selector.py

# Test orchestrator
python3 scripts/dual_orchestrator.py
```

## ✅ VALIDATION CHECKLIST

Before going live:

```
MIS Mode:
[ ] Backtest shows 60%+ win rate
[ ] Profit factor > 1.5
[ ] Net P&L positive after costs
[ ] Paper traded 5 days successfully
[ ] Force close tested (3:15 PM works)

CNC Mode:
[ ] Backtest shows 55%+ win rate
[ ] Profit factor > 1.3
[ ] Net P&L positive after costs
[ ] Already proven (₹3k actual profit) ✅
[ ] Can go live after capital added

Capital:
[ ] Added ₹10,000 to Kite
[ ] Balance > ₹9,900
[ ] GOLDBEES pledged (₹15k margin available)
```

## 🎯 SUCCESS CRITERIA

### Week 1: Backtest
```
✅ MIS validated or threshold adjusted
✅ CNC validated (should match ₹3k profit history)
✅ Both show positive net P&L
```

### Week 2-3: Paper Trade (MIS only)
```
✅ 5+ MIS signals tracked
✅ Win rate matches backtest ±5%
✅ No surprises vs expectations
```

### Week 3-4: Live Small
```
✅ 3+ CNC trades successful
✅ 2+ MIS trades successful (after paper validation)
✅ Zero manual interventions
✅ System adhering to rules
```

### Month 2+: Full System
```
✅ Consistent profitability
✅ Trust in automation built
✅ Scale to full position sizes
✅ Track for further optimization
```

---

## 🚀 YOUR IMMEDIATE NEXT STEP

```bash
python3 demo_backtest_dual_mode.py
```

Then share:
1. MIS win rate & profit factor
2. CNC win rate & profit factor
3. Net P&L for each mode
4. Any validation failures

I'll help you interpret and proceed! 🎯
