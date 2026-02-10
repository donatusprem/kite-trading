# TRADING SYSTEM V3 - QUICK START GUIDE

## 🚀 **INSTANT LAUNCH**

```bash
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"
./start_system.sh
```

Choose option **[1]** to start the full system.

---

## ⚡ **WHAT YOU JUST BUILT**

### **The Complete Solution to Your Entry Timing Problem**

#### **Before** ❌
- Manual approval bottleneck
- Missing 5-8% moves daily
- No exit management
- No journaling or learning
- Reactive watchlist checking

#### **After** ✅
- **Automated scanning every 5 minutes**
- **Instant alerts on 75+ score setups**
- **Dynamic exit management (stops, targets, trails)**
- **Complete journaling of every decision**
- **Learning engine that improves over time**

---

## 🎯 **HOW IT WORKS - SIMPLE VERSION**

### **HYBRID MODE** (Default - Recommended)

```
1. System scans NSE/BSE every 5 minutes
   ↓
2. Finds stocks with technical structure
   ↓
3. Scores them 0-100 based on:
   • Support/Resistance proximity
   • Fair Value Gaps
   • Trend alignment
   • Candlestick patterns
   • Volume confirmation
   ↓
4. If score ≥ 75 → GENERATES ALERT 🔔
   ↓
5. YOU review alert and decide
   ↓
6. If you enter → add position to exit manager
   ↓
7. System manages exit automatically:
   • Moves stop to breakeven
   • Takes 50% profit at Target 1
   • Trails stop on remaining 50%
   • Exits on pattern invalidation
   ↓
8. Logs everything + learns from results
```

---

## 📍 **YOUR EXACT WORKFLOW**

### **Morning Routine** (Before Market Opens)

```bash
# 1. Start the system
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"
./start_system.sh

# Choose option 1 (Full System)
```

### **During Trading Hours**

**When you see alert** 🔔:
```bash
# Check pending alerts
cat alerts/pending_entries.json | jq .
```

**You'll see something like**:
```json
{
  "symbol": "ADANIGREEN",
  "score": 82,
  "setup_type": "LONG",
  "current_price": 954.45,
  "entry_strategy": "Wait for pullback to support/FVG, enter on bullish confirmation",
  "support": [920.35, 905.00],
  "resistance": [1030.0, 1070.0],
  "patterns": ["hammer", "bullish_engulfing"]
}
```

**If you approve** ✅:
1. Enter trade manually via Kite
2. Add position to exit manager (see below)

**Adding Position to Exit Manager**:
```python
# Quick command
python3 -c "
from scripts.exit_manager import ExitManager

manager = ExitManager('config/trading_rules.json')

position = {
    'symbol': 'ADANIGREEN',      # Stock symbol
    'type': 'LONG',               # LONG or SHORT
    'entry_price': 954.45,        # Your entry price
    'quantity': 20,               # Shares bought
    'position_size': 19089,       # Total invested
    'score': 82,                  # From alert
    'support_level': 920.35,      # From alert
    'resistance_level': 1030.0    # From alert
}

manager.add_position(position)
print('✅ Position added - system now managing exits')
"
```

**System automatically**:
- Calculates stop loss (at support or 2% below)
- Calculates Target 1 (2:1 R:R)
- Calculates Target 2 (4:1 R:R)
- Monitors price continuously
- Moves stop to breakeven after T1
- Trails stop after breakeven
- Exits on invalidation

### **Checking Positions**

```bash
# View all open positions
python3 scripts/exit_manager.py
```

**Output**:
```
Symbol: ADANIGREEN
Type: LONG
Entry: ₹954.45
Current: ₹985.20
Stop: ₹920.35
Target1: ₹1023.00
Target2: ₹1091.55
P&L: 3.22%
Exit Signals: None
```

### **End of Day**

```bash
# Generate performance review
python3 scripts/learning_engine.py
```

**Shows you**:
- Win rate
- Profit factor
- Which patterns work best
- Areas to improve
- Scoring adjustments suggested

---

## 🎮 **CHEAT SHEET - COMMON COMMANDS**

```bash
# Quick navigation
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"

# Start system
./start_system.sh

# View today's alerts
cat alerts/pending_entries.json | jq .

# View latest scan results
ls -lt alerts/scan_*.json | head -1 | xargs cat | jq .

# Check open positions
python3 scripts/exit_manager.py

# View today's journal
tail -f journals/journal_$(date +%Y%m%d).jsonl

# Performance review
python3 scripts/learning_engine.py

# View config
cat config/trading_rules.json | jq .
```

---

## ⚙️ **ESSENTIAL SETTINGS**

**File**: `config/trading_rules.json`

### **To Make System More/Less Aggressive**

```json
{
  "entry_rules": {
    "minimum_score": 75  // RAISE to 80 for fewer, higher quality
                        // LOWER to 70 for more opportunities
  }
}
```

### **To Change Position Size**

