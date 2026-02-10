# Run Trading System

## Goal
Start the AI Trading System components: Backend API, Live Sync, and Frontend Dashboard.

## Prerequisites
- Python 3.10+
- Node.js 18+
- Active Internet Connection (for Kite API)

## Layer 3: Execution Components

### 1. Start Backend API
This serves the data to the dashboard.
```bash
# Run from project root
python3 execution/trading_system/dashboard_api.py
```
*Runs on http://localhost:8000*

### 2. Start Live Data Sync
This fetches data from Kite (or generates mock data) and writes to `_tmp/live_cache.json`.
```bash
# Run from project root (in a new terminal)
python3 execution/trading_system/scripts/live_sync.py
```

### 3. Start Frontend Dashboard
The user interface.
```bash
# Run from project root (in a new terminal)
cd dashboard
npm run dev
```
*Accessible at http://localhost:3000*

## Alternative: Interactive Menu
You can use the interactive shell script to run specific subsystems (Scanner, Orchestrator), but this DOES NOT start the Dashboard API.
```bash
# Run from project root
./execution/trading_system/start_system.sh
```

## Logs & Data
- **Live Cache**: stored in `_tmp/live_cache.json`
- **Alerts**: stored in `execution/trading_system/alerts/`
- **Journals**: stored in `execution/trading_system/journals/`
