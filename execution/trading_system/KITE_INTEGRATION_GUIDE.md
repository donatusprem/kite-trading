# KITE MCP INTEGRATION GUIDE

## 🎯 **WHAT THIS SOLVES**

**Problem**: Trading system needs live market data from Kite to:
- Scan stocks in real-time
- Get historical price data for technical analysis
- Place/manage orders automatically

**Solution**: Integrate Kite MCP Server for seamless API access

---

## 🏗️ **ARCHITECTURE**

```
Your Trading System              Kite MCP Server              Kite Connect API
──────────────────              ───────────────              ────────────────

market_scanner.py
     │
     ├──▶ Get current prices ─────▶ get_ltp() ───────────▶  Kite API
     ├──▶ Get historical data ─────▶ get_historical_data()
     └──▶ Search instruments ──────▶ search_instruments()

exit_manager.py
     │
     ├──▶ Get positions ───────────▶ get_positions()
     ├──▶ Place orders ────────────▶ place_order()
     └──▶ Cancel orders ───────────▶ cancel_order()

                          [Daily OAuth Authentication]
                                    │
                                    ▼
                              You click link
                              once per day
```

---

## 📦 **TWO OPTIONS FOR SETUP**

### **Option 1: Use Hosted Version** (Easiest - Read-Only)

**Pros**: No setup, works immediately
**Cons**: Read-only (no order placement), requires trust

Already available through MCP tools you see in Cowork!

### **Option 2: Self-Host** (Recommended - Full Access)

**Pros**: Full API access including orders, total control
**Cons**: Requires Go installation and daily authentication

---

## 🚀 **OPTION 2: SELF-HOSTED SETUP** (Recommended)

### **Step 1: Get Kite Connect API Credentials**

1. Go to https://developers.kite.trade/
2. Create a new app
3. Note your:
   - **API Key**
   - **API Secret**
   - **Redirect URL** (use `http://127.0.0.1:8080/callback`)

### **Step 2: Build Kite MCP Server**

```bash
# Navigate to cloned repo
cd /sessions/wizardly-confident-hopper/kite-mcp-server

# Create .env file
cat > .env << EOF
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
APP_MODE=http
APP_PORT=8080
APP_HOST=localhost
EOF

# Install Go (if not installed)
# On Mac: brew install go
# On Ubuntu: sudo apt install golang-go

# Build the server
go build -o kite-mcp-server

# Run it
./kite-mcp-server
```

Server will start at `http://localhost:8080/`

### **Step 3: Daily Authentication Flow**

**Every morning before market opens:**

1. **Start MCP server** (if not running)
```bash
cd /sessions/wizardly-confident-hopper/kite-mcp-server
./kite-mcp-server
```

2. **Get login link** (through Cowork or directly):
```bash
# Option A: Ask me (Claude) to call login tool
# "Get me the Kite login link"

# Option B: Direct API call
curl http://localhost:8080/login
```

3. **Click the link** and authorize

4. **Grab access token** from redirect URL

5. **Token valid for rest of trading day**

---

## 🔧 **INTEGRATE WITH TRADING SYSTEM**

### **Update market_scanner.py**

Replace the mock data fetching with real MCP calls:

```python
import requests
import os

class KiteDataFetcher:
    """Fetches real market data via Kite MCP Server"""

    def __init__(self, mcp_url="http://localhost:8080"):
        self.mcp_url = mcp_url

    def get_instruments(self, exchange="NSE"):
        """Get instrument list"""
        response = requests.post(
            f"{self.mcp_url}/search_instruments",
            json={"query": "", "exchange": exchange}
        )
        return response.json()

    def get_historical_data(self, symbol, days=5):
        """Get historical price data"""
        response = requests.post(
            f"{self.mcp_url}/get_historical_data",
            json={
                "instrument_token": self.get_token_for_symbol(symbol),
                "interval": "hour",
                "days": days
            }
        )
        data = response.json()

        # Convert to DataFrame
        return pd.DataFrame(data['candles'], columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])

    def get_current_prices(self, symbols):
        """Get latest prices"""
        # Convert symbols to exchange:symbol format
        instruments = [f"NSE:{s}" for s in symbols]

        response = requests.post(
            f"{self.mcp_url}/get_ltp",
            json={"instruments": instruments}
        )
        return response.json()
```

### **Update exit_manager.py**

Add order execution through MCP:

```python
class KiteOrderExecutor:
    """Executes orders via Kite MCP Server"""

    def __init__(self, mcp_url="http://localhost:8080"):
        self.mcp_url = mcp_url

    def place_order(self, position):
        """Place order for position"""
        order_params = {
            "tradingsymbol": position['symbol'],
            "exchange": "NSE",
            "transaction_type": "BUY" if position['type'] == 'LONG' else "SELL",
            "quantity": position['quantity'],
            "order_type": "MARKET",  # Or LIMIT with price
            "product": "CNC",  # Or MIS for intraday
            "validity": "DAY"
        }

        response = requests.post(
            f"{self.mcp_url}/place_order",
            json=order_params
        )
        return response.json()

    def cancel_order(self, order_id):
        """Cancel an order"""
        response = requests.post(
            f"{self.mcp_url}/cancel_order",
            json={
                "variety": "regular",
                "order_id": order_id
            }
        )
        return response.json()
```

---

## 📝 **DAILY WORKFLOW WITH AUTHENTICATION**

### **Morning Routine**

```bash
# 1. Start Kite MCP Server
cd /sessions/wizardly-confident-hopper/kite-mcp-server
./kite-mcp-server &

# 2. Authenticate (get link via Cowork)
# Ask Claude: "Get me today's Kite login link"
# Click link, authorize

# 3. Start Trading System
cd "/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3"
./start_system.sh
```

