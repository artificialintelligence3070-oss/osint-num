import os
import httpx
import json
import urllib.parse
from datetime import datetime

# ---- CORE SYSTEM GATEWAY SETTINGS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "SHAYAN_EXPLORER"

# Shared memory pool for real-time request tracking across browser sessions
SYSTEM_LIVE_LOGS = []

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
    global SYSTEM_LIVE_LOGS
    
    if scope['type'] != 'http':
        return

    path = scope['path']
    query_string = scope.get('query_string', b'').decode('utf-8')
    params = parse_query_string(query_string)

    # ====================================================
    # 1. LIVE API GATEWAY PROXY INTERFACES
    # ====================================================
    if path.startswith("/api/"):
        endpoint = path.replace("/api/", "", 1)
        client_key = params.get("key")
        
        # Pull dynamic validation metrics securely passed from the client UI storage layer
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
            await send_json(send, {"error": "API query limitations exhausted."}, 429)
            return

        # Validate Modular Target Scopes
        if allowed_tools != "all":
            allowed_list = [t.strip().lower() for t in allowed_tools.split(",")]
            if endpoint.lower() not in allowed_list:
                await send_json(send, {"error": f"Access denied. This key is restricted to: {allowed_tools}"}, 403)
                return

        # Strip architecture arguments before routing payload downstream
        cleaned_params = {k: v for k, v in params.items() if k not in ["key", "client_name", "key_limit", "key_used", "key_expires", "key_tools"]}
        
        # Inject log packet
        SYSTEM_LIVE_LOGS.insert(0, {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })

        # Forward downstream request
        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(upstream_url, params=cleaned_params, timeout=12.0)
                await send_json(send, response.json(), response.status_code)
                return
            except Exception as e:
                await send_json(send, {"error": "Target infrastructure connection timeout", "details": str(e)}, 502)
                return

    # ====================================================
    # 2. LOG ENGINE MONITOR TELEMETRY ENDPOINT
    # ====================================================
    elif path == "/admin/logs":
        await send_json(send, {"logs": SYSTEM_LIVE_LOGS[:30]})
        return

    # ====================================================
    # 3. HIGH-END PREMIUM DASHBOARD INTERFACE UI (/)
    # ====================================================
    elif path == "/":
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Nexus Hub | {DEVELOPER_NAME}</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background-color: #05070f; 
                    color: #e2e8f0; 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    -webkit-font-smoothing: antialiased;
                }}
                .crypto-panel {{ 
                    background: #0b0f19; 
                    border: 1px solid #1e293b; 
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
                }}
                .neon-glow-text {{ 
                    text-shadow: 0 0 10px rgba(59, 130, 246, 0.5); 
                }}
                .tool-btn {{
                    background: #111827;
                    border: 1px solid #374151;
                    transition: all 0.2s ease;
                }}
                .tool-btn.active {{
                    background: rgba(59, 130, 246, 0.15);
                    border-color: #3b82f6;
                    color: #60a5fa;
                    box-shadow: 0 0 12px rgba(59, 130, 246, 0.2);
                }}
                /* Custom Checkbox for API Scopes */
                .api-checkbox:checked + label {{
                    background: rgba(59, 130, 246, 0.15);
                    border-color: #3b82f6;
                    color: #60a5fa;
                }}
                /* Clean custom scrollbars */
                ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
                ::-webkit-scrollbar-track {{ background: #05070f; }}
                ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 3px; }}
            </style>
        </head>
        <body class="p-3 sm:p-6 min-h-screen">

            <div class="max-w-7xl mx-auto space-y-6">
                <!-- System Status Header -->
                <header class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-800 pb-4 gap-4">
                    <div>
                        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-blue-500 neon-glow-text">NEXUS INFRASTRUCTURE CONTROL</h1>
                        <p class="text-xs text-gray-400 font-mono mt-0.5">OPERATOR ID: {DEVELOPER_NAME}</p>
                    </div>
                    <div class="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end">
                        <button onclick="toggleCleanReconDisplay()" class="text-xs bg-gray-900 hover:bg-gray-800 border border-gray-700 text-gray-300 font-medium px-3 py-2 rounded-lg transition active:scale-95">
                            👁️ REVEAL NO-KEY VALUES
                        </button>
                        <span class="text-[10px] sm:text-xs font-bold tracking-widest bg-blue-950 text-blue-400 px-3 py-1.5 rounded-md border border-blue-800">STATE_STORE_ACTIVE</span>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Provisioning Console Form Box -->
                    <div class="crypto-panel p-5 rounded-xl flex flex-col justify-between">
                        <form id="tokenGenerationForm" onsubmit="commitNewTokenToRegistry(event)" class="space-y-4 text-xs">
                            <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase border-b border-gray-800 pb-2">PROVISION AUTH KEY</h2>
                            
                            <div>
                                <label class="block text-gray-400 font-medium mb-1">CLIENT NAME</label>
                                <input type="text" id="inputClientName" placeholder="e.g. Premium User A" required class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500 transition">
                            </div>
                            <div>
                                <label class="block text-gray-400 font-medium mb-1">CUSTOM ACCESS LICENSE KEY</label>
                                <div class="flex gap-2">
                                    <input type="text" id="inputLicenseKey" placeholder="e.g. CUSTOM-SHAYAN-77" required class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-yellow-500 font-mono focus:outline-none focus:border-blue-500 transition">
                                    <button type="button" onclick="triggerKeyGen()" class="bg-gray-800 border border-gray-700 hover:bg-gray-700 text-white px-3 rounded-lg font-mono">GEN</button>
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-gray-400 font-medium mb-1">MAX LIMIT</label>
                                    <input type="number" id="inputQuotaLimit" value="1000" required class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500 transition">
                                </div>
                                <div>
                                    <label class="block text-gray-400 font-medium mb-1">EXPIRATION TIMESTAMP</label>
                                    <input type="datetime-local" id="inputExpiryFrame" required class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500 transition">
                                </div>
                            </div>

                            <!-- Target Component Select Grid Matrices -->
                            <div>
                                <label class="block text-gray-400 font-medium mb-1.5 tracking-wider uppercase text-[10px]">AUTHORIZED SCOPE ROUTING LIMITATION</label>
                                <div class="grid grid-cols-2 gap-1.5">
                                    <div class="relative">
                                        <input type="checkbox" id="scope_all" value="all" checked onchange="handleAllScopeToggle(this)" class="hidden api-checkbox">
                                        <label for="scope_all" class="block text-center p-2 rounded-md tool-btn cursor-pointer font-medium text-gray-300">⭐ Select All APIs</label>
                                    </div>
                                    <div class="relative">
                                        <input type="checkbox" id="scope_truecaller" value="truecaller" class="hidden api-checkbox individual-scope">
                                        <label for="scope_truecaller" class="block text-center p-2 rounded-md tool-btn cursor-pointer font-medium text-gray-300">📱 Truecaller</label>
                                    </div>
                                    <div class="relative">
                                        <input type="checkbox" id="scope_whatsapp" value="whatsapp" class="hidden api-checkbox individual-scope">
                                        <label for="scope_whatsapp" class="block text-center p-2 rounded-md tool-btn cursor-pointer font-medium text-gray-300">💬 WhatsApp</label>
                                    </div>
                                    <div class="relative">
                                        <input type="checkbox" id="scope_instagram" value="instagram" class="hidden api-checkbox individual-scope">
                                        <label for="scope_instagram" class="block text-center p-2 rounded-md tool-btn cursor-pointer font-medium text-gray-300">📸 Instagram</label>
                                    </div>
                                    <div class="relative">
                                        <input type="checkbox" id="scope_scraper" value="scraper" class="hidden api-checkbox individual-scope">
                                        <label for="scope_scraper" class="block text-center p-2 rounded-md tool-btn cursor-pointer font-medium text-gray-300">🌐 Web Scraper</label>
                                    </div>
                                    <div class="relative">
                                        <input type="checkbox" id="scope_lookup" value="lookup" class="hidden api-checkbox individual-scope">
                                        <label for="scope_lookup" class="block text-center p-2 rounded-md tool-btn cursor-pointer font-medium text-gray-300">🔍 OSINT Engine</label>
                                    </div>
                                </div>
                            </div>

                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg tracking-widest uppercase shadow transition active:scale-98">INJECT REGISTRY KEY</button>
                        </form>
                    </div>

                    <!-- Database Matrix View Table Panel Grid -->
                    <div class="lg:col-span-2 crypto-panel p-5 rounded-xl flex flex-col justify-between overflow-hidden">
                        <div class="w-full">
                            <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase border-b border-gray-800 pb-2 mb-3">ACTIVE ENGINE REGISTRIES</h2>
                            <div class="overflow-x-auto w-full">
                                <table class="w-full text-left text-xs min-w-[550px]">
                                    <thead>
                                        <tr class="border-b border-gray-800 text-gray-500 font-mono tracking-wider">
                                            <th class="pb-2">CLIENT NAME</th>
                                            <th class="pb-2">TOKEN ACCESS KEY</th>
                                            <th class="pb-2">USAGE STATUS</th>
                                            <th class="pb-2">EXPIRATION WINDOW</th>
                                            <th class="pb-2">SCOPE</th>
                                            <th class="pb-2 text-right">MGMT</th>
                                        </tr>
                                    </thead>
                                    <tbody id="registryTableElementRows" class="divide-y divide-gray-950">
                                        <!-- Controlled Dynamically via JavaScript Layer Runloop -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sandbox Testing Playground Workspace Terminal Box -->
                <div class="crypto-panel p-5 rounded-xl space-y-4">
                    <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase border-b border-gray-800 pb-2">SANDBOX INTERACTIVE ROUTER DESK</h2>
                    
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
                        <button type="button" onclick="bindSandboxTarget(this, 'truecaller')" class="p-3 rounded-lg tool-btn active text-center font-medium">📱 Truecaller</button>
                        <button type="button" onclick="bindSandboxTarget(this, 'whatsapp')" class="p-3 rounded-lg tool-btn text-center font-medium">💬 WhatsApp</button>
                        <button type="button" onclick="bindSandboxTarget(this, 'instagram')" class="p-3 rounded-lg tool-btn text-center font-medium">📸 Instagram</button>
                        <button type="button" onclick="bindSandboxTarget(this, 'scraper')" class="p-3 rounded-lg tool-btn text-center font-medium">🌐 Web Scraper</button>
                        <button type="button" onclick="bindSandboxTarget(this, 'lookup')" class="p-3 rounded-lg tool-btn text-center font-medium">🔍 OSINT Engine</button>
                        <button type="button" onclick="bindSandboxTarget(this, 'bypass')" class="p-3 rounded-lg tool-btn text-center font-medium">🔓 System Bypass</button>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs items-end">
                        <div>
                            <label class="block text-gray-500 font-medium mb-1">ACTIVE TARGET PATH</label>
                            <input type="text" id="targetSandboxPathField" value="truecaller" class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 font-mono text-gray-400" readonly>
                        </div>
                        <div>
                            <label class="block text-gray-500 font-medium mb-1">VERIFICATION TOKEN KEY</label>
                            <input type="text" id="targetSandboxKeyField" placeholder="Click any key value from your registry table to fill instantly..." class="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 font-mono text-yellow-500 focus:outline-none">
                        </div>
                        <button onclick="executeSandboxProbeRequest()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg tracking-wider uppercase transition active:scale-98">FIRE VERIFICATION PACKET</button>
                    </div>
                    <div id="sandboxResponseTerminal" class="hidden p-4 bg-black border border-gray-900 rounded-lg font-mono text-xs text-green-400 overflow-x-auto whitespace-pre-wrap"></div>
                </div>

                <!-- Live Query Streams Inspector Panel Box -->
                <div class="crypto-panel p-5 rounded-xl">
                    <div class="flex justify-between items-center border-b border-gray-800 pb-2 mb-3">
                        <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase">LIVE NETWORK PACKET INSPECTOR</h2>
                        <button onclick="syncTelemetryLogsFeed()" class="text-[10px] bg-gray-950 hover:bg-gray-900 border border-gray-800 px-3 py-1 rounded-md text-gray-400">SYNC FEED</button>
                    </div>
                    <div class="overflow-x-auto max-h-56 text-xs font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-gray-500 border-b border-gray-900">
                                    <th class="pb-1">TIMESTAMP</th>
                                    <th class="pb-1">KEY_REF</th>
                                    <th class="pb-1">RESOURCE COMPONENT</th>
                                    <th class="pb-1">METADATA PARAMS</th>
                                </tr>
                            </thead>
                            <tbody id="telemetryPacketStreamBodyRows" class="divide-y divide-gray-950">
                                <tr><td colspan="4" class="py-4 text-center text-gray-600">Awaiting runtime socket sync...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- EMBEDDED DYNAMIC PERSISTENCE LAYER CONTROLS SCRIPT -->
            <script>
                let maskStateActive = false;
                const defaultTimeLockISO = "2027-12-31T23:59";
                document.getElementById('inputExpiryFrame').value = defaultTimeLockISO;

                // Validate storage persistence layers on page runtime sequence loading
                if (!localStorage.getItem('NEXUS_REGISTRIES_DATABASE')) {{
                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify({{
                        "VIP-SHAYAN": {{
                            name: "Root Master Account",
                            limit: 5000,
                            used: 0,
                            expires_at: "2027-12-31 23:59:59",
                            allowed_tools: "all"
                        }}
                    }}));
                }}

                function handleAllScopeToggle(masterCheckbox) {{
                    const individualBoxes = document.querySelectorAll('.individual-scope');
                    individualBoxes.forEach(box => {{
                        box.checked = false;
                        if(masterCheckbox.checked) box.disabled = true;
                        else box.disabled = false;
                    }});
                }}

                function compileSelectedScopesString() {{
                    if(document.getElementById('scope_all').checked) return "all";
                    let checkedScopes = [];
                    const individualBoxes = document.querySelectorAll('.individual-scope');
                    individualBoxes.forEach(box => {{
                        if(box.checked) checkedScopes.push(box.value);
                    }});
                    return checkedScopes.length > 0 ? checkedScopes.join(', ') : "all";
                }}

                function loadRegistriesViewTableMatrix() {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const targetBody = document.getElementById('registryTableElementRows');
                    targetBody.innerHTML = '';

                    if(Object.keys(db).length === 0) {{
                        targetBody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-gray-600">No records allocated inside device storage database matrix.</td></tr>`;
                        return;
                    }}

                    for(const [key, profile] of Object.entries(db)) {{
                        const renderedKey = maskStateActive ? '••••••••••••' : key;
                        const clickActionString = maskStateActive ? `"${{profile.name}} [Scope: ${{profile.allowed_tools}}] Quota: ${{profile.used}}/${{profile.limit}}"` : `"${{key}}"`;
                        
                        targetBody.innerHTML += `
                            <tr class="hover:bg-gray-950 transition-colors">
                                <td class="py-3 text-white font-semibold tracking-wide">${{profile.name}}</td>
                                <td class="py-3 font-mono">
                                    <span class="text-yellow-500 cursor-pointer hover:underline" onclick='executeGlobalClipboardInject(${{clickActionString}})' title="Click to instantly copy or select to input field">${{renderedKey}}</span>
                                </td>
                                <td class="py-3 font-mono text-gray-300">${{profile.used}} / ${{profile.limit}}</td>
                                <td class="py-3 text-gray-400 font-sans text-xs">${{profile.expires_at}}</td>
                                <td class="py-3 text-blue-400 font-mono text-[11px]">${{profile.allowed_tools}}</td>
                                <td class="py-3 text-right">
                                    <button onclick="purgeKeyFromStorage('${{key}}')" class="text-red-500 hover:text-red-400 font-bold transition">REVOKE</button>
                                </td>
                            </tr>
                        `;
                    }}
                }}

                function commitNewTokenToRegistry(e) {{
                    e.preventDefault();
                    const name = document.getElementById('inputClientName').value;
                    const key = document.getElementById('inputLicenseKey').value.trim();
                    const limit = parseInt(document.getElementById('inputQuotaLimit').value);
                    let expiryISO = document.getElementById('inputExpiryFrame').value.replace('T', ' ');
                    if(expiryISO.length === 16) expiryISO += ":00";
                    
                    const compiledScopes = compileSelectedScopesString();
                    const activeDb = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    
                    activeDb[key] = {{
                        name: name,
                        limit: limit,
                        used: 0,
                        expires_at: expiryISO,
                        allowed_tools: compiledScopes
                    }};

                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(activeDb));
                    document.getElementById('tokenGenerationForm').reset();
                    document.getElementById('inputExpiryFrame').value = defaultTimeLockISO;
                    document.getElementById('scope_all').checked = true;
                    handleAllScopeToggle(document.getElementById('scope_all'));
                    
                    loadRegistriesViewTableMatrix();
                }}

                function purgeKeyFromStorage(key) {{
                    const activeDb = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(activeDb[key]) {{
                        delete activeDb[key];
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(activeDb));
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                function toggleCleanReconDisplay() {{
                    maskStateActive = !maskStateActive;
                    loadRegistriesViewTableMatrix();
                }}

                function executeGlobalClipboardInject(text) {{
                    // Auto-fill active test terminal key input field to maximize UX fluidity
                    if(!maskStateActive) {{
                        document.getElementById('targetSandboxKeyField').value = text;
                    }}
                    navigator.clipboard.writeText(text).then(() => {{
                        alert("Dispatched to system clipboard buffer:\\n" + text);
                    }}).catch(() => {{}});
                }}

                function bindSandboxTarget(btnElement, pathName) {{
                    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                    btnElement.classList.add('active');
                    document.getElementById('targetSandboxPathField').value = pathName;
                }}

                function triggerKeyGen() {{
                    const generatedToken = "NX-" + Math.random().toString(36).substring(2, 7).toUpperCase() + "-" + Math.random().toString(36).substring(2, 7).toUpperCase();
                    document.getElementById('inputLicenseKey').value = generatedToken;
                }}

                async function executeSandboxProbeRequest() {{
                    const endpoint = document.getElementById('targetSandboxPathField').value;
                    const key = document.getElementById('targetSandboxKeyField').value.trim();
                    const terminalDisplay = document.getElementById('sandboxResponseTerminal');

                    if(!key) {{
                        alert("Provide or select an active verification registry license token first.");
                        return;
                    }}

                    const clientStorageMatrix = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const contextProfile = clientStorageMatrix[key] || {{ name: "Admin Handshake", limit: 1000, used: 0, expires_at: "2027-12-31 23:59:59", allowed_tools: "all" }};

                    terminalDisplay.classList.remove('hidden');
                    terminalDisplay.innerText = "Transmitting framework proxy packet trace downstream...";

                    const connectionUrl = `/api/${{endpoint}}?key=${{encodeURIComponent(key)}}&client_name=${{encodeURIComponent(contextProfile.name)}}&key_limit=${{contextProfile.limit}}&key_used=${{contextProfile.used}}&key_expires=${{encodeURIComponent(contextProfile.expires_at)}}&key_tools=${{encodeURIComponent(contextProfile.allowed_tools)}}&lookup_probe=test`;

                    try {{
                        const res = await fetch(connectionUrl);
                        const responsePayload = await res.json();
                        
                        if(res.ok) {{
                            if(clientStorageMatrix[key]) {{
                                clientStorageMatrix[key].used += 1;
                                localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(clientStorageMatrix));
                                loadRegistriesViewTableMatrix();
                            }}
                        }}
                        terminalDisplay.innerText = JSON.stringify(responsePayload, null, 4);
                    }} catch (err) {{
                        terminalDisplay.innerText = "Network Gateway Intercept Error: " + err.toString();
                    }}
                    syncTelemetryLogsFeed();
                }}

                async function syncTelemetryLogsFeed() {{
                    try {{
                        const response = await fetch('/admin/logs');
                        const data = await response.json();
                        const logsTbody = document.getElementById('telemetryPacketStreamBodyRows');
                        logsTbody.innerHTML = '';

                        if(!data.logs || data.logs.length === 0) {{
                            logsTbody.innerHTML = `<tr><td colspan="4" class="py-3 text-center text-gray-600">No logs captured.</td></tr>`;
                            return;
                        }}

                        data.logs.forEach(log => {{
                            logsTbody.innerHTML += `
                                <tr class="border-b border-gray-950 hover:bg-gray-950 transition-colors">
                                    <td class="py-2 text-gray-500">${{log.timestamp}}</td>
                                    <td class="py-2 text-yellow-600 font-bold">${{log.key}}</td>
                                    <td class="py-2 text-green-400">/api/${{log.endpoint}}</td>
                                    <td class="py-2 text-gray-400 font-sans bg-gray-900 bg-opacity-30 px-2 rounded">${{log.params}}</td>
                                </tr>
                            `;
                        }});
                    }} catch(e) {{}}
                }}

                window.onload = function() {{
                    loadRegistriesViewTableMatrix();
                    handleAllScopeToggle(document.getElementById('scope_all'));
                    syncTelemetryLogsFeed();
                    setInterval(syncTelemetryLogsFeed, 10000);
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
