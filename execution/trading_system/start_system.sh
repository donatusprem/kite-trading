#!/bin/bash

# TRADING SYSTEM V3 - QUICK START
# Run this script to start the complete trading system

echo ""
echo "======================================================================"
echo "  TRADING SYSTEM V3 - STARTING UP"
echo "======================================================================"
echo ""

# Navigate to system directory
cd "$(dirname "$0")"

# Install dependencies if needed
echo "[1/4] Checking dependencies..."
pip install requests pandas numpy ta --break-system-packages --quiet 2>&1 > /dev/null
echo "     ✅ Dependencies ready"

# Make scripts executable
echo "[2/4] Setting up scripts..."
chmod +x scripts/*.py
echo "     ✅ Scripts ready"

# Create necessary folders if missing
echo "[3/4] Verifying folder structure..."
mkdir -p journals alerts analysis data models exits config
echo "     ✅ Folders ready"

# Display configuration
echo "[4/4] Loading configuration..."
echo ""
cat config/trading_rules.json | python3 -m json.tool | head -20
echo ""
echo "     ✅ Configuration loaded"
echo ""
echo "======================================================================"
echo "  SYSTEM READY"
echo "======================================================================"
echo ""
echo "Choose your mode:"
echo ""
echo "  [1] Start Full System (Scanner + Exit Manager + Orchestrator)"
echo "  [2] Start Scanner Only"
echo "  [3] View Open Positions"
echo "  [4] Generate Performance Review"
echo "  [5] View Configuration"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
  1)
    echo ""
    echo "Starting full trading system..."
    echo "Press Ctrl+C to stop"
    echo ""
    sleep 2
    python3 scripts/trading_orchestrator.py
    ;;
  2)
    echo ""
    echo "Starting market scanner..."
    echo "Press Ctrl+C to stop"
    echo ""
    sleep 2
    python3 scripts/market_scanner.py
    ;;
  3)
    echo ""
    echo "======================================================================"
    echo "  OPEN POSITIONS"
    echo "======================================================================"
    echo ""
    python3 scripts/exit_manager.py
    ;;
  4)
    echo ""
    echo "======================================================================"
    echo "  PERFORMANCE REVIEW"
    echo "======================================================================"
    echo ""
    python3 scripts/learning_engine.py
    ;;
  5)
    echo ""
    echo "======================================================================"
    echo "  CURRENT CONFIGURATION"
    echo "======================================================================"
    echo ""
    cat config/trading_rules.json | python3 -m json.tool
    echo ""
    ;;
  *)
    echo ""
    echo "Invalid choice. Exiting."
    echo ""
    ;;
esac

echo ""
echo "======================================================================"
echo ""
