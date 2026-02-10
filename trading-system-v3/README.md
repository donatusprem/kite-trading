# TRADING SYSTEM V3 - Complete Documentation

## 🎯 **WHAT THIS SOLVES**

**The Problem**: Missing 5-8% daily moves because of manual approval bottlenecks

**The Solution**: Hybrid automation that continuously scans markets, scores setups, manages entries AND exits, and learns from every trade

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Core Components**

1. **Market Scanner** (`market_scanner.py`)
   - Scans NSE/BSE every 5 minutes
   - Detects Support/Resistance levels algorithmically
   - Identifies Fair Value Gaps (price imbalances)
   - Recognizes candlestick patterns AT KEY LEVELS
   - Analyzes trend structure (higher highs/lows)
   - Scores every setup 0-100

2. **Exit Manager** (`exit_manager.py`)
   - Tracks all open positions
   - Manages stops dynamically (breakeven, trailing)
   - Monitors support/resistance invalidation
   - Handles partial exits at targets
   - Detects pattern breakdown
   - Logs all exit decisions

3. **Trading Orchestrator** (`trading_orchestrator.py`)
   - Coordinates scanner + exit manager
   - Enforces risk management rules
   - Generates alerts for approval (HYBRID MODE)
   - Executes trades (if auto-mode enabled)
   - Tracks daily limits (trades, losses, positions)
   - Maintains system state

4. **Learning Engine** (`learning_engine.py`)
   - Analyzes closed trades
   - Calculates win rates by pattern/setup
   - Tracks profit factor over time
   - Identifies improvement areas
   - Suggests scoring adjustments
   - Captures lessons learned

---

## ⚙️ **CONFIGURATION**

All settings in: `config/trading_rules.json`

### **Key Settings**

```json
{
  "mode": "hybrid",              // hybrid = alerts, auto = execute
  "auto_execute": false,         // false = require approval

  "position_limits": {
    "max_positions": 5,          // Max open at once
    "max_daily_trades": 5,       // Daily trade limit
    "position_size": 20000       // ₹20k per trade
  },

  "entry_rules": {
    "minimum_score": 75          // Only trade 75+ setups
  },

  "exit_rules": {
    "risk_reward_minimum": 2.0,  // 2:1 R:R minimum
    "partial_exit_at_target1": 0.5,  // Exit 50% at T1
    "breakeven_after_target1": true  // Move stop to B/E
  },

  "scanning": {
    "scan_interval_minutes": 5   // Scan every 5 mins
  }
}
```

---

## 🚀 **HOW TO USE**

### **1. Start the System**

```bash
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"

# Make scripts executable
chmod +x scripts/*.py

# Start the orchestrator (hybrid mode)
python3 scripts/trading_orchestrator.py
```

**What Happens**:
- Scans market every 5 minutes
- Generates alerts for 75+ score setups
- Monitors open positions continuously
- Manages exits automatically
- Logs everything to journals/

### **2. Review Entry Alerts**

When system finds opportunities, check:

```bash
cat alerts/pending_entries.json
```

You'll see:
- Symbol + Score
- Setup type (LONG/SHORT)
- Current price
- Support/Resistance levels
- Entry strategy
- Patterns detected

### **3. Execute Manual Entry (if approved)**

```bash
# Edit the position manually via Kite
# OR add to system:

python3 -c "
from scripts.exit_manager import ExitManager
from scripts.trading_orchestrator import TradingOrchestrator

manager = ExitManager('config/trading_rules.json')

position = {
    'symbol': 'ADANIGREEN',
    'type': 'LONG',
    'entry_price': 954.45,
    'quantity': 20,
    'position_size': 19089,
    'score': 82,
    'support_level': 920.35,
    'resistance_level': 1030.0
}

manager.add_position(position)
print(f'Position added: {position[\"symbol\"]}')
"
```

### **4. Monitor Positions**

System automatically:
- ✅ Moves stop to breakeven after Target 1
- ✅ Takes 50% profit at Target 1
- ✅ Trails stop as price moves favorably
- ✅ Exits on pattern invalidation
- ✅ Exits on stop loss / target 2

View positions:
```bash
python3 scripts/exit_manager.py
```

### **5. Review Performance**

```bash
# Generate weekly review
python3 scripts/learning_engine.py

# View closed trades
cat analysis/closed_trades_*.json

# View daily journal
cat journals/journal_$(date +%Y%m%d).jsonl
```

---

## 📊 **SCORING SYSTEM (0-100)**

### **How Setups Are Scored**

