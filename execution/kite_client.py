
import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configuration
MCP_PORT = 8080
MCP_URL = f"http://localhost:{MCP_PORT}/mcp"
HEALTH_URL = f"http://localhost:{MCP_PORT}/"

# Locate strict paths (Adjust as necessary based on where this file is located)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"
MCP_SERVER_DIR = SCRIPT_DIR / "kite-mcp-server"
MCP_SERVER_BIN = MCP_SERVER_DIR / "kite-mcp-server"

class KiteMCPClient:
    """
    A client wrapper for the Kite MCP Server.
    Handles process management, authentication, and JSON-RPC calls.
    """

    def __init__(self):
        self.session_id: Optional[str] = None
        self.process: Optional[subprocess.Popen] = None

    def load_env(self) -> bool:
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
            print(f"⚠️ Permission denied reading {ENV_FILE}.")
            return False
        except Exception as e:
            print(f"⚠️ Error reading .env: {e}")
            return False

    def check_server(self) -> bool:
        """Check if server is running"""
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
                return response.status == 200
        except:
            return False

    def start_server(self) -> bool:
        """Start the MCP server subprocess"""
        print("Starting Kite MCP Server...")
        
        if not MCP_SERVER_BIN.exists():
            print(f"❌ Binary not found at {MCP_SERVER_BIN}")
            print("Please run 'go build -o kite-mcp-server' in that directory.")
            return False

        # Load env vars needed for the server
        if not self.load_env():
            return False

        # Start process
        try:
            self.process = subprocess.Popen(
                [str(MCP_SERVER_BIN)],
                cwd=str(MCP_SERVER_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for it to come up
            print("Waiting for server to start...")
            for i in range(30):
                if self.check_server():
                    print("✅ Server started!")
                    return True
                time.sleep(1)
            
            print("❌ Server failed to start (timeout).")
            self.stop_server()
            return False
            
        except Exception as e:
            print(f"❌ Failed to launch process: {e}")
            return False

    def stop_server(self):
        """Terminate the server process if we started it"""
        if self.process:
            self.process.terminate()
            self.process = None

    def _call(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Make a raw JSON-RPC call to MCP server"""
        if params is None:
            params = {}
            
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params
        }
        
        req = urllib.request.Request(
            MCP_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        if self.session_id:
            req.add_header("Mcp-Session-Id", self.session_id)
            
        try:
            with urllib.request.urlopen(req) as response:
                result_json = json.loads(response.read().decode('utf-8'))
                
                # Update session ID if changed
                new_session = response.getheader("Mcp-Session-Id")
                if new_session:
                    self.session_id = new_session

                if "error" in result_json:
                    raise Exception(f"MCP Error: {result_json['error']}")
                
                return result_json.get("result")
                
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
            
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Helper to call an MCP tool"""
        if arguments is None:
            arguments = {}
            
        response = self._call("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        # Tools typically return a content list. We want to parse the JSON inside.
        # But wait, looking at the MCP spec and Go implementation:
        # The Go implementation returns `handler.MarshalResponse(data)` which typically
        # structures it as content: [{type: text, text: JSON_STRING}]
        
        try:
            content = response.get("content", [])
            if not content:
                return None
                
            text = content[0].get("text", "")
            # The Kite MCP server returns the data directly as JSON string in text
            return json.loads(text)
        except json.JSONDecodeError:
            return text # Return raw text if not JSON
        except Exception as e:
            print(f"Error parsing tool response: {e}")
            return response

    def initialize(self) -> bool:
        """Perform MCP handshake"""
        print("[MCP] Initializing Session...")
        try:
            res = self._call("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "kite-python-client", "version": "1.0"}
            })
            # The session ID is usually set in headers during this call
            if self.session_id:
                print(f"✅ Session Initialized (ID: {self.session_id})")
                return True
            else:
                print("❌ Failed to get Session ID.")
                return False
        except Exception as e:
            print(f"❌ Initialize failed: {e}")
            return False

    def login(self) -> bool:
        """
        Request login URL, open browser, and wait for user.
        """
        if not self.session_id:
            if not self.initialize():
                return False

        print("\n[MCP] Requesting Login URL...")
        try:
            # We use _call instead of call_tool here because 'login' returns 
            # a text message with the URL, not a JSON data object.
            response = self._call("tools/call", {
                "name": "login",
                "arguments": {}
            })
            
            content = response.get("content", [{}])[0].get("text", "")
            
            import re
            url_match = re.search(r'\((https://kite\.zerodha\.com/[^)]+)\)', content)
            
            if url_match:
                login_url = url_match.group(1)
                print(f"✅ Login URL received")
                print(f"\nURL: {login_url}\n")
                
                print("Opening Browser...")
                webbrowser.open(login_url)
                
                input("\n👉 Press Enter after you have authenticated in the browser... ")
                
                # Verify
                print("\nVerifying session...")
                profile = self.get_profile()
                if profile:
                     print(f"✅ Authenticated as {profile.get('user_name')} ({profile.get('user_id')})")
                     return True
                else:
                     print("❌ Verification failed.")
                     return False
            else:
                print("❌ Could not parse URL from response.")
                print(content)
                return False
                
        except Exception as e:
             print(f"❌ Login flow error: {e}")
             return False

    # --- Market Data Tools ---

    def get_profile(self):
        return self.call_tool("get_profile")

    def get_margins(self):
        return self.call_tool("get_margins")

    def get_holdings(self):
        return self.call_tool("get_holdings")
        
    def get_positions(self):
        return self.call_tool("get_positions")

    def get_orders(self):
        return self.call_tool("get_orders")

    def search_instruments(self, query: str, filter_on: str = "id", limit: int = 10):
        return self.call_tool("search_instruments", {
            "query": query,
            "filter_on": filter_on,
            "limit": limit
        })

    def get_quotes(self, instruments: List[str]):
        """
        Get API quotes.
        instruments list eg: ["NSE:INFY", "BSE:SENSEX"]
        """
        return self.call_tool("get_quotes", {
            "instruments": instruments
        })

    def get_ltp(self, instruments: List[str]):
        return self.call_tool("get_ltp", {
            "instruments": instruments
        })

    def get_ohlc(self, instruments: List[str]):
        return self.call_tool("get_ohlc", {
            "instruments": instruments
        })

    def get_historical_data(self, instrument_token: int, from_date: str, to_date: str, interval: str, continuous: bool = False, oi: bool = False):
        """
        from_date/to_date format: YYYY-MM-DD HH:MM:SS
        interval: minute, day, 3minute, 5minute, etc.
        """
        return self.call_tool("get_historical_data", {
            "instrument_token": instrument_token,
            "from_date": from_date,
            "to_date": to_date,
            "interval": interval,
            "continuous": continuous,
            "oi": oi
        })

    # --- Order Tools ---

    def place_order(self, 
                    tradingsymbol: str, 
                    transaction_type: str, 
                    quantity: int, 
                    product: str, 
                    order_type: str, 
                    exchange: str = "NSE", 
                    price: float = 0.0, 
                    trigger_price: float = 0.0, 
                    variety: str = "regular",
                    validity: str = "DAY",
                    disclosed_quantity: int = 0,
                    tag: str = ""):
        
        args = {
            "variety": variety,
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "product": product,
            "order_type": order_type,
            "validity": validity
        }
        
        if price > 0: args["price"] = price
        if trigger_price > 0: args["trigger_price"] = trigger_price
        if disclosed_quantity > 0: args["disclosed_quantity"] = disclosed_quantity
        if tag: args["tag"] = tag

        return self.call_tool("place_order", args)

