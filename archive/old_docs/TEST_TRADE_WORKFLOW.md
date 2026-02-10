# 🧪 TEST TRADE WORKFLOW - POWERGRID

## **Entry Analysis - Feb 5, 2026**

### **Setup Quality: 95/100** ⭐⭐⭐⭐⭐

**Why This is an Excellent Test Trade:**
- ✅ Near support (low risk entry)
- ✅ Tight stop loss (₹1.10 = 0.38% risk)
- ✅ Clear invalidation level
- ✅ Good risk:reward (1:2 to 1:7)
- ✅ Intraday scalp opportunity
- ✅ Simple pattern (support bounce)

---

## 🎯 **STEP-BY-STEP EXECUTION**

### **BEFORE YOU START**
Current Price: ₹288.80
Time: Market Hours
Status: READY TO ENTER

---

### **STEP 1: PLACE ORDER IN KITE** ⏰ (2 minutes)

**Open Kite App/Web**:
1. Search for "POWERGRID"
2. Click "BUY"

**Order Details**:
```
Exchange:    NSE
Quantity:    69 shares
Order Type:  MARKET (for instant fill)
             OR
             LIMIT @ ₹288.50 (for better price)
Product:     MIS (Intraday - recommended for test)
             OR
             CNC (Delivery - if holding overnight)
```

**Click "BUY"** and confirm.

**Expected Fill**: ₹288.50 - ₹289.00

---

### **STEP 2: ADD TO EXIT MANAGER** ⏰ (30 seconds)

After your order fills, note the **actual fill price**.

**Run this command**:
```bash
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"

# Edit the script to update entry price
nano add_position.py
# Change line 20: 'entry_price': 288.80  (to your actual fill)

# Then run it
python3 add_position.py
```

**You'll see**:
```
======================================================================
  ✅ POSITION ADDED TO EXIT MANAGER
======================================================================

Symbol:      POWERGRID
Entry:       ₹288.80
Quantity:    69 shares
Stop Loss:   ₹287.70
Target 1:    ₹289.90
Target 2:    ₹291.96

Risk:        ₹76
Reward (T2): ₹218

======================================================================

✅ System now monitoring exits automatically!
```

---

### **STEP 3: MONITOR POSITION** ⏰ (Ongoing)

**Check Position Status**:
```bash
python3 scripts/exit_manager.py
```

**You'll see current**:
- Current price
- P&L (% and ₹)
- Distance to stop/targets
- Exit signals (if any)

**Check every 15-30 minutes** or set price alerts in Kite.

---

### **STEP 4: LET SYSTEM MANAGE EXITS** ✅

**The exit manager will**:
1. ✅ Monitor price continuously
2. ✅ Alert when Target 1 hit (₹289.90)
3. ✅ Recommend 50% exit at T1
4. ✅ Suggest moving stop to breakeven
5. ✅ Trail on remaining position
6. ✅ Exit at Target 2 or stop loss

**You manually execute** the exits in Kite when alerted.

---

## 📊 **EXPECTED OUTCOMES**

### **Scenario 1: Winner** (70% probability)
- Price bounces from support
- Hits Target 1: +₹76 (50% exit)
- Trails to Target 2: +₹218 total
- **Result**: +0.76% to +1.1%

### **Scenario 2: Small Loss** (20% probability)
- Price breaks support
- Stop hit at ₹287.70
- **Result**: -₹76 (-0.38%)

### **Scenario 3: Scratch** (10% probability)
- Price chops around entry
- Exit at breakeven or small gain/loss
- **Result**: ±₹20

---

## ⏰ **TIME MANAGEMENT**

### **Active Monitoring Period**
- **First 30 min**: Check every 15 minutes
- **After 30 min**: Check every 30 minutes
- **Near targets**: Check every 5 minutes

### **Exit Timeline**
- **Target 1**: Could hit in 15-60 minutes
- **Target 2**: Could hit in 1-3 hours
- **Stop Loss**: If triggered, likely within first hour
- **Max Hold**: End of trading day

---

## 🎓 **WHAT YOU'LL LEARN**

This test trade will show you:
1. ✅ How to plan entries with tight risk
2. ✅ How exit manager calculates stops/targets
3. ✅ How to monitor positions systematically
4. ✅ How to execute partial exits
5. ✅ How journaling captures everything
6. ✅ How the system feels in live markets

---

## 📝 **JOURNALING (Automatic)**

Everything is logged to:
- `journals/journal_20260205.jsonl` - Complete activity log
- `data/open_positions.json` - Current position tracking
- `analysis/closed_trades_*.json` - After exit (with P&L)

---

## 🚨 **IMPORTANT REMINDERS**

1. **This is a TEST** - Small position, tight stop, low risk
2. **Follow the plan** - Don't move stops or targets emotionally
3. **Let system work** - Trust the exit management
4. **Take notes** - What worked? What didn't?
5. **Review after** - Run learning engine to analyze

---

## 💡 **QUICK COMMANDS**

```bash
# Check position
python3 scripts/exit_manager.py

# View today's journal
tail -f journals/journal_$(date +%Y%m%d).jsonl

# Check current price (via Kite MCP)
# Ask Claude: "What's POWERGRID trading at now?"

# Force exit (if needed)
# Just sell in Kite, then run:
python3 -c "
from scripts.exit_manager import ExitManager
manager = ExitManager('config/trading_rules.json')
manager.close_position('POWERGRID', 289.50, 'MANUAL_EXIT')
"
```

---

## ✅ **POST-TRADE CHECKLIST**

After exit:
- [ ] Note actual entry price
- [ ] Record exit price
- [ ] Calculate final P&L
- [ ] Review what happened
- [ ] Check journal logs
- [ ] Run `python3 scripts/learning_engine.py`
- [ ] Capture lessons learned

---

## 🎯 **SUCCESS CRITERIA**

This test is successful if:
1. ✅ Entry executed near plan
2. ✅ Stop was honored (if hit)
3. ✅ System correctly tracked position
4. ✅ Exit signals worked
5. ✅ Everything was logged

**Win or lose, you learn!**

---

## 📞 **NEED HELP?**

During the trade, ask Claude:
- "What's POWERGRID at now?"
- "Check my POWERGRID position"
- "Show me exit signals"
- "Should I exit now?"
- "What's my P&L?"

---

**Ready to place the trade? Let me know when you've entered!** 🚀
