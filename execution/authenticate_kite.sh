#!/bin/bash

# KITE AUTHENTICATION HELPER
# Automates daily Kite Connect authentication

echo ""
echo "========================================================================"
echo "  KITE AUTHENTICATION HELPER"
echo "========================================================================"
echo ""

MCP_SERVER_URL="http://localhost:8080"
KITE_MCP_DIR="$(cd "$(dirname "$0")/kite-mcp-server" && pwd)"
# Hardcoding path to be absolutely sure
ENV_FILE="/Users/ajaydonatusprem/Claude/AI Trading /.env"

# Load .env variables
if [ -f "$ENV_FILE" ]; then
    echo "Loading .env from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "⚠️  .env file not found at $ENV_FILE"
fi

# Function to check if MCP server is running
check_server() {
    if curl -s "$MCP_SERVER_URL/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Step 1: Check if server is running
echo "[1/4] Checking Kite MCP Server..."
if check_server; then
    echo "      ✅ Server is running"
else
    echo "      ❌ Server not running"
    echo ""
    echo "      Starting Kite MCP Server..."
    echo ""

    # Check if binary exists
    if [ ! -f "$KITE_MCP_DIR/kite-mcp-server" ]; then
        echo "      ⚠️  MCP server binary not found"
        echo ""
        echo "      Please build it first:"
        echo "      cd $KITE_MCP_DIR"
        echo "      go build -o kite-mcp-server"
        echo ""
        exit 1
    fi

    # Start server in background
    cd "$KITE_MCP_DIR" || exit 1
    ./kite-mcp-server > /tmp/kite-mcp-server.log 2>&1 &
    SERVER_PID=$!

    echo "      Started with PID: $SERVER_PID"
    echo "      Waiting for server to initialize..."
    sleep 3

    # Verify it started
    if check_server; then
        echo "      ✅ Server started successfully"
    else
        echo "      ❌ Failed to start server"
        echo ""
        echo "      Check logs: tail -f /tmp/kite-mcp-server.log"
        echo ""
        exit 1
    fi
fi

echo ""

# Step 2: Get login URL
echo "[2/4] Requesting login URL..."

LOGIN_RESPONSE=$(curl -s -X POST "$MCP_SERVER_URL/mcp" \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "login",
            "arguments": {}
        }
    }')

# Extract URL from response
if command -v jq &> /dev/null; then
    LOGIN_URL=$(echo "$LOGIN_RESPONSE" | jq -r '.result.content[0].text' 2>/dev/null)
else
    # Fallback if jq not available
    LOGIN_URL=$(echo "$LOGIN_RESPONSE" | grep -o 'https://[^"]*' | head -1)
fi

if [ -z "$LOGIN_URL" ] || [ "$LOGIN_URL" = "null" ]; then
    echo "      ❌ Failed to get login URL"
    echo ""
    echo "      Response: $LOGIN_RESPONSE"
    echo ""
    exit 1
fi

echo "      ✅ Login URL received"
echo ""

# Step 3: Open browser
echo "[3/4] Opening Kite login in browser..."
echo ""
echo "      URL: $LOGIN_URL"
echo ""

# Detect OS and open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$LOGIN_URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open &> /dev/null; then
        xdg-open "$LOGIN_URL"
    elif command -v gnome-open &> /dev/null; then
        gnome-open "$LOGIN_URL"
    else
        echo "      ⚠️  Could not auto-open browser"
        echo "      Please manually open the URL above"
    fi
fi

echo ""

# Step 4: Wait for confirmation
echo "[4/4] Waiting for authentication..."
echo ""
echo "      📱 Complete the authentication in your browser"
echo "      🔐 Authorize the application"
echo "      ✅ Session will be active for the trading day"
echo ""

# Check if authentication succeeded (by trying to get profile)
echo "      Press Enter after you've completed authentication..."
read -r

echo ""
echo "      Verifying authentication..."

PROFILE_RESPONSE=$(curl -s -X POST "$MCP_SERVER_URL/mcp" \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_profile",
            "arguments": {}
        }
    }')

if echo "$PROFILE_RESPONSE" | grep -q "user_id"; then
    echo "      ✅ Authentication successful!"
    echo ""

    # Extract user info if jq is available
    if command -v jq &> /dev/null; then
        USER_NAME=$(echo "$PROFILE_RESPONSE" | jq -r '.result.content[0].text' | grep -o '"user_name":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$USER_NAME" ] && [ "$USER_NAME" != "null" ]; then
            echo "      👤 Logged in as: $USER_NAME"
        fi
    fi

    echo ""
    echo "========================================================================"
    echo "  🎉 READY TO TRADE"
    echo "========================================================================"
    echo ""
    echo "  Your Kite session is active for today's trading session."
    echo "  You can now start the trading system:"
    echo ""
    echo "  cd \"/sessions/wizardly-confident-hopper/mnt/AI Trading /trading-system-v3\""
    echo "  ./start_system.sh"
    echo ""
    echo "========================================================================"
    echo ""
else
    echo "      ❌ Authentication failed or incomplete"
    echo ""
    echo "      Please try again or check:"
    echo "      - Did you complete the authorization?"
    echo "      - Are your API credentials correct in .env?"
    echo "      - Check server logs: tail -f /tmp/kite-mcp-server.log"
    echo ""
    exit 1
fi