```json
{
  "position_limits": {
    "position_size": 20000  // Your ₹ per trade
  }
}
```

### **To Change Scan Frequency**

```json
{
  "scanning": {
    "scan_interval_minutes": 5  // 1=very active, 10=relaxed
  }
}
```

### **To Enable Auto-Execute** (Advanced)

```json
{
  "auto_execute": true  // System enters trades automatically
}
```
⚠️ Only enable after validating strategy in hybrid mode!

---

## 🔥 **PRO TIPS**

### **First Week** (Learning Phase)
1. Keep `minimum_score` at **75**
2. Only take **1-2 trades per day**
3. Review **every alert** even if you don't trade
4. Log your manual observations in journals
5. Run performance review **every 3 days**

### **After Validation** (Scaling Phase)
1. Increase to **3-5 trades per day** if win rate >60%
2. Consider lowering score to **72** for more opportunities
3. Enable partial auto-execution for high-score setups (85+)
4. Add more capital per position if profit factor >2.0

### **Continuous Improvement**
1. Check learning engine **weekly**
2. Adjust pattern weights based on **your results**
3. Capture lessons after **every loss**
4. Refine support/resistance detection based on **what works**

---

## 🚨 **IF SOMETHING GOES WRONG**

### **System Not Finding Opportunities**

**Check**:
- Is market open?
- Is score threshold too high? (try 70)
- Is scan running? (should see output every 5 mins)

**Fix**:
```bash
# Lower threshold temporarily
# Edit config, change minimum_score to 70
nano config/trading_rules.json

# Restart system
./start_system.sh
```

### **Exit Not Triggering**

**Check**:
- Is position in exit manager?
```bash
cat data/open_positions.json | jq .
```

**Fix**:
```bash
# Add position manually (see "Adding Position" above)
# Or check if exit reasons are building up
python3 scripts/exit_manager.py
```

### **System Paused**

**Check**:
- Consecutive losses? (resets daily)
- Daily P&L limit hit? (resets daily)
- Max positions reached?

**Fix**:
- Wait for next trading day
- OR manually reset in config
- OR close some positions

---

## 📚 **FOLDER MAP - WHERE EVERYTHING LIVES**

```
trading-system-v3/
│
├── 📂 config/
│   └── trading_rules.json        ← ALL YOUR SETTINGS
│
├── 📂 scripts/
│   ├── market_scanner.py         ← Finds opportunities
│   ├── exit_manager.py           ← Manages exits
│   ├── trading_orchestrator.py  ← Main system brain
│   └── learning_engine.py        ← Performance analysis
│
├── 📂 alerts/
│   ├── pending_entries.json      ← REVIEW THESE for trades
│   └── scan_*.json               ← All opportunities found
│
├── 📂 journals/
│   └── journal_YYYYMMDD.jsonl    ← Complete log of everything
│
├── 📂 analysis/
│   ├── closed_trades_*.json      ← Your trade history
│   └── review_*.json             ← Performance reports
│
├── 📂 data/
│   └── open_positions.json       ← Currently active trades
│
└── 📂 models/
    └── learned_patterns.json     ← System's knowledge base
```

---

## 🎯 **SUCCESS CHECKLIST**

### **Week 1 Goals**
- [ ] System runs without errors
- [ ] Receiving 3-5 alerts per day
- [ ] Taken 1-2 high-quality trades
- [ ] Exit manager working correctly
- [ ] Journal logging everything

### **Week 2 Goals**
- [ ] Win rate >55%
- [ ] Profit factor >1.5
- [ ] Identified best patterns
- [ ] Adjusted scoring weights
- [ ] Comfortable with workflow

### **Week 3+ Goals**
- [ ] Win rate >60%
- [ ] Profit factor >2.0
- [ ] System proving edge
- [ ] Considering auto-execution
- [ ] Scaling position sizes

---

## 💡 **REMEMBER**

> **"This system doesn't predict. It identifies structure, waits for pullbacks, and executes with discipline."**

### **Your Advantage**:
1. **Continuous monitoring** (never miss moves)
2. **Objective scoring** (no emotion)
3. **Systematic exits** (preserve capital)
4. **Learning loop** (constant improvement)

### **Your Responsibility**:
1. **Review alerts promptly**
2. **Follow the rules** (don't override system)
3. **Add positions to exit manager** (critical!)
4. **Study the results** (learn from data)

---

## 📞 **QUICK HELP**

**Need the full documentation?**
```bash
cat README.md
```

**System not starting?**
```bash
# Install dependencies manually
pip install requests pandas numpy ta --break-system-packages

# Try running directly
python3 scripts/trading_orchestrator.py
```

**Want to test without real trades?**
- Keep `auto_execute: false` in config
- Review alerts but don't enter trades
- System will still scan and alert
- Perfect for paper trading

---

**You're ready to trade with structure, discipline, and intelligence** 🚀

*Built: February 5, 2026 | Version: 3.0*
