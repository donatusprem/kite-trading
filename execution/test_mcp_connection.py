import subprocess
import json
import sys
import os

# Path to the wrapper script we created
WRAPPER_SCRIPT = "/Users/ajaydonatusprem/Claude/AI Trading /execution/run_kite_mcp.sh"

def test_mcp_connection():
    print(f"Testing connection to: {WRAPPER_SCRIPT}")
    
    # Start the process
    try:
        process = subprocess.Popen(
            [WRAPPER_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"Failed to start process: {e}")
        return

    # Send initialize request (JSON-RPC 2.0)
    # This matches what Claude would send
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    
    print("Sending 'initialize' request...")
    try:
        # Write to stdin and flush
        json_req = json.dumps(initialize_request) + "\n"
        process.stdin.write(json_req)
        process.stdin.flush()
        
        # Read response from stdout
        # simple read loop, real implementations would be more robust
        response_line = process.stdout.readline()
        
        if response_line:
            print("Received response:")
            print(json.dumps(json.loads(response_line), indent=2))
            
            # If successful, try to list tools
            list_tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            print("\nSending 'tools/list' request...")
            process.stdin.write(json.dumps(list_tools_request) + "\n")
            process.stdin.flush()
            
            tools_response = process.stdout.readline()
            if tools_response:
                print("Received tools list:")
                tools_data = json.loads(tools_response)
                # Print just tool names to keep it clean
                if "result" in tools_data and "tools" in tools_data["result"]:
                     tools = [t["name"] for t in tools_data["result"]["tools"]]
                     print(f"Available Tools: {', '.join(tools)}")
                else:
                     print(json.dumps(tools_data, indent=2))
            else:
                print("No response for tools/list")
                
        else:
            print("No response received from server.")
            # Check stderr
            err = process.stderr.read()
            if err:
                print(f"Stderr output:\n{err}")

    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_mcp_connection()