| Criteria | Weight | Max Points |
|----------|--------|------------|
| Support/Resistance proximity | 25% | 25 |
| Fair Value Gap presence | 20% | 20 |
| Trend alignment (strong) | 20% | 20 |
| Candlestick patterns | 15% | 15 |
| Volume confirmation | 10% | 10 |
| Risk:Reward ratio | 10% | 10 |

**Score Thresholds**:
- **90-100**: Exceptional - highest conviction
- **80-89**: Excellent - strong confluence
- **75-79**: Good - minimum threshold
- **<75**: Skip - insufficient quality

---

## 🎯 **ENTRY STRATEGY**

### **What System Looks For**

**LONG Setups**:
1. ✅ Uptrend (higher highs + higher lows)
2. ✅ Pullback to support OR Fair Value Gap
3. ✅ Bullish candle pattern AT KEY LEVEL
4. ✅ Volume confirmation
5. ✅ Risk:Reward ≥ 2:1

**SHORT Setups**:
1. ✅ Downtrend (lower highs + lower lows)
2. ✅ Pullback to resistance OR Fair Value Gap
3. ✅ Bearish candle pattern AT KEY LEVEL
4. ✅ Volume confirmation
5. ✅ Risk:Reward ≥ 2:1

**We DON'T chase gaps or breakouts** - we wait for pullbacks to structure!

---

## 🛡️ **EXIT STRATEGY**

### **Dynamic Exit Management**

**Target Structure**:
- **Target 1**: Risk × 2.0 (exit 50%)
- **Target 2**: Risk × 4.0 (exit remaining 50%)

**Stop Management**:
1. **Initial Stop**: 2% below entry OR support level (whichever tighter)
2. **After T1 Hit**: Move stop to breakeven
3. **After Breakeven**: Trail stop 2% behind price
4. **Pattern Invalidation**: Exit immediately
5. **Trend Reversal**: Exit immediately

**Maximum Hold Time**: 48 hours (prevents dead capital)

---

## 📈 **RISK MANAGEMENT**

### **Position Limits**
- Max 5 positions open simultaneously
- Max 5 trades per day
- Max 2 trades per stock per day
- ₹20,000 per position

### **Loss Limits**
- Max 2% loss per trade
- Max 5% loss per day
- 2 consecutive losses = pause new entries
- Scale down after loss, scale up after win

---

## 📝 **JOURNALING & LEARNING**

### **What Gets Logged**

**Every Scan**:
- Timestamp
- Opportunities found
- Top scores
- Symbols alerted

**Every Entry**:
- Setup details
- Technical analysis
- Score breakdown
- Entry price + levels

**Every Exit**:
- Exit reason
- P&L (% and ₹)
- Win/Loss
- Lessons captured

**Daily Analysis**:
- Win rate by pattern
- Profit factor by setup type
- Improvement suggestions
- Scoring adjustments

---

## 🧠 **LEARNING & EVOLUTION**

### **How System Improves**

1. **Pattern Performance Tracking**
   - Tracks win rate for each pattern type
   - Identifies high-probability patterns (>70% win rate)
   - Flags low-probability patterns (<40% win rate)

2. **Setup Type Optimization**
   - Analyzes LONG vs SHORT performance
   - Adjusts focus based on market conditions
   - Suggests setup type preferences

3. **Scoring Refinement**
   - Increases weight for successful criteria
   - Decreases weight for unsuccessful criteria
   - Adapts thresholds based on results

4. **Lesson Capture**
   - Logs manual observations
   - Captures market insights
   - Builds institutional knowledge

---

## 🔔 **ALERT SYSTEM**

### **You Get Alerted On**

1. **Entry Opportunities** (score ≥ 75)
2. **Exit Signals** (stop approach, targets hit)
3. **Risk Events** (pattern invalidation, limit hits)
4. **System Status** (pauses, errors)

**Alert Locations**:
- Console output (real-time)
- `alerts/pending_entries.json` (pending)
- `alerts/scan_*.json` (all opportunities)
- `journals/journal_*.jsonl` (complete log)

---

## 📁 **FOLDER STRUCTURE**

```
trading-system-v3/
├── config/
│   └── trading_rules.json        # All system settings
├── scripts/
│   ├── market_scanner.py         # Real-time scanner
│   ├── exit_manager.py           # Exit orchestration
│   ├── trading_orchestrator.py   # Main system
│   └── learning_engine.py        # Performance analysis
├── journals/
│   └── journal_YYYYMMDD.jsonl    # Daily logs
├── alerts/
│   ├── pending_entries.json      # Awaiting approval
│   └── scan_*.json               # All scans
├── analysis/
│   ├── closed_trades_*.json      # Completed trades
│   └── review_*.json             # Performance reviews
├── data/
│   └── open_positions.json       # Active trades
├── models/
│   └── learned_patterns.json     # Accumulated knowledge
└── README.md                     # This file
```

