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
HEALTH_URL = f"http://localhost:{MCP_PORT}/"

# Locate strict paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
MCP_SERVER_DIR = SCRIPT_DIR / "kite-mcp-server"
MCP_SERVER_BIN = MCP_SERVER_DIR / "kite-mcp-server"

def load_env():
    """Load .env file manually to avoid dependencies"""
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
        print(f"⚠️ Permission denied reading {ENV_FILE}. Using environment variables if set.")
        if os.environ.get("KITE_API_KEY"):
            return True
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
        return None

    if not load_env():
        return None

    try:
        # Use a new process group to avoid termination signals propagating?
        # For simple script runner, Popen is enough if we keep parent alive.
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
            new_session_id = response.getheader("Mcp-Session-Id")
            return result, new_session_id
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        return None, None
    except Exception as e:
        print(f"Error calling MCP: {e}")
        return None, None

def main():
    print("KITE AUTH KEEPER - Starting")
    
    server_process = None
    if not check_server():
        server_process = start_server()
        if not server_process:
            sys.exit(1)
            
        print("Waiting for server...")
        for i in range(30):
            if check_server():
                print("✅ Server started!")
                break
            time.sleep(1)
        else:
            print("❌ Server timeout.")
            if server_process: server_process.terminate()
            sys.exit(1)
    else:
        print("✅ Server already running.")

    try:
        print("\n[1/3] Initializing Session...")
        init_result, session_id = call_mcp("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "keeper-script", "version": "1.0"}
        })
        
        if not session_id:
            print("❌ Failed to get Session ID.")
            return

        print(f"✅ Session: {session_id}")

        print("\n[2/3] Login URL...")
        login_result, _ = call_mcp("tools/call", {
            "name": "login",
            "arguments": {}
        }, session_id)

        # Extract URL
        content = login_result.get("result", {}).get("content", [{}])[0].get("text", "")
        import re
        url_match = re.search(r'\((https://kite\.zerodha\.com/[^)]+)\)', content)
        
        if url_match:
            login_url = url_match.group(1)
            print(f"LOGIN_URL: {login_url}")
            print("OPENING_BROWSER")
            try:
                webbrowser.open(login_url)
            except:
                pass
            
            # Wait for user signal
            print("WAITING_FOR_USER_INPUT")
            sys.stdout.flush()
            input() # Wait for newline from agent
            
            print("VERIFYING")
            profile_result, _ = call_mcp("tools/call", {
                "name": "get_profile",
                "arguments": {}
            }, session_id)
            
            if profile_result and "result" in profile_result:
                 print("✅ AUTH_SUCCESS")
                 print("KEEPING_ALIVE")
                 sys.stdout.flush()
                 
                 # Keep running forever
                 while True:
                     time.sleep(60)
            else:
                 print("❌ AUTH_FAILED")
        else:
            print("❌ NO_URL_FOUND")

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    main()
