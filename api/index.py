import os
import httpx
import json
import urllib.parse
from datetime import datetime, timedelta

# ---- CORE SYSTEM GATEWAY SETTINGS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "@vernexzz"
CHANNEL_URL = "https://t.me/shayan_explorer_channel"

SYSTEM_LIVE_LOGS = []

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

def scrub_legacy_branding(data):
    if isinstance(data, dict):
        for k, v in list(data.items()):
            if isinstance(v, str):
                v_lower = v.lower()
                if "ftgamer" in v_lower or "bronex" in v_lower or "lynx_api" in v_lower:
                    if k == "by":
                        data[k] = DEVELOPER_NAME
                    elif k == "channel":
                        data[k] = CHANNEL_URL
                    else:
                        data[k] = v.replace("@ftgamer2", DEVELOPER_NAME).replace("https://t.me/lynx_api", CHANNEL_URL).replace("@BronexUltra", DEVELOPER_NAME)
            else:
                scrub_legacy_branding(v)
    elif isinstance(data, list):
        for item in data:
            scrub_legacy_branding(item)
    return data

async def app(scope, receive, send):
    global SYSTEM_LIVE_LOGS
    
    if scope['type'] != 'http':
        return

    path = scope['path']
    query_string = scope.get('query_string', b'').decode('utf-8')
    params = parse_query_string(query_string)

    if path.startswith("/api/"):
        endpoint = path.replace("/api/", "", 1)
        client_key = params.get("key")
        
        # Pull parameters dynamically injected by the proxy management shell
        client_name = urllib.parse.unquote(params.get("client_name", "External Node"))
        key_limit = int(params.get("key_limit", 1000))
        key_used = int(params.get("key_used", 0))
        key_expiry = urllib.parse.unquote(params.get("key_expires", "Expired"))
        allowed_tools = urllib.parse.unquote(params.get("key_tools", "all"))
        
        # FIX: Check if the suspension flag was passed down by front-end state sync
        is_suspended = params.get("key_suspended", "false").lower() == "true"

        if not client_key:
            await send_json(send, {"error": "Missing client authorization identifier token."}, 403)
            return

        # 1. SUSPENSION ENFORCEMENT CHECK
        if is_suspended:
            await send_json(send, {"error": "Access Denied. This API key is currently suspended by the administrator."}, 403)
            return

        # 2. EXPIRY ENFORCEMENT CHECK
        if key_expiry != "Unlimited":
            try:
                if datetime.utcnow() > datetime.strptime(key_expiry, "%Y-%m-%d %H:%M:%S"):
                    await send_json(send, {"error": f"Access Denied. Your API key expired on {key_expiry} UTC."}, 403)
                    return
            except Exception:
                pass

        # 3. QUOTA ENFORCEMENT CHECK
        if key_used >= key_limit:
            await send_json(send, {"error": "API token quota usage limit exceeded. Please re-limit or upgrade your plan."}, 429)
            return

        # 4. SCOPE BOUNDS CHECK
        if allowed_tools != "all":
            allowed_list = [t.strip().lower() for t in allowed_tools.split(",")]
            if endpoint.lower() not in allowed_list:
                await send_json(send, {"error": "Access Denied. Endpoint restriction active for this key."}, 403)
                return

        cleaned_params = {}
        for k, v in params.items():
            if k not in ["key", "client_name", "key_limit", "key_used", "key_expires", "key_tools", "key_suspended"]:
                cleaned_params[k] = v
        
        SYSTEM_LIVE_LOGS.insert(0, {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })

        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(upstream_url, params=cleaned_params, timeout=12.0)
                raw_response_json = response.json()
                scrubbed_response_json = scrub_legacy_branding(raw_response_json)
                await send_json(send, scrubbed_response_json, response.status_code)
                return
            except Exception as e:
                await send_json(send, {"error": "Target backend infrastructure network timeout"}, 502)
                return

    elif path == "/admin/logs":
        await send_json(send, {"logs": SYSTEM_LIVE_LOGS[:30]})
        return

    elif path == "/":
        checkbox_grid_html = "".join([f"""
        <div class="relative">
            <input type="checkbox" id="scope_{tool}" value="{tool}" class="hidden api-checkbox individual-scope">
            <label for="scope_{tool}" class="block text-center p-2 rounded-lg tool-btn cursor-pointer font-medium border border-gray-800 text-gray-400 bg-gray-900 transition text-[11px] uppercase">
                {tool}
            </label>
        </div>
        """ for tool in CORE_API_ENDPOINTS])

        sandbox_grid_html = "".join([f"""
        <button type="button" onclick="bindSandboxTarget(this, '{tool}')" class="p-2.5 rounded-lg tool-btn text-center font-mono text-[11px] uppercase tracking-wider text-gray-400 {'active' if idx == 0 else ''}">
            {tool}
        </button>
        """ for idx, tool in enumerate(CORE_API_ENDPOINTS)])

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Nexus Advanced Panel Matrix | {DEVELOPER_NAME}</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ background-color: #030712; color: #f1f5f9; font-family: sans-serif; }}
                .crypto-panel {{ background: #090d16; border: 1px solid #1e293b; }}
                input, select {{ background-color: #020617 !important; color: #fff !important; border: 1px solid #1e293b !important; outline: none; }}
                input:focus, select:focus {{ border-color: #3b82f6 !important; }}
                .tool-btn.active {{ background: rgba(59, 130, 246, 0.15) !important; border-color: #3b82f6 !important; color: #60a5fa !important; }}
                .api-checkbox:checked + label {{ background: rgba(59, 130, 246, 0.15) !important; border-color: #3b82f6 !important; color: #60a5fa !important; }}
            </style>
        </head>
        <body class="p-3 sm:p-5 min-h-screen">
            <div class="max-w-7xl mx-auto space-y-5">
                <header class="flex justify-between items-center border-b border-gray-800 pb-4">
                    <div>
                        <h1 class="text-lg font-bold text-blue-500 tracking-wider">OSINT CONTROL GATEWAY HUB</h1>
                        <div class="text-xs text-gray-400 font-mono">OWNER MOD: <a href="{CHANNEL_URL}" class="text-blue-400 font-bold">{DEVELOPER_NAME}</a></div>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
                    <div class="crypto-panel p-4 rounded-xl">
                        <form id="tokenGenerationForm" onsubmit="commitNewTokenToRegistry(event)" class="space-y-4 text-xs">
                            <h2 class="text-xs font-bold text-gray-400 uppercase border-b border-gray-800 pb-2">PROVISION CLOUD API KEY</h2>
                            
                            <div>
                                <label class="block text-gray-400 mb-1">CLIENT ASSIGNMENT TAG</label>
                                <input type="text" id="inputClientName" placeholder="Client Name or ID" required class="w-full rounded-lg p-2.5">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1">LICENSE ROUTING KEY</label>
                                <div class="flex gap-2">
                                    <input type="text" id="inputLicenseKey" placeholder="VX-XXXXX" required class="w-full rounded-lg p-2.5 text-yellow-500 font-mono">
                                    <button type="button" onclick="triggerKeyGen()" class="bg-gray-800 px-3 rounded-lg font-mono hover:bg-gray-700">AUTO</button>
                                </div>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-gray-400 mb-1">PLAN VALIDITY Frame</label>
                                    <select id="validitySelector" onchange="updateCalculatedExpiry()" class="w-full rounded-lg p-2.5 bg-gray-950">
                                        <option value="1">1 Day Node</option>
                                        <option value="7">7 Days Node</option>
                                        <option value="30">30 Days Node</option>
                                        <option value="unlimited">Unlimited Structural Access</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1">QUOTA CALL LIMIT</label>
                                    <input type="number" id="inputQuotaLimit" value="2500" class="w-full rounded-lg p-2.5">
                                </div>
                            </div>

                            <div class="p-2 bg-gray-950 border border-gray-800 rounded-lg text-[11px]">
                                <span class="text-gray-500">Calculated Sync Expiry (UTC): </span>
                                <span id="expiryPreviewDisplay" class="text-green-400 font-mono font-bold"></span>
                            </div>

                            <div>
                                <label class="block text-gray-400 mb-1.5 uppercase text-[10px]">ROUTE SCOPE MATRIX MATRIX</label>
                                <div class="max-h-44 overflow-y-auto border border-gray-800 p-2 rounded-lg space-y-2 bg-black bg-opacity-30">
                                    <input type="checkbox" id="scope_all" value="all" checked onchange="handleAllScopeToggle(this)" class="hidden api-checkbox">
                                    <label for="scope_all" class="block text-center p-2 rounded-lg tool-btn cursor-pointer text-blue-400 bg-gray-900 font-bold border border-blue-900">⭐ ALL ENDPOINTS ACTIVE</label>
                                    <div class="grid grid-cols-2 gap-1.5">{checkbox_grid_html}</div>
                                </div>
                            </div>

                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg uppercase tracking-wide">INJECT ROUTING REGISTRY</button>
                        </form>
                    </div>

                    <div class="lg:col-span-2 crypto-panel p-4 rounded-xl overflow-hidden">
                        <h2 class="text-xs font-bold text-gray-400 uppercase border-b border-gray-800 pb-2 mb-2.5">ACTIVE NETWORK AUTH DATABASE</h2>
                        <div class="overflow-x-auto w-full">
                            <table class="w-full text-left text-xs min-w-[650px]">
                                <thead>
                                    <tr class="border-b border-gray-800 text-gray-500 font-mono">
                                        <th class="pb-2">CLIENT</th>
                                        <th class="pb-2">ROUTING TOKEN KEY</th>
                                        <th class="pb-2">QUOTA STATUS</th>
                                        <th class="pb-2">EXPIRES TIME (UTC)</th>
                                        <th class="pb-2">STATUS STATE</th>
                                        <th class="pb-2 text-right">MANAGEMENT MANAGEMENT</th>
                                    </tr>
                                </thead>
                                <tbody id="registryTableElementRows" class="divide-y divide-gray-950"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SANDBOX INTERACTION FRAME -->
                <div class="crypto-panel p-4 rounded-xl space-y-3.5">
                    <h2 class="text-xs font-bold text-gray-400 uppercase border-b border-gray-800 pb-2">INTERACTIVE SANDBOX matrix CONSOLE</h2>
                    <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-10 gap-1.5 text-xs">{sandbox_grid_html}</div>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs items-end">
                        <div>
                            <label class="block text-gray-500 mb-1">TARGET GATEWAY PATH</label>
                            <input type="text" id="targetSandboxPathField" value="adv" class="w-full rounded-lg p-2.5 font-mono" readonly>
                        </div>
                        <div>
                            <label class="block text-gray-500 mb-1">INJECT DEMO ACCESS TOKEN</label>
                            <input type="text" id="targetSandboxKeyField" class="w-full rounded-lg p-2.5 font-mono text-yellow-500" placeholder="Click any key string above to inject...">
                        </div>
                        <button onclick="executeSandboxProbeRequest()" class="w-full bg-blue-600 text-white font-bold py-2.5 rounded-lg uppercase tracking-wider hover:bg-blue-700">FIRE ENCRYPTED PROBE</button>
                    </div>
                    <div id="sandboxResponseTerminal" class="hidden p-4 bg-black border border-gray-900 rounded-lg font-mono text-xs text-green-400 max-h-96 overflow-y-auto whitespace-pre-wrap"></div>
                </div>
            </div>

            <script>
                function updateCalculatedExpiry() {{
                    const selection = document.getElementById('validitySelector').value;
                    const preview = document.getElementById('expiryPreviewDisplay');
                    
                    if(selection === "unlimited") {{
                        preview.innerText = "Unlimited";
                        return;
                    }}
                    
                    const days = parseInt(selection);
                    const expiryDate = new Date();
                    expiryDate.setDate(expiryDate.getDate() + days);
                    
                    const yyyy = expiryDate.getUTCFullYear();
                    const mm = String(expiryDate.getUTCMonth() + 1).padStart(2, '0');
                    const dd = String(expiryDate.getUTCDate()).padStart(2, '0');
                    const hh = String(expiryDate.getUTCHours()).padStart(2, '0');
                    const min = String(expiryDate.getUTCMinutes()).padStart(2, '0');
                    const ss = String(expiryDate.getUTCSeconds()).padStart(2, '0');
                    
                    preview.innerText = `${{yyyy}}-${{mm}}-${{dd}} ${{hh}}:${{min}}:${{ss}}`;
                }}

                function handleAllScopeToggle(master) {{
                    document.querySelectorAll('.individual-scope').forEach(box => {{
                        box.checked = false;
                        box.disabled = master.checked;
                    }});
                }}

                function compileScopes() {{
                    if(document.getElementById('scope_all').checked) return "all";
                    let checked = [];
                    document.querySelectorAll('.individual-scope').forEach(box => {{
                        if(box.checked) checked.push(box.value);
                    }});
                    return checked.length > 0 ? checked.join(', ') : "all";
                }}

                function loadRegistriesViewTableMatrix() {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const targetBody = document.getElementById('registryTableElementRows');
                    targetBody.innerHTML = '';

                    if(Object.keys(db).length === 0) {{
                        targetBody.innerHTML = `<tr><td colspan="6" class="py-4 text-center text-gray-600 font-mono">Empty database register arrays.</td></tr>`;
                        return;
                    }}

                    for(const [key, profile] of Object.entries(db)) {{
                        let timeStatusHtml = profile.expires_at;
                        if(profile.expires_at !== "Unlimited") {{
                            const hasExpired = new Date() > new Date(profile.expires_at.replace(' ', 'T') + 'Z');
                            if(hasExpired) timeStatusHtml = `<span class="text-red-500 font-bold">[EXPIRED]</span>`;
                        }}

                        // Determine visual label states
                        const stateSuspended = profile.suspended === true;
                        const statusBadge = stateSuspended 
                            ? `<span class="bg-red-950 text-red-400 border border-red-900 px-2 py-0.5 rounded font-bold text-[10px]">SUSPENDED</span>`
                            : `<span class="bg-green-950 text-green-400 border border-green-900 px-2 py-0.5 rounded font-bold text-[10px]">ACTIVE</span>`;

                        const suspendActionBtn = stateSuspended
                            ? `<button onclick="toggleKeySuspensionState('${{key}}', false)" class="text-green-400 hover:underline font-bold mr-2">UNSUSPEND</button>`
                            : `<button onclick="toggleKeySuspensionState('${{key}}', true)" class="text-yellow-500 hover:underline font-bold mr-2">SUSPEND</button>`;

                        targetBody.innerHTML += `
                            <tr class="hover:bg-gray-950 transition-colors">
                                <td class="py-3 text-white font-medium">${{profile.name}}</td>
                                <td class="py-3 text-yellow-500 font-mono cursor-pointer font-bold tracking-wide" onclick="document.getElementById('targetSandboxKeyField').value='${{key}}'">${{key}}</td>
                                <td class="py-3 font-mono">${{profile.used}} / ${{profile.limit}}</td>
                                <td class="py-3 font-mono text-[11px] text-gray-400">${{timeStatusHtml}}</td>
                                <td class="py-3 font-mono">${{statusBadge}}</td>
                                <td class="py-3 text-right text-[11px]">
                                    ${{suspendActionBtn}}
                                    <button onclick="resetKeyQuotaCounter('${{key}}')" class="text-blue-400 hover:underline font-bold mr-2">RE-LIMIT</button>
                                    <button onclick="purgeKey('${{key}}')" class="text-red-500 hover:underline font-bold">DELETE</button>
                                </td>
                            </tr>
                        `;
                    }}
                }}

                // ---- ACTION CONTROLLER: DYNAMIC SUSPENSION STATE ----
                function toggleKeySuspensionState(key, setSuspended) {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(db[key]) {{
                        db[key].suspended = setSuspended;
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                // ---- ACTION CONTROLLER: RESET LIMIT QUOTA COUNTER ----
                function resetKeyQuotaCounter(key) {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(db[key]) {{
                        db[key].used = 0; // Completely clears use logs instantly
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        loadRegistriesViewTableMatrix();
                        alert(`Quota limit reset successfully for token: ${{key}}`);
                    }}
                }}

                // ---- ACTION CONTROLLER: PURGE/DELETE ROUTING REGISTRY ----
                function purgeKey(key) {{
                    if(confirm(`Are you completely sure you want to delete and destroy key "${{key}}"? All runtime access will terminate immediately.`)) {{
                        const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                        delete db[key];
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                function commitNewTokenToRegistry(e) {{
                    e.preventDefault();
                    const name = document.getElementById('inputClientName').value;
                    const key = document.getElementById('inputLicenseKey').value.trim();
                    const limit = parseInt(document.getElementById('inputQuotaLimit').value);
                    const expiryTime = document.getElementById('expiryPreviewDisplay').innerText;
                    
                    const activeDb = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    
                    // Added default metadata properties
                    activeDb[key] = {{ 
                        name, 
                        limit, 
                        used: 0, 
                        expires_at: expiryTime, 
                        allowed_tools: compileScopes(),
                        suspended: false 
                    }};
                    
                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(activeDb));
                    document.getElementById('tokenGenerationForm').reset();
                    triggerKeyGen();
                    updateCalculatedExpiry();
                    loadRegistriesViewTableMatrix();
                }}

                function triggerKeyGen() {{
                    document.getElementById('inputLicenseKey').value = "VX-" + Math.random().toString(36).substring(2, 7).toUpperCase() + "-" + Math.random().toString(36).substring(2, 7).toUpperCase();
                }}

                function bindSandboxTarget(btnElement, pathName) {{
                    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                    btnElement.classList.add('active');
                    document.getElementById('targetSandboxPathField').value = pathName;
                }}

                async function executeSandboxProbeRequest() {{
                    const endpoint = document.getElementById('targetSandboxPathField').value;
                    const key = document.getElementById('targetSandboxKeyField').value.trim();
                    const terminal = document.getElementById('sandboxResponseTerminal');

                    if(!key) return alert("Select or type an active registry validation key!");
                    
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    
                    // Core validation fallback layer
                    const p = db[key] || {{ name: "Probe Mode", limit: 1000, used: 0, expires_at: "Unlimited", allowed_tools: "all", suspended: false }};

                    terminal.classList.remove('hidden');
                    terminal.innerText = "Transmitting framework authorization transaction sequence frames downstream...";

                    // Pass absolute validation status downward through routing query parameters
                    const url = `/api/${{endpoint}}?key=${{key}}&client_name=${{p.name}}&key_limit=${{p.limit}}&key_used=${{p.used}}&key_expires=${{encodeURIComponent(p.expires_at)}}&key_tools=${{p.allowed_tools}}&key_suspended=${{p.suspended}}&num=7003741482`;

                    try {{
                        const res = await fetch(url);
                        const data = await res.json();
                        
                        if(res.ok && db[key]) {{
                            db[key].used += 1;
                            localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                            loadRegistriesViewTableMatrix();
                        }}
                        terminal.innerText = JSON.stringify(data, null, 4);
                    }} catch(e) {{ terminal.innerText = "Error framework exception connection loss: " + e.toString(); }}
                }}

                window.onload = function() {{
                    triggerKeyGen();
                    updateCalculatedExpiry();
                    loadRegistriesViewTableMatrix();
                }}
            </script>
        </body>
        </html>
        """
        await send_html(send, html_content)
        return
    else:
        await send_json(send, {"detail": "Not Found"}, 404)

async def send_json(send, data: dict, status_code: int = 200):
    body = json.dumps(data).encode('utf-8')
    await send({'type': 'http.response.start', 'status': status_code, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': body})

async def send_html(send, html_text: str):
    body = html_text.encode('utf-8')
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/html')]})
    await send({'type': 'http.response.body', 'body': body})