---

## 🎮 **OPERATING MODES**

### **1. Hybrid Mode (RECOMMENDED)**

```json
{
  "mode": "hybrid",
  "auto_execute": false
}
```

**Flow**:
1. System scans → finds setup
2. Generates alert → you review
3. You approve → manually enter via Kite
4. You add position to exit manager
5. System manages exit automatically

**Pros**: Full control, learn from every decision
**Best For**: Building confidence, learning setups

### **2. Auto Mode (ADVANCED)**

```json
{
  "mode": "hybrid",
  "auto_execute": true
}
```

**Flow**:
1. System scans → finds setup
2. Evaluates criteria → executes if approved
3. Manages entry via Kite API
4. Manages exit automatically
5. Logs everything

**Pros**: Zero manual bottleneck, catch every move
**Best For**: After validating strategy, high confidence

---

## 🔧 **CUSTOMIZATION**

### **Adjust Scan Frequency**

```json
{
  "scanning": {
    "scan_interval_minutes": 5  // Change to 1, 3, 10, etc.
  }
}
```

### **Change Minimum Score**

```json
{
  "entry_rules": {
    "minimum_score": 75  // Raise to 80 for higher quality
  }
}
```

### **Modify Risk:Reward**

```json
{
  "exit_rules": {
    "risk_reward_minimum": 2.0  // Change to 1.5, 2.5, 3.0
  }
}
```

### **Adjust Scoring Weights**

```json
{
  "technical_criteria": {
    "support_resistance_weight": 25,  // Increase for S/R focus
    "fair_value_gap_weight": 20,      // Adjust FVG importance
    "trend_alignment_weight": 20,     // Modify trend weight
    ...
  }
}
```

---

## 🚨 **TROUBLESHOOTING**

### **No Opportunities Found**

- Lower minimum score temporarily
- Expand volatility range in config
- Check if market is open
- Verify scan is running

### **System Paused**

- Check consecutive losses (resets daily)
- Verify daily P&L limit not hit
- Confirm max positions not reached

### **Exit Not Triggering**

- Verify position added to exit manager
- Check position file: `data/open_positions.json`
- Ensure orchestrator is running
- Review exit_reasons in position

---

## 📚 **QUICK COMMANDS**

```bash
# Start system
python3 scripts/trading_orchestrator.py

# Check positions
python3 scripts/exit_manager.py

# Generate performance review
python3 scripts/learning_engine.py

# View today's journal
tail -f journals/journal_$(date +%Y%m%d).jsonl

# View pending alerts
cat alerts/pending_entries.json | jq '.'

# Check system config
cat config/trading_rules.json | jq '.'
```

---

## 🎓 **PHILOSOPHY**

### **Pure Mathematical Genius Through**:
1. **Rigorous pattern recognition** (algorithmic)
2. **Statistical edge identification** (data-driven)
3. **Adaptive learning** (evolving intelligence)
4. **Disciplined risk management** (emotional neutrality)

### **We Learn By DOING**:
- Every trade is data
- Every loss is a lesson
- Speed + iteration = mastery
- Build → Test → Learn → Improve → Repeat

---

## 🎯 **SUCCESS METRICS**

**Weekly Targets**:
- ✅ 1-2 quality setups captured per day
- ✅ Win rate >60%
- ✅ Profit factor >2.0
- ✅ Average gain 5-8% per winner
- ✅ Zero overtrading violations
- ✅ Complete journal of decisions

**System Validates Strategy When**:
- Consistent 75+ scores produce wins
- Patterns show >60% success rates
- Exit management preserves capital
- Learning engine shows improvement trends

---

## 🔥 **NEXT LEVEL UPGRADES**

### **Phase 2 Enhancements**:
1. **Live Kite API Integration** (real-time execution)
2. **Multi-Timeframe Analysis** (5min + 15min + 1hr)
3. **Forex Market Expansion** (24/7 volatility)
4. **Machine Learning Scoring** (neural network patterns)
5. **Telegram Bot Alerts** (mobile notifications)
6. **Backtesting Engine** (historical validation)

---

## 💡 **REMEMBER**

> **"We don't predict the future. We identify structure, wait for pullbacks, and execute with discipline."**

This system doesn't rely on guessing direction. It:
- Finds where price SHOULD react (S/R, FVG)
- Waits for confirmation (patterns, volume)
- Enters with clear invalidation (stops)
- Exits with predetermined targets (R:R)

**Your edge = Structure + Patience + Execution**

---

**Built for iterative improvisors who learn fast and build systematically** 🚀

*Last Updated: February 5, 2026*
