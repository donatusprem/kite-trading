#!/bin/bash
# Hardcoded wrapper to run Kite MCP with the correct URL
# This bypasses potential JSON argument parsing issues in Claude Desktop

# Ensure node/npx is in path
export PATH="/Users/ajaydonatusprem/.nvm/versions/node/v20.19.6/bin:$PATH"

# Log start for debugging
echo "Starting Kite MCP wrapper at $(date)" >> /tmp/kite_mcp_wrapper.log

# Run the command with explicit arguments and error logging
exec /Users/ajaydonatusprem/.nvm/versions/node/v20.19.6/bin/npx -y mcp-remote "https://mcp.kite.trade/mcp" 2>> /tmp/kite_mcp_wrapper.log
