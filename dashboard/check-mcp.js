const { spawn } = require('child_process');
const http = require('http');
const https = require('https');
const url = require('url');

/**
 * CONFIGURATION
 * Set MODE to 'sse' for HTTP servers (like Kite) or 'stdio' for local scripts.
 */
const CONFIG = {
    mode: 'sse', // Options: 'sse' | 'stdio'

    // Configuration for 'sse' mode (Remote/HTTP)
    sse: {
        url: 'http://127.0.0.1:8080/sse'
    },

    // Configuration for 'stdio' mode (Local Process)
    stdio: {
        command: 'node',
        args: ['./path/to/your/mcp-server.js']
    }
};

async function checkMcpServer() {
    console.log(`🔍 Checking MCP Server (${CONFIG.mode.toUpperCase()} mode)...`);

    try {
        if (CONFIG.mode === 'sse') {
            await checkSseServer();
        } else {
            await checkStdioServer();
        }
    } catch (error) {
        console.error(`❌ Health check failed: ${error.message}`);
        if (error.message.includes('Connection refused')) {
            console.log('\n💡 Tip: Open a new terminal and run your MCP server (e.g., ./kite-mcp-server) before running this check.');
        }
        process.exit(1);
    }
}

// --- SSE (HTTP) Implementation ---

function checkSseServer() {
    return new Promise((resolve, reject) => {
        const target = CONFIG.sse.url;
        const lib = target.startsWith('https') ? https : http;

        console.log(`   Connecting to ${target}...`);

        // Set a connection timeout (in case the server is reachable but not responding)
        const connectionTimeout = setTimeout(() => {
            reject(new Error('Connection timed out (server might be down or blocked)'));
        }, 5000);

        const req = lib.get(target, (res) => {
            clearTimeout(connectionTimeout);
            console.log(`   HTTP Status: ${res.statusCode}`);
            if (res.statusCode !== 200) {
                reject(new Error(`HTTP Connection failed: ${res.statusCode} ${res.statusMessage}`));
                return;
            }

            let buffer = '';
            let postEndpoint = null;

            // Timeout if handshake takes too long
            const timeout = setTimeout(() => {
                req.destroy();
                reject(new Error('Timed out waiting for handshake'));
            }, 5000);

            res.on('end', () => {
                console.log('   ⚠️ SSE stream closed by server');
            });

            res.on('data', (chunk) => {
                const str = chunk.toString();
                console.log(`   [DEBUG] Raw Chunk: ${JSON.stringify(str)}`);
                buffer += str;
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6).trim();
                        console.log(`   Received data: ${data.substring(0, 100)}${data.length > 100 ? '...' : ''}`);

                        // 1. Discover POST endpoint (sent by server as plain text or JSON)
                        if (!postEndpoint && !data.startsWith('{')) {
                            const baseUrl = new url.URL(target);
                            // Handle relative or absolute URLs
                            postEndpoint = data.startsWith('http') ? data : new url.URL(data, baseUrl).toString();
                            console.log(`   Endpoint discovered: ${postEndpoint}`);

                            // Send Initialize Request to the discovered endpoint
                            console.log(`   [DEBUG] Sending initialize to ${postEndpoint}`);
                            sendInitialize(postEndpoint).then(() => {
                                console.log(`   [DEBUG] Initialize POST sent successfully`);
                            }).catch(err => {
                                clearTimeout(timeout);
                                reject(new Error(`Failed to send initialize: ${err.message}`));
                            });
                        }

                        // 2. Check for JSON-RPC response
                        if (data.startsWith('{')) {
                            try {
                                const msg = JSON.parse(data);
                                if (msg.id === 1 && msg.result && msg.result.protocolVersion) {
                                    clearTimeout(timeout);
                                    console.log('✅ MCP Server is functioning!');
                                    console.log('   Server Name:', msg.result.serverInfo?.name || 'Unknown');
                                    console.log('   Protocol Version:', msg.result.protocolVersion);
                                    res.destroy();
                                    resolve();
                                }
                            } catch (e) { }
                        }
                    }
                }
            });
        });

        req.on('error', (err) => {
            clearTimeout(connectionTimeout);
            if (err.code === 'ECONNREFUSED') {
                reject(new Error(`Connection refused at ${target}. Make sure the server is running on port 8080.`));
            } else {
                reject(err);
            }
        });
    });
}

function sendInitialize(postUrl) {
    return new Promise((resolve, reject) => {
        const parsed = new url.URL(postUrl);
        const body = JSON.stringify({
            jsonrpc: "2.0", id: 1, method: "initialize",
            params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "health-check", version: "1.0.0" } }
        });

        const lib = parsed.protocol === 'https:' ? https : http;
        const req = lib.request(postUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' } }, (res) => {
            if (res.statusCode >= 400) reject(new Error(`POST failed with ${res.statusCode}`));
            else resolve();
        });

        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

// --- Stdio (Local Process) Implementation ---

async function checkStdioServer() {
    console.log(`   Command: ${CONFIG.stdio.command} ${CONFIG.stdio.args.join(' ')}`);

    const server = spawn(CONFIG.stdio.command, CONFIG.stdio.args, {
        stdio: ['pipe', 'pipe', 'inherit'], // pipe stdin/stdout, inherit stderr for logs
    });

    server.on('error', (err) => {
        throw new Error(`Failed to spawn server process: ${err.message}`);
    });

    // Promise to handle the handshake verification
    return new Promise((resolve, reject) => {
        let buffer = '';

        // Set a timeout for the check
        const timeout = setTimeout(() => {
            server.kill();
            reject(new Error('Timed out waiting for initialization response (5000ms)'));
        }, 5000);

        server.stdout.on('data', (data) => {
            buffer += data.toString();
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const message = JSON.parse(line);
                    // Check for successful initialization response
                    if (message.id === 1 && message.result && message.result.protocolVersion) {
                        clearTimeout(timeout);
                        console.log('✅ MCP Server is functioning!');
                        console.log('   Server Name:', message.result.serverInfo?.name || 'Unknown');
                        console.log('   Protocol Version:', message.result.protocolVersion);
                        server.kill();
                        resolve();
                    }
                } catch (e) {
                    // Ignore non-JSON output (debug logs, etc.)
                }
            }
        });

        // 1. Send Initialize Request
        const initRequest = {
            jsonrpc: "2.0", id: 1, method: "initialize",
            params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "health-check", version: "1.0.0" } }
        };
        server.stdin.write(JSON.stringify(initRequest) + '\n');
    });
}

checkMcpServer();