### **Automated Authentication Helper**

Create a helper script that opens the browser automatically:

```bash
#!/bin/bash
# File: authenticate_kite.sh

echo "🔐 Kite Authentication Helper"
echo "==============================="

# Get login URL from MCP server
LOGIN_URL=$(curl -s http://localhost:8080/login | jq -r '.url')

echo "Opening Kite login in browser..."
echo "URL: $LOGIN_URL"

# Open in default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$LOGIN_URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$LOGIN_URL"
fi

echo ""
echo "✅ After authorizing, your session is active for the day!"
echo "   You can now run the trading system."
```

---

## 🔄 **COMPLETE INTEGRATION EXAMPLE**

Here's how to update `market_scanner.py` to use real data:

```python
#!/usr/bin/env python3
"""
Updated market_scanner.py with Kite MCP integration
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class KiteMCPClient:
    """Client for Kite MCP Server"""

    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self._check_connection()

    def _check_connection(self):
        """Verify MCP server is running and authenticated"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("MCP server not responding")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Kite MCP server not running. Start it with:\n"
                "cd /sessions/wizardly-confident-hopper/kite-mcp-server && ./kite-mcp-server"
            )

    def search_instruments(self, query="", exchange="NSE"):
        """Search for trading instruments"""
        response = requests.post(
            f"{self.base_url}/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "search_instruments",
                    "arguments": {
                        "query": query,
                        "exchange": exchange
                    }
                }
            }
        )
        return response.json()

    def get_historical_data(self, instrument_token, from_date, to_date, interval="hour"):
        """Get historical OHLC data"""
        response = requests.post(
            f"{self.base_url}/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "get_historical_data",
                    "arguments": {
                        "instrument_token": instrument_token,
                        "from_date": from_date,
                        "to_date": to_date,
                        "interval": interval
                    }
                }
            }
        )
        data = response.json()

        # Convert to DataFrame
        if 'content' in data and len(data['content']) > 0:
            candles = data['content'][0]['text']  # Parse based on actual response
            return self._parse_to_dataframe(candles)
        return pd.DataFrame()

    def get_ltp(self, symbols):
        """Get last traded prices"""
        # Format: ["NSE:SYMBOL1", "NSE:SYMBOL2"]
        instruments = [f"NSE:{s}" for s in symbols]

        response = requests.post(
            f"{self.base_url}/mcp",
            json={
                "method": "tools/call",
                "params": {
                    "name": "get_ltp",
                    "arguments": {
                        "instruments": instruments
                    }
                }
            }
        )
        return response.json()

# Update MarketScanner class to use KiteMCPClient
class MarketScanner:
    def __init__(self, config_path):
        self.analyzer = TechnicalAnalyzer(config_path)
        self.config = self.analyzer.config
        self.base_path = self.analyzer.base_path

        # Initialize Kite MCP client
        try:
            self.kite_client = KiteMCPClient()
            print("[SUCCESS] Connected to Kite MCP Server")
        except ConnectionError as e:
            print(f"[WARNING] {e}")
            self.kite_client = None

    def fetch_historical_data(self, symbol, days=5):
        """Fetch real historical data from Kite"""
        if not self.kite_client:
            print(f"[ERROR] No Kite connection for {symbol}")
            return pd.DataFrame()

        # Get instrument token
        instruments = self.kite_client.search_instruments(
            query=symbol,
            exchange="NSE"
        )

        if not instruments:
            print(f"[ERROR] Symbol {symbol} not found")
            return pd.DataFrame()

        instrument_token = instruments[0]['instrument_token']

        # Get historical data
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        df = self.kite_client.get_historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval="hour"
        )

        return df
```

---

## ✅ **VERIFICATION CHECKLIST**

Before trading session:
- [ ] Kite MCP Server running (`http://localhost:8080/`)
- [ ] Authenticated for the day (clicked auth link)
- [ ] Trading system can connect (test with health check)
- [ ] Scanner fetching real prices
- [ ] Order execution configured (if using auto-mode)

---

## 🚨 **IMPORTANT NOTES**

### **Session Management**
- **Kite sessions expire daily** at market close
- **Re-authenticate every morning** before market opens
- Token is stored in MCP server memory (not persistent)

### **Rate Limits**
- Kite has API rate limits (3 requests/second)
- Scanner respects this with 5-minute intervals
- Historical data: Max 60 days, 2000 candles per request

### **Order Execution**
- Test with **paper trading first** (manual approval mode)
- Enable auto-execution only after validation
- Always have stop losses configured

---

## 🔧 **TROUBLESHOOTING**

### **"Connection refused" error**
```bash
# Check if MCP server is running
ps aux | grep kite-mcp-server

# Start it if needed
cd /sessions/wizardly-confident-hopper/kite-mcp-server
./kite-mcp-server
```

### **"Authentication required" error**
```bash
# Get new login link
curl http://localhost:8080/login

# Or ask Claude: "Get me the Kite login link"
```

### **"Symbol not found" error**
```python
# Verify symbol format
# Correct: "RELIANCE", "ADANIGREEN", "TCS"
# Incorrect: "RELIANCE.NS", "NSE:RELIANCE"
```

---

## 📚 **ADDITIONAL RESOURCES**

- **Kite Connect Docs**: https://kite.trade/docs/connect/
- **Kite MCP Server**: https://github.com/zerodha/kite-mcp-server
- **API Rate Limits**: https://kite.trade/docs/connect/v3/exceptions/

---

**With this integration, your trading system goes from mock data to live market scanning!** 🚀

*Next: Run through the setup and test with real market data*
