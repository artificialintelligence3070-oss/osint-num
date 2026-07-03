import os
import httpx
import json
import urllib.parse
from datetime import datetime

# ---- CORE SYSTEM GATEWAY SETTINGS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "@vernexzz"
CHANNEL_URL = "https://t.me/shayan_explorer_channel"

# Shared telemetry data logger across session cycles
SYSTEM_LIVE_LOGS = []

# Complete verified list of all 28 core system-integrated API routes
CORE_API_ENDPOINTS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", "number", 
    "pincode", "ip", "challan", "ff", "bgmi", "snap", "email", 
    "vehicle", "git", "insta", "tg", "tgidinfo", "numleak", "pk", 
    "name", "aadhar", "numtoupi", "pan", "veh2num", "adharfamily", "bomber"
]

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
    # 1. LIVE API PROXY GATEWAY ROUTER INTERFACES
    # ====================================================
    if path.startswith("/api/"):
        endpoint = path.replace("/api/", "", 1)
        client_key = params.get("key")
        
        # Pull isolation filters passed down from client configuration store
        client_name = urllib.parse.unquote(params.get("client_name", "External Node"))
        key_limit = int(params.get("key_limit", 1000))
        key_used = int(params.get("key_used", 0))
        key_expiry = urllib.parse.unquote(params.get("key_expires", "2027-12-31 23:59:59"))
        allowed_tools = urllib.parse.unquote(params.get("key_tools", "all"))

        if not client_key:
            await send_json(send, {"error": "Missing client authorization identifier token."}, 403)
            return

        # Check Expiration Frame
        try:
            if datetime.utcnow() > datetime.strptime(key_expiry, "%Y-%m-%d %H:%M:%S"):
                await send_json(send, {"error": "Allocated key window timeline has expired."}, 403)
                return
        except Exception:
            pass

        # Check Total Quota Limits
        if key_used >= key_limit:
            await send_json(send, {"error": "API token quota usage limit exceeded."}, 429)
            return

        # Validate Allowed Scopes
        if allowed_tools != "all":
            allowed_list = [t.strip().lower() for t in allowed_tools.split(",")]
            if endpoint.lower() not in allowed_list:
                await send_json(send, {"error": f"Access Denied. Endpoint restriction active. Allowed: {allowed_tools}"}, 403)
                return

        # Core query params scrubbed of old default dev parameters and internal proxy blocks
        cleaned_params = {}
        for k, v in params.items():
            if k not in ["key", "client_name", "key_limit", "key_used", "key_expires", "key_tools"]:
                # Force replace legacy credentials if mistakenly requested by external callers
                if "ftgamer" in str(v).lower() or "bronex" in str(v).lower():
                    cleaned_params[k] = "vernexzz"
                else:
                    cleaned_params[k] = v
        
        # Log this payload execution trace line
        SYSTEM_LIVE_LOGS.insert(0, {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })

        # Inject Master Upstream Key
        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(upstream_url, params=cleaned_params, timeout=12.0)
                await send_json(send, response.json(), response.status_code)
                return
            except Exception as e:
                await send_json(send, {"error": "Target engine cluster connection timeout", "details": str(e)}, 502)
                return

    # ====================================================
    # 2. TELEMETRY LOG DATA ACCESS ENDPOINT
    # ====================================================
    elif path == "/admin/logs":
        await send_json(send, {"logs": SYSTEM_LIVE_LOGS[:30]})
        return

    # ====================================================
    # 3. INTERFACE RENDERING ENGINE (/)
    # ====================================================
    elif path == "/":
        endpoints_json = json.dumps(CORE_API_ENDPOINTS)
        
        # Dynamically generate key scope checkboxes
        checkbox_grid_html = ""
        for tool in CORE_API_ENDPOINTS:
            checkbox_grid_html += f"""
            <div class="relative">
                <input type="checkbox" id="scope_{tool}" value="{tool}" class="hidden api-checkbox individual-scope">
                <label for="scope_{tool}" class="block text-center p-2 rounded-lg tool-btn cursor-pointer font-medium border border-gray-800 text-gray-400 bg-gray-900 transition text-[11px] uppercase">
                    {tool}
                </label>
            </div>
            """

        # Dynamically generate interactable sandbox buttons
        sandbox_grid_html = ""
        for idx, tool in enumerate(CORE_API_ENDPOINTS):
            active_class = "active" if idx == 0 else ""
            sandbox_grid_html += f"""
            <button type="button" onclick="bindSandboxTarget(this, '{tool}')" class="p-2.5 rounded-lg tool-btn text-center font-mono text-[11px] uppercase tracking-wider text-gray-400 {active_class}">
                {tool}
            </button>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Nexus Panel Matrix | {DEVELOPER_NAME}</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background-color: #030712; 
                    color: #f1f5f9; 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif;
                }}
                .crypto-panel {{ 
                    background: #090d16; 
                    border: 1px solid #1e293b; 
                }}
                
                /* FIX: Complete removal of white fields and light browser defaults */
                input[type="text"], input[type="number"], input[type="datetime-local"] {{
                    background-color: #020617 !important;
                    color: #ffffff !important;
                    border: 1px solid #1e293b !important;
                    outline: none !important;
                }}
                input[type="text"]:focus, input[type="number"]:focus, input[type="datetime-local"]:focus {{
                    border-color: #3b82f6 !important;
                    box-shadow: 0 0 8px rgba(59, 130, 246, 0.3) !important;
                }}
                
                .tool-btn {{
                    background: #020617;
                    border: 1px solid #1e293b;
                }}
                .tool-btn.active {{
                    background: rgba(59, 130, 246, 0.15) !important;
                    border-color: #3b82f6 !important;
                    color: #60a5fa !important;
                }}
                .api-checkbox:checked + label {{
                    background: rgba(59, 130, 246, 0.15) !important;
                    border-color: #3b82f6 !important;
                    color: #60a5fa !important;
                }}
                ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
                ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 4px; }}
            </style>
        </head>
        <body class="p-3 sm:p-5 min-h-screen">

            <div class="max-w-7xl mx-auto space-y-5">
                <!-- Header Component with Authorized Branding Links -->
                <header class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-800 pb-4 gap-4">
                    <div>
                        <h1 class="text-lg md:text-xl font-bold tracking-wider text-blue-500 uppercase">OSINT GATEWAY MONITOR</h1>
                        <div class="flex items-center gap-2 mt-1 text-xs text-gray-400 font-mono">
                            <span>OWNER MASTER:</span>
                            <a href="{CHANNEL_URL}" target="_blank" class="text-blue-400 hover:underline font-bold font-mono text-sm tracking-wide">{DEVELOPER_NAME}</a>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 w-full md:w-auto justify-between md:justify-end">
                        <button onclick="toggleKeyMaskingState()" class="text-xs bg-gray-900 hover:bg-gray-800 border border-gray-700 text-gray-300 font-medium px-3 py-2 rounded-lg transition">
                            👁️ MASK/UNMASK KEYS
                        </button>
                        <span class="text-xs font-bold font-mono tracking-wider bg-blue-950 text-blue-400 px-3 py-1.5 rounded-lg border border-blue-900">CORE_ONLINE</span>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
                    <!-- Dynamic Provisioning Terminal Block -->
                    <div class="crypto-panel p-4 rounded-xl">
                        <form id="tokenGenerationForm" onsubmit="commitNewTokenToRegistry(event)" class="space-y-4 text-xs">
                            <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase border-b border-gray-800 pb-2">PROVISION RECON LINK KEY</h2>
                            
                            <div>
                                <label class="block text-gray-400 font-medium mb-1">CLIENT ASSIGNMENT NAME</label>
                                <input type="text" id="inputClientName" placeholder="Username / ID Reference" required class="w-full rounded-lg p-2.5 text-white">
                            </div>
                            <div>
                                <label class="block text-gray-400 font-medium mb-1">CUSTOM KEY STRING</label>
                                <div class="flex gap-2">
                                    <input type="text" id="inputLicenseKey" placeholder="e.g. CUSTOM-VX-TOKEN" required class="w-full rounded-lg p-2.5 text-yellow-500 font-mono">
                                    <button type="button" onclick="triggerKeyGen()" class="bg-gray-800 border border-gray-700 hover:bg-gray-700 text-white px-3 rounded-lg font-mono">AUTO</button>
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-gray-400 font-medium mb-1">CALL QUOTA CAP</label>
                                    <input type="number" id="inputQuotaLimit" value="2500" required class="w-full rounded-lg p-2.5 text-white">
                                </div>
                                <div>
                                    <label class="block text-gray-400 font-medium mb-1">TIME EXPIRATION LOCK</label>
                                    <input type="datetime-local" id="inputExpiryFrame" required class="w-full rounded-lg p-2.5 text-white">
                                </div>
                            </div>

                            <div>
                                <label class="block text-gray-400 font-medium mb-1.5 uppercase tracking-wider text-[10px]">ROUTE SCOPE MATRIX ALLOCATION</label>
                                <div class="max-h-44 overflow-y-auto border border-gray-800 p-2 rounded-lg bg-black bg-opacity-40 space-y-2">
                                    <div class="relative">
                                        <input type="checkbox" id="scope_all" value="all" checked onchange="handleAllScopeToggle(this)" class="hidden api-checkbox">
                                        <label for="scope_all" class="block text-center p-2 rounded-lg tool-btn cursor-pointer font-bold border border-blue-900 text-blue-400 bg-gray-900 text-[11px] uppercase">
                                            ⭐ UNRESTRICTED SYSTEM ACCESS (ALL ENDPOINTS)
                                        </label>
                                    </div>
                                    <div class="grid grid-cols-2 gap-1.5">
                                        {checkbox_grid_html}
                                    </div>
                                </div>
                            </div>

                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg tracking-widest uppercase transition">INJECT ROUTE REGISTRY</button>
                        </form>
                    </div>

                    <!-- Client Active Data Grid Table Layout -->
                    <div class="lg:col-span-2 crypto-panel p-4 rounded-xl overflow-hidden">
                        <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase border-b border-gray-800 pb-2 mb-2.5">ACTIVE ROUTING DATABASE</h2>
                        <div class="overflow-x-auto w-full">
                            <table class="w-full text-left text-xs min-w-[580px]">
                                <thead>
                                    <tr class="border-b border-gray-800 text-gray-500 font-mono">
                                        <th class="pb-2">CLIENT DESIGNATION</th>
                                        <th class="pb-2">SECRET ROUTE TOKEN</th>
                                        <th class="pb-2">QUOTA PROG</th>
                                        <th class="pb-2">TIME BLOCK EXPIRES</th>
                                        <th class="pb-2">BOUND RECON MODULES</th>
                                        <th class="pb-2 text-right">ACTION</th>
                                    </tr>
                                </thead>
                                <tbody id="registryTableElementRows" class="divide-y divide-gray-950">
                                    <!-- Populated via system runtime JS storage hook -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- FIX: Fully Repaired & Responsive Interactive Sandbox Desk Workspace -->
                <div class="crypto-panel p-4 rounded-xl space-y-3.5">
                    <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase border-b border-gray-800 pb-2">INTERACTIVE SANDBOX matrix DESK</h2>
                    
                    <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-7 lg:grid-cols-10 gap-1.5 text-xs">
                        {sandbox_grid_html}
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs items-end">
                        <div>
                            <label class="block text-gray-500 font-medium mb-1">TARGET ROUTER ENDPOINT ROUTE</label>
                            <div class="flex items-center bg-gray-950 rounded-lg border border-gray-800 font-mono text-gray-300 p-2.5">
                                <span class="text-gray-600 pr-1">/api/</span>
                                <input type="text" id="targetSandboxPathField" value="adv" class="w-full bg-transparent border-none text-white focus:ring-0 p-0 m-0 font-mono" readonly style="background-color:transparent !important; border:none !important; box-shadow:none !important;">
                            </div>
                        </div>
                        <div>
                            <label class="block text-gray-500 font-medium mb-1">ACTIVE TEST AUTH KEY INJECTOR</label>
                            <input type="text" id="targetSandboxKeyField" placeholder="Select or type registry token key here..." class="w-full rounded-lg p-2.5 font-mono text-yellow-500">
                        </div>
                        <button onclick="executeSandboxProbeRequest()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg tracking-wider uppercase transition">FIRE ENDPOINT PROBE</button>
                    </div>
                    
                    <!-- Fixed Target Output Window Container UI Layout -->
                    <div id="sandboxResponseTerminal" class="hidden p-4 bg-black border border-gray-900 rounded-lg font-mono text-xs text-green-400 overflow-x-auto whitespace-pre-wrap max-h-96"></div>
                </div>

                <!-- Network Telemetry Activity Tracker Monitor Engine Row -->
                <div class="crypto-panel p-4 rounded-xl">
                    <div class="flex justify-between items-center border-b border-gray-800 pb-2 mb-2.5">
                        <h2 class="text-xs font-bold tracking-wider text-gray-400 uppercase">LIVE SYSTEM TRANSACTION TRACKING PACKETS</h2>
                        <button onclick="syncTelemetryLogsFeed()" class="text-[10px] bg-gray-950 border border-gray-800 px-2.5 py-1 rounded-md text-gray-400 hover:text-white">FORCE SYNC</button>
                    </div>
                    <div class="overflow-x-auto max-h-48 text-xs font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-gray-500 border-b border-gray-900">
                                    <th class="pb-1">TIMESTAMP UTC</th>
                                    <th class="pb-1">CLIENT ACCESS KEY</th>
                                    <th class="pb-1">ROUTED TARGET</th>
                                    <th class="pb-1">CLEANED PARAMETERS MATRIX</th>
                                </tr>
                            </thead>
                            <tbody id="telemetryPacketStreamBodyRows" class="divide-y divide-gray-950">
                                <tr><td colspan="4" class="py-4 text-center text-gray-600">Awaiting stream execution sequence data threads...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- JAVASCRIPT APP MATRIX CONTROLLERS -->
            <script>
                let maskStateActive = false;
                const defaultTimeLockISO = "2027-12-31T23:59";
                document.getElementById('inputExpiryFrame').value = defaultTimeLockISO;

                // Instantiate operational fallback node credentials if clear
                if (!localStorage.getItem('NEXUS_REGISTRIES_DATABASE')) {{
                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify({{
                        "VX-MASTER-KEY": {{
                            name: "Root Master Hub",
                            limit: 99999,
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
                        box.disabled = masterCheckbox.checked;
                    }});
                }}

                function compileSelectedScopesString() {{
                    if(document.getElementById('scope_all').checked) return "all";
                    let checkedScopes = [];
                    document.querySelectorAll('.individual-scope').forEach(box => {{
                        if(box.checked) checkedScopes.push(box.value);
                    }});
                    return checkedScopes.length > 0 ? checkedScopes.join(', ') : "all";
                }}

                function loadRegistriesViewTableMatrix() {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const targetBody = document.getElementById('registryTableElementRows');
                    targetBody.innerHTML = '';

                    if(Object.keys(db).length === 0) {{
                        targetBody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-gray-600">No client profiles cataloged in active memory registers.</td></tr>`;
                        return;
                    }}

                    for(const [key, profile] of Object.entries(db)) {{
                        const renderedKey = maskStateActive ? '••••••••••••••••' : key;
                        
                        targetBody.innerHTML += `
                            <tr class="hover:bg-gray-950 transition-colors">
                                <td class="py-2.5 text-white font-semibold">${{profile.name}}</td>
                                <td class="py-2.5 font-mono">
                                    <span class="text-yellow-500 cursor-pointer hover:underline" onclick="injectKeyToSandbox('${{key}}')" title="Click to instantly inject to test verification engine">${{renderedKey}}</span>
                                </td>
                                <td class="py-2.5 font-mono text-gray-300">${{profile.used}} / ${{profile.limit}}</td>
                                <td class="py-2.5 text-gray-400 font-mono text-[11px]">${{profile.expires_at}}</td>
                                <td class="py-2.5 text-blue-400 font-mono text-[11px] max-w-xs truncate" title="${{profile.allowed_tools}}">${{profile.allowed_tools}}</td>
                                <td class="py-2.5 text-right">
                                    <button onclick="purgeKeyFromStorage('${{key}}')" class="text-red-500 hover:text-red-400 font-bold">REVOKE</button>
                                </td>
                            </tr>
                        `;
                    }}
                }}

                function injectKeyToSandbox(key) {{
                    document.getElementById('targetSandboxKeyField').value = key;
                    alert("Token structural key value successfully assigned to sandbox field input router node.");
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

                function toggleKeyMaskingState() {{
                    maskStateActive = !maskStateActive;
                    loadRegistriesViewTableMatrix();
                }}

                function bindSandboxTarget(btnElement, pathName) {{
                    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                    btnElement.classList.add('active');
                    document.getElementById('targetSandboxPathField').value = pathName;
                }}

                function triggerKeyGen() {{
                    const generatedToken = "VX-" + Math.random().toString(36).substring(2, 7).toUpperCase() + "-" + Math.random().toString(36).substring(2, 7).toUpperCase();
                    document.getElementById('inputLicenseKey').value = generatedToken;
                }}

                async function executeSandboxProbeRequest() {{
                    const endpoint = document.getElementById('targetSandboxPathField').value;
                    const key = document.getElementById('targetSandboxKeyField').value.trim();
                    const terminalDisplay = document.getElementById('sandboxResponseTerminal');

                    if(!key) {{
                        alert("Configure or inject an authorization registry record key line item before routing live checks.");
                        return;
                    }}

                    const clientStorageMatrix = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const contextProfile = clientStorageMatrix[key] || {{ name: "Adhoc Probe Exec", limit: 1000, used: 0, expires_at: "2027-12-31 23:59:59", allowed_tools: "all" }};

                    terminalDisplay.classList.remove('hidden');
                    terminalDisplay.innerText = "Transmitting secure connection payload matrix frames downstream...";

                    // Standard dynamic playground argument injection mapping
                    const baseParams = `?key=${{encodeURIComponent(key)}}&client_name=${{encodeURIComponent(contextProfile.name)}}&key_limit=${{contextProfile.limit}}&key_used=${{contextProfile.used}}&key_expires=${{encodeURIComponent(contextProfile.expires_at)}}&key_tools=${{encodeURIComponent(contextProfile.allowed_tools)}}`;
                    const operationalQueryMock = `&num=9876543210&upi=example@ybl&ifsc=SBIN0001234&pin=110001&ip=8.8.8.8&vehicle=UP42BB2572&uid=3143389983&username=priyapanchal272&email=airtel123@gmail.com&imei=357817383506298&info=username&id=7530266953&name=abhiraaj&pan=AXDPR2606K&counter=5`;

                    const completeTargetUrl = `/api/${{endpoint}}${{baseParams}}${{operationalQueryMock}}`;

                    try {{
                        const res = await fetch(completeTargetUrl);
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
                        terminalDisplay.innerText = "Proxy Connection Error (Check terminal deployment console logs): " + err.toString();
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
                            logsTbody.innerHTML = `<tr><td colspan="4" class="py-3 text-center text-gray-600">No inbound api requests parsed through the gateway cluster stack yet.</td></tr>`;
                            return;
                        }}

                        data.logs.forEach(log => {{
                            logsTbody.innerHTML += `
                                <tr class="border-b border-gray-950 hover:bg-gray-950 transition-colors">
                                    <td class="py-2 text-gray-500">${{log.timestamp}}</td>
                                    <td class="py-2 text-yellow-600 font-bold">${{log.key}}</td>
                                    <td class="py-2 text-blue-400">/api/${{log.endpoint}}</td>
                                    <td class="py-2 text-gray-400 font-sans bg-gray-900 bg-opacity-30 px-2 rounded max-w-xs truncate" title="${{log.params}}">${{log.params}}</td>
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
        await send_json(send, {"detail": f"Route route '{path}' does not point to an active nexus core node assembly."}, 404)

async def send_json(send, data: dict, status_code: int = 200):
    body = json.dumps(data).encode('utf-8')
    await send({'type': 'http.response.start', 'status': status_code, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': body})

async def send_html(send, html_text: str):
    body = html_text.encode('utf-8')
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/html')]})
    await send({'type': 'http.response.body', 'body': body})
