#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path

# Configuration
MCP_PORT = 8080
MCP_URL = f"http://localhost:{MCP_PORT}/mcp"
HEALTH_URL = f"http://localhost:{MCP_PORT}/"  # Root URL for health check

# Locate strict paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
MCP_SERVER_DIR = SCRIPT_DIR / "kite-mcp-server"
MCP_SERVER_BIN = MCP_SERVER_DIR / "kite-mcp-server"

def load_env():
    """Load .env file manually to avoid dependencies"""
    # Check if vars already exist
    if os.environ.get("KITE_API_KEY") and os.environ.get("KITE_API_SECRET"):
        print("✅ Credentials found in environment variables.")
        return True

    print(f"Loading .env from {ENV_FILE}")
    try:
        if not ENV_FILE.exists():
            print(f"⚠️ .env file not found at {ENV_FILE}")
            return False
            
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        return True
    except PermissionError:
        print(f"⚠️ Permission denied reading {ENV_FILE}. Asking user to export variables manually if needed.")
        return False
    except Exception as e:
        print(f"⚠️ Error reading .env: {e}")
        return False

def check_server():
    """Check if server is running"""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
            return response.status == 200
    except:
        return False

def start_server():
    """Start the MCP server"""
    print("Starting Kite MCP Server...")
    
    if not MCP_SERVER_BIN.exists():
        print(f"❌ Binary not found at {MCP_SERVER_BIN}")
        print("Please run 'go build -o kite-mcp-server' in that directory.")
        return None

    # Load env vars
    if not load_env():
        return None

    # Start process
    try:
        process = subprocess.Popen(
            [str(MCP_SERVER_BIN)],
            cwd=str(MCP_SERVER_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        print(f"❌ Failed to launch process: {e}")
        return None

def call_mcp(method, params, session_id=None):
    """Make a JSON-RPC call to MCP server"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
        
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            # Extract session ID from header if present
            new_session_id = response.getheader("Mcp-Session-Id")
            return result, new_session_id
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return None, None
    except Exception as e:
        print(f"Error calling MCP: {e}")
        return None, None

def main():
    print("==================================================")
    print("  KITE AUTHENTICATION HELPER (Python Version)")
    print("==================================================")
    
    # 1. Start Server
    server_process = None
    if not check_server():
        server_process = start_server()
        if not server_process:
            sys.exit(1)
            
        print("Waiting for server to start...")
        for i in range(60):
            if check_server():
                print("✅ Server started!")
                break
            if i % 5 == 0:
                print(f"   Waiting... ({i}s)")
            time.sleep(1)
        else:
            print("❌ Server failed to start (timeout).")
            if server_process:
                try:
                    outs, errs = server_process.communicate(timeout=2)
                    if outs:
                        print(f"\nServer Output (stdout):\n{outs.decode('utf-8')}")
                    if errs:
                        print(f"\nServer Error Output (stderr):\n{errs.decode('utf-8')}")
                except Exception as e:
                    print(f"Could not read output: {e}")
                
                if server_process.poll() is not None:
                    print(f"Server exited with code {server_process.returncode}")
                
                server_process.terminate()
            sys.exit(1)
    else:
        print("✅ Server is already running.")

    try:
        # 2. Initialize (Handshake)
        print("\n[1/3] Initializing Session...")
        init_result, session_id = call_mcp("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "auth-script", "version": "1.0"}
        })
        
        if not session_id:
            print("❌ Failed to get Session ID from initialize.")
            return

        print(f"✅ Session Initialized (ID: {session_id})")

        # 3. Request Login URL
        print("\n[2/3] Requesting Login URL...")
        login_result, _ = call_mcp("tools/call", {
            "name": "login",
            "arguments": {}
        }, session_id)

        if not login_result or "error" in login_result:
            print(f"❌ Login call failed: {login_result}")
            return

        # Extract URL (it's embedded in the text content)
        content = login_result.get("result", {}).get("content", [{}])[0].get("text", "")
        # Very hacky extraction because the tool returns markdown text
        import re
        url_match = re.search(r'\((https://kite\.zerodha\.com/[^)]+)\)', content)
        
        if url_match:
            login_url = url_match.group(1)
            print(f"✅ Login URL received")
            print(f"\nURL: {login_url}\n")
            
            print("[3/3] Opening Browser...")
            webbrowser.open(login_url)
            
            input("\nPress Enter after you have authenticated in the browser...")
            
            # Verify Profile
            print("\nVerifying...")
            profile_result, _ = call_mcp("tools/call", {
                "name": "get_profile",
                "arguments": {}
            }, session_id)
            
            if profile_result and "result" in profile_result:
                 print("✅ Authentication Verified!")
                 print("You can now close this script and start the trading system.")
            else:
                 print("❌ Verification failed. Please try again.")

        else:
            print("❌ Could not parse URL from response.")
            print(content)

    finally:
        # Cleanup if needed
        pass

if __name__ == "__main__":
    main()
