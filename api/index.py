import os
import httpx
import json
import urllib.parse
from datetime import datetime

# ---- CORE COMPONENT ENGINE LAYERS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "SHAYAN_EXPLORER"

# Global system log array (Maintained safely across live browser cycles via active queries)
LIVE_TRAFFIC_LOGS = []

def parse_query_string(query_string: str) -> dict:
    if not query_string:
        return {}
    pairs = query_string.split('&')
    params = {}
    for pair in pairs:
        if '=' in pair:
            k, v = pair.split('=', 1)
            params[k] = v
    return params

async def app(scope, receive, send):
    global LIVE_TRAFFIC_LOGS
    
    if scope['type'] != 'http':
        return

    path = scope['path']
    query_string = scope.get('query_string', b'').decode('utf-8')
    params = parse_query_string(query_string)

    # ====================================================
    # 1. LIVE API ROUTER INTERACTION INTERFACES
    # ====================================================
    if path.startswith("/api/"):
        endpoint = path.replace("/api/", "", 1)
        client_key = params.get("key")
        
        # Client profile credentials passed down dynamically by the web UI runtime for server validation
        client_name = urllib.parse.unquote(params.get("client_name", "External App"))
        key_limit = int(params.get("key_limit", 1000))
        key_used = int(params.get("key_used", 0))
        key_expiry = urllib.parse.unquote(params.get("key_expires", "2027-12-31 23:59:59"))
        allowed_tools = urllib.parse.unquote(params.get("key_tools", "all"))

        if not client_key:
            await send_json(send, {"error": "Invalid token configuration identifier."}, 403)
            return

        # Check Expiration Frame
        try:
            if datetime.utcnow() > datetime.strptime(key_expiry, "%Y-%m-%d %H:%M:%S"):
                await send_json(send, {"error": "Your allocated license access window has expired."}, 403)
                return
        except Exception:
            pass

        # Check Total Quota Limits
        if key_used >= key_limit:
            await send_json(send, {"error": "API daily/total query limitations exhausted."}, 429)
            return

        # Validate Modular Target Scopes
        if allowed_tools != "all":
            allowed_list = [t.strip() for t in allowed_tools.split(",")]
            if endpoint not in allowed_list:
                await send_json(send, {"error": f"Access denied to target sub-module: {endpoint}"}, 403)
                return

        # Clean query variables for secure upstream routing delivery
        cleaned_params = {k: v for k, v in params.items() if k not in ["key", "client_name", "key_limit", "key_used", "key_expires", "key_tools"]}
        
        # Inject current traffic analytics
        LIVE_TRAFFIC_LOGS.insert(0, {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })

        # Append master upstream access credentials
        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(upstream_url, params=cleaned_params, timeout=12.0)
                await send_json(send, response.json(), response.status_code)
                return
            except Exception as e:
                await send_json(send, {"error": "Core gateway forwarding timed out", "details": str(e)}, 502)
                return

    # ====================================================
    # 2. APPLICATION LIVE TRAFFIC MONITOR SYNCING POOL
    # ====================================================
    elif path == "/admin/logs":
        await send_json(send, {"logs": LIVE_TRAFFIC_LOGS[:30]})
        return

    # ====================================================
    # 3. CENTRAL ULTRA-PREMIUM INTERFACE RENDERING ENGINE (/)
    # ====================================================
    elif path == "/":
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Control Center | {DEVELOPER_NAME}</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background-color: #030712; 
                    color: #cbd5e1; 
                    font-family: 'Courier New', monospace;
                    position: relative;
                    overflow-x: hidden;
                    min-height: 100vh;
                }}
                /* Glow Cyberpunk Effects */
                .panel {{ 
                    background: rgba(10, 15, 30, 0.8); 
                    border: 1px solid rgba(59, 130, 246, 0.25); 
                    box-shadow: 0 0 20px rgba(59, 130, 246, 0.15), inset 0 0 15px rgba(59, 130, 246, 0.05);
                    backdrop-filter: blur(8px);
                }}
                .neon-txt {{ 
                    text-shadow: 0 0 12px rgba(37, 99, 235, 0.8), 0 0 4px rgba(37, 99, 235, 0.4); 
                }}
                .neon-border-focus:focus {{
                    border-color: #3b82f6;
                    box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
                }}
                
                /* High-Performance Mobile-Friendly Snowfall Background Animation */
                .snow-container {{
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    pointer-events: none;
                    z-index: 1;
                }}
                .snowflake {{
                    position: absolute;
                    top: -10px;
                    color: #fff;
                    font-size: 1em;
                    opacity: 0.7;
                    user-select: none;
                    animation: fall linear infinite;
                }}
                @keyframes fall {{
                    0% {{ transform: translateY(0) translateX(0); opacity: 0; }}
                    10% {{ opacity: 0.6; }}
                    90% {{ opacity: 0.6; }}
                    100% {{ transform: translateY(105vh) translateX(50px); opacity: 0; }}
                }}
            </style>
        </head>
        <body class="p-4 md:p-6">
            <!-- Snow System Integration -->
            <div class="snow-container" id="snow"></div>

            <div class="max-w-7xl mx-auto relative z-10">
                <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 border-b border-gray-800 pb-4 gap-4">
                    <div>
                        <h1 class="text-xl md:text-2xl font-bold text-blue-500 neon-txt tracking-wider">NEXUS PERSISTENT GATEWAY</h1>
                        <p class="text-xs text-gray-500 mt-1">CORE ARCHITECT: {DEVELOPER_NAME}</p>
                    </div>
                    <div class="flex flex-wrap items-center gap-2">
                        <!-- Top Corner Feature: Reveal Clean Values Token Action Utility Button -->
                        <button onclick="toggleKeyMasking()" class="bg-gradient-to-r from-purple-900 to-indigo-900 hover:from-purple-800 hover:to-indigo-800 border border-indigo-500 text-indigo-200 text-xs font-bold px-3 py-2 rounded shadow-lg transition transform active:scale-95">
                            👁️ REVEAL RECON NO-KEY
                        </button>
                        <span class="text-xs bg-green-950 text-green-400 border border-green-800 px-3 py-1 rounded-full font-bold tracking-widest">LOCAL_STORAGE SYNCED</span>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Provision Management Form Panel -->
                    <div class="panel p-5 rounded-xl flex flex-col justify-between">
                        <div>
                            <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider flex items-center gap-2">
                                <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span> Provision Secure Key
                            </h2>
                            <form id="keyForm" onsubmit="handleFormSubmit(event)" class="space-y-4 text-xs">
                                <div>
                                    <label class="block text-gray-400 mb-1 tracking-widest">CLIENT ASSIGNED NAME</label>
                                    <input type="text" id="formName" required class="w-full bg-gray-950 border border-gray-800 rounded p-2.5 text-white focus:outline-none neon-border-focus">
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1 tracking-widest">CUSTOM API ACCESS LICENSE KEY</label>
                                    <div class="flex gap-2">
                                        <input type="text" id="formKey" placeholder="VIP-KEY-XYZ" required class="w-full bg-gray-950 border border-gray-800 rounded p-2.5 text-white focus:outline-none neon-border-focus">
                                        <button type="button" onclick="generateRandomToken()" class="bg-gray-800 px-3 text-white rounded hover:bg-gray-700">⚡</button>
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1 tracking-widest">MAX QUOTA REQUEST LIMIT</label>
                                    <input type="number" id="formLimit" value="1000" required class="w-full bg-gray-950 border border-gray-800 rounded p-2.5 text-white focus:outline-none neon-border-focus">
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1 tracking-widest">EXPIRATION WINDOW TIMESTAMP</label>
                                    <input type="datetime-local" id="formExpires" required class="w-full bg-gray-950 border border-gray-800 rounded p-2.5 text-white focus:outline-none neon-border-focus">
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1 tracking-widest">ALLOWED ENDPOINTS SCOPE (or 'all')</label>
                                    <input type="text" id="formTools" value="all" required class="w-full bg-gray-950 border border-gray-800 rounded p-2.5 text-white focus:outline-none neon-border-focus">
                                </div>
                                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded tracking-widest uppercase transition-all shadow-md">Inject Records</button>
                            </form>
                        </div>
                    </div>

                    <!-- Client Key Registry Table Matrix Allocation Grid -->
                    <div class="lg:col-span-2 panel p-5 rounded-xl overflow-x-auto flex flex-col justify-between">
                        <div>
                            <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Active Token Allocations</h2>
                            <table class="w-full text-left text-xs min-w-[600px]">
                                <thead>
                                    <tr class="border-b border-gray-800 text-gray-500 font-mono tracking-widest">
                                        <th class="pb-3">CLIENT</th>
                                        <th class="pb-3">TOKEN KEY IDENTIFIER</th>
                                        <th class="pb-3">USAGE STATUS</th>
                                        <th class="pb-3">EXPIRATION TIMESTAMP</th>
                                        <th class="pb-3">SCOPE</th>
                                        <th class="pb-3 text-right">ACTION</th>
                                    </tr>
                                </thead>
                                <tbody id="keyTableBody" class="divide-y divide-gray-900">
                                    <!-- Embedded Dynamically via JavaScript Local Storage Matrix Runtime -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- NEW INTERACTIVE FEATURE: Click-and-Select Live API Playground Execution Matrix Router -->
                <div class="mt-6 panel p-5 rounded-xl">
                    <h2 class="text-sm font-bold mb-3 text-blue-400 uppercase tracking-wider">Dynamic Interactive Playground Routing Desk</h2>
                    <p class="text-xs text-gray-500 mb-4">Click any target resource tool card to instantly bind the path router selection parameter without manual writing.</p>
                    <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs text-center">
                        <div onclick="selectEndpoint('truecaller')" class="p-3 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-850 active:scale-95 transition-all">📱 Truecaller</div>
                        <div onclick="selectEndpoint('whatsapp')" class="p-3 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-850 active:scale-95 transition-all">💬 WhatsApp</div>
                        <div onclick="selectEndpoint('instagram')" class="p-3 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-850 active:scale-95 transition-all">📸 Instagram</div>
                        <div onclick="selectEndpoint('scraper')" class="p-3 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-850 active:scale-95 transition-all">🌐 Scraper</div>
                        <div onclick="selectEndpoint('lookup')" class="p-3 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-850 active:scale-95 transition-all">🔍 OSINT Search</div>
                        <div onclick="selectEndpoint('bypass')" class="p-3 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-850 active:scale-95 transition-all">🔓 Core Bypass</div>
                    </div>

                    <!-- Sandbox Testing Frame Execution Interface -->
                    <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 items-end text-xs">
                        <div>
                            <label class="block text-gray-500 mb-1">SELECTED GATEWAY PATH</label>
                            <input type="text" id="sandboxPath" value="truecaller" class="w-full bg-gray-950 border border-gray-800 rounded p-2 text-white font-mono" readonly>
                        </div>
                        <div>
                            <label class="block text-gray-500 mb-1">TEST CONSOLE APP LICENSE KEY</label>
                            <input type="text" id="sandboxKey" placeholder="Paste or input provisioned key..." class="w-full bg-gray-950 border border-gray-800 rounded p-2 text-yellow-500 font-mono">
                        </div>
                        <button onclick="runSandboxTest()" class="w-full bg-gradient-to-r from-blue-700 to-blue-800 hover:from-blue-600 hover:to-blue-700 font-bold py-2 px-4 rounded tracking-wider transition uppercase">Fire Verification Probe</button>
                    </div>
                    <div id="sandboxResult" class="hidden mt-4 p-3 bg-black border border-gray-900 rounded font-mono text-xs overflow-x-auto text-green-400 whitespace-pre-wrap"></div>
                </div>

                <!-- Core Analytics Monitor Live Console Feed Feed -->
                <div class="mt-6 panel p-5 rounded-xl">
                    <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider flex justify-between items-center">
                        <span>Live Traffic Query Inspection Feed</span>
                        <button onclick="refreshTrafficLogs()" class="text-xs bg-gray-900 hover:bg-gray-800 px-3 py-1 rounded border border-gray-700">🔄 Synchronize Feed</button>
                    </h2>
                    <div class="overflow-x-auto max-h-60 text-xs font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="border-b border-gray-800 text-gray-500">
                                    <th class="pb-2">TIMESTAMP</th>
                                    <th class="pb-2">TOKEN REF</th>
                                    <th class="pb-2">ENDPOINT RESOURCE</th>
                                    <th class="pb-2">LOOKUP DATA PARAMETERS</th>
                                </tr>
                            </thead>
                            <tbody id="logsTableBody" class="divide-y divide-gray-900">
                                <tr>
                                    <td colspan="4" class="py-4 text-center text-gray-600">Awaiting runtime data packets stream transmission...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- UI ENGINE PERSISTENCE LOGIC SCRIPT CODES -->
            <script>
                let maskKeysState = true;
                const defaultExpiry = "2027-12-31T23:59";
                document.getElementById('formExpires').value = defaultExpiry;

                // Secure initialization step for state persistence
                if(!localStorage.getItem('NEXUS_KEYS')) {{
                    localStorage.setItem('NEXUS_KEYS', JSON.stringify({{
                        "VIP-SHAYAN": {{
                            name: "Beta Master",
                            limit: 5000,
                            used: 0,
                            expires_at: "2027-12-31 23:59:59",
                            allowed_tools: "all"
                        }}
                    }}));
                }}

                function loadKeysRegistry() {{
                    const data = JSON.parse(localStorage.getItem('NEXUS_KEYS') || '{{}}');
                    const tbody = document.getElementById('keyTableBody');
                    tbody.innerHTML = '';

                    if(Object.keys(data).length === 0) {{
                        tbody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-gray-600">No active keys assigned inside browser local storage space.</td></tr>`;
                        return;
                    }}

                    for (const [key, info] of Object.entries(data)) {{
                        const visibleKey = maskKeysState ? '••••••••••••' : key;
                        const copyActionArg = maskKeysState ? `"${{info.name}} - ${{info.allowed_tools}} - Limit: ${{info.used}}/${{info.limit}}"` : `"${{key}}"`;
                        
                        tbody.innerHTML += `
                            <tr class="hover:bg-gray-950 transition-colors">
                                <td class="py-3 text-white font-bold tracking-wide">${{info.name}}</td>
                                <td class="py-3 text-yellow-500 font-mono select-all">
                                    <span class="cursor-pointer hover:underline" onclick='copyValueToClipboard(${{copyActionArg}})' title="Click to instantly copy values">${{visibleKey}}</span>
                                </td>
                                <td class="py-3 font-mono text-gray-300">${{info.used}} / ${{info.limit}}</td>
                                <td class="py-3 text-gray-400 font-sans text-xs">${{info.expires_at}}</td>
                                <td class="py-3 text-blue-400 font-mono">${{info.allowed_tools}}</td>
                                <td class="py-3 text-right">
                                    <button onclick="revokeKey('${{key}}')" class="text-red-500 hover:text-red-400 font-bold hover:underline">REVOKE</button>
                                </td>
                            </tr>
                        `;
                    }}
                }}

                function handleFormSubmit(e) {{
                    e.preventDefault();
                    const name = document.getElementById('formName').value;
                    const key = document.getElementById('formKey').value.trim();
                    const limit = parseInt(document.getElementById('formLimit').value);
                    let rawExpiry = document.getElementById('formExpires').value.replace('T', ' ');
                    if(rawExpiry.length === 16) rawExpiry += ":00";
                    const tools = document.getElementById('formTools').value;

                    const currentData = JSON.parse(localStorage.getItem('NEXUS_KEYS') || '{{}}');
                    currentData[key] = {{
                        name: name,
                        limit: limit,
                        used: 0,
                        expires_at: rawExpiry,
                        allowed_tools: tools
                    }};

                    localStorage.setItem('NEXUS_KEYS', JSON.stringify(currentData));
                    document.getElementById('keyForm').reset();
                    document.getElementById('formExpires').value = defaultExpiry;
                    loadKeysRegistry();
                }}

                function revokeKey(key) {{
                    const currentData = JSON.parse(localStorage.getItem('NEXUS_KEYS') || '{{}}');
                    if(currentData[key]) {{
                        delete currentData[key];
                        localStorage.setItem('NEXUS_KEYS', JSON.stringify(currentData));
                        loadKeysRegistry();
                    }}
                }}

                // Feature 1: Reveal values configuration array without private token identifiers
                function toggleKeyMasking() {{
                    maskKeysState = !maskKeysState;
                    loadKeysRegistry();
                }}

                // Feature 2: High-speed absolute copy shortcut utility interaction rule
                function copyValueToClipboard(text) {{
                    navigator.clipboard.writeText(text).then(() => {{
                        alert("Copied configuration package to clipboard payload matrix!\\n" + text);
                    }}).catch(() => {{
                        alert("Fallback copy processing error.");
                    }});
                }}

                // Feature 3: Select specialized tool click nodes natively without field manual inputs
                function selectEndpoint(name) {{
                    document.getElementById('sandboxPath').value = name;
                }}

                function generateRandomToken() {{
                    const token = "NEXUS-" + Math.random().toString(36).substring(2, 7).toUpperCase() + "-" + Math.random().toString(36).substring(2, 7).toUpperCase();
                    document.getElementById('formKey').value = token;
                }}

                async function runSandboxTest() {{
                    const endpoint = document.getElementById('sandboxPath').value;
                    const key = document.getElementById('sandboxKey').value.trim();
                    const display = document.getElementById('sandboxResult');

                    if(!key) {{
                        alert("Please select or input an access token key first.");
                        return;
                    }}

                    const storedData = JSON.parse(localStorage.getItem('NEXUS_KEYS') || '{{}}');
                    const keyProfile = storedData[key] || {{ name: "External Request", limit: 1000, used: 0, expires_at: "2027-12-31 23:59:59", allowed_tools: "all" }};

                    display.classList.remove('hidden');
                    display.innerText = "Transmitting probe sequence down to serverless environment worker processing pipeline...";

                    // Dynamically pass browser validation metrics inside the payload parameters to maintain persistence across instances
                    const queryUrl = `/api/${{endpoint}}?key=${{encodeURIComponent(key)}}&client_name=${{encodeURIComponent(keyProfile.name)}}&key_limit=${{keyProfile.limit}}&key_used=${{keyProfile.used}}&key_expires=${{encodeURIComponent(keyProfile.expires_at)}}&key_tools=${{encodeURIComponent(keyProfile.allowed_tools)}}&num=12345`;

                    try {{
                        const res = await fetch(queryUrl);
                        const payload = await res.json();
                        
                        if (res.ok) {{
                            // Increment local usage securely upon a valid proxy verification confirmation
                            if(storedData[key]) {{
                                storedData[key].used += 1;
                                localStorage.setItem('NEXUS_KEYS', JSON.stringify(storedData));
                                loadKeysRegistry();
                            }}
                        }}
                        display.innerText = JSON.stringify(payload, null, 4);
                    }} catch(err) {{
                        display.innerText = "System Failure Event Channel Connection: " + err.toString();
                    }}
                    refreshTrafficLogs();
                }}

                async function refreshTrafficLogs() {{
                    try {{
                        const res = await fetch('/admin/logs');
                        const data = await res.json();
                        const tbody = document.getElementById('logsTableBody');
                        tbody.innerHTML = '';

                        if(!data.logs || data.logs.length === 0) {{
                            tbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-gray-600">No telemetry packets intercepted yet.</td></tr>`;
                            return;
                        }}

                        data.logs.forEach(log => {{
                            tbody.innerHTML += `
                                <tr class="border-b border-gray-950 hover:bg-gray-950">
                                    <td class="py-2 text-gray-500">${{log.timestamp}}</td>
                                    <td class="py-2 text-yellow-600 font-bold">${{log.key}}</td>
                                    <td class="py-2 text-green-400">/api/${{log.endpoint}}</td>
                                    <td class="py-2 text-gray-400 font-sans bg-gray-900 bg-opacity-40 px-2 rounded">${{log.params}}</td>
                                </tr>
                            `;
                        }});
                    }} catch(e) {{}}
                }}

                // Feature 4: Lightweight CSS optimization snowfall structure generator engine
                function runSnowfallEngine() {{
                    const container = document.getElementById('snow');
                    const maxSnowflakes = 25; // Balanced distribution boundary for maximum low-end mobile framing speeds
                    
                    for (let i = 0; i < maxSnowflakes; i++) {{
                        const flake = document.createElement('div');
                        flake.className = 'snowflake';
                        flake.innerHTML = '❄';
                        flake.style.left = Math.random() * 100 + 'vw';
                        flake.style.animationDuration = (Math.random() * 3 + 4) + 's'; // Varied speeds
                        flake.style.animationDelay = (Math.random() * 5) + 's';
                        flake.style.fontSize = (Math.random() * 0.6 + 0.6) + 'em';
                        container.appendChild(flake);
                    }}
                }}

                // Boot initialization routine trigger sequences
                window.onload = function() {{
                    loadKeysRegistry();
                    runSnowfallEngine();
                    refreshTrafficLogs();
                    setInterval(refreshTrafficLogs, 8000); // Continuous quiet automated tracking synchronization
                }};
            </script>
        </body>
        </html>
        """
        await send_html(send, html_content)
        return

    else:
        await send_json(send, {"detail": f"Path '{path}' not found on Nexus Gateway Server."}, 404)

async def send_json(send, data: dict, status_code: int = 200):
    body = json.dumps(data).encode('utf-8')
    await send({'type': 'http.response.start', 'status': status_code, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': body})

async def send_html(send, html_text: str):
    body = html_text.encode('utf-8')
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/html')]})
    await send({'type': 'http.response.body', 'body': body})

async def send_redirect(send, location: str):
    await send({'type': 'http.response.start', 'status': 303, 'headers': [(b'location', location.encode('utf-8'))]})
    await send({'type': 'http.response.body', 'body': b''})
