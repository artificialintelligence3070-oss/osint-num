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
        
        client_name = urllib.parse.unquote(params.get("client_name", "External Node"))
        key_limit = int(params.get("key_limit", 1000))
        key_used = int(params.get("key_used", 0))
        key_expiry = urllib.parse.unquote(params.get("key_expires", "Expired"))
        allowed_tools = urllib.parse.unquote(params.get("key_tools", "all"))
        is_suspended = params.get("key_suspended", "false").lower() == "true"

        if not client_key:
            await send_json(send, {"error": "Missing client authorization identifier token."}, 403)
            return

        # 1. CRITICAL FIXED: SUSPENSION HARD-STOP
        if is_suspended:
            await send_json(send, {"error": "Access Denied. This API key is suspended. DM FOR BUY NEW API"}, 403)
            return

        # 2. CRITICAL FIXED: EXPIRY HARD-STOP
        if key_expiry != "Lifetime":
            try:
                if datetime.utcnow() > datetime.strptime(key_expiry, "%Y-%m-%d %H:%M:%S"):
                    await send_json(send, {"error": f"API Key Expired ({key_expiry} UTC). DM FOR BUY NEW API"}, 403)
                    return
            except Exception:
                await send_json(send, {"error": "Invalid Expiry Format Configuration. DM FOR BUY NEW API"}, 403)
                return

        # 3. CRITICAL FIXED: LIMIT FINISHED HARD-STOP
        if key_used >= key_limit:
            await send_json(send, {"error": "Quota Limit Finished! DM FOR BUY NEW API"}, 429)
            return

        # 4. MODULE VALIDATION
        if allowed_tools != "all":
            allowed_list = [t.strip().lower() for t in allowed_tools.split(",")]
            if endpoint.lower() not in allowed_list:
                await send_json(send, {"error": "Access Denied. Endpoint restriction active."}, 403)
                return

        cleaned_params = {}
        for k, v in params.items():
            if k not in ["key", "client_name", "key_limit", "key_used", "key_expires", "key_tools", "key_suspended"]:
                cleaned_params[k] = v
        
        # LOGS COLLECTOR SYSTEM (Tracks everything searched by users)
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
                await send_json(send, {"error": "Target infrastructure timeout connection failure"}, 502)
                return

    elif path == "/admin/logs":
        await send_json(send, {"logs": SYSTEM_LIVE_LOGS[:50]})
        return

    elif path == "/":
        checkbox_grid_html = "".join([f"""
        <div class="relative">
            <input type="checkbox" id="scope_{tool}" value="{tool}" class="hidden api-checkbox individual-scope">
            <label for="scope_{tool}" class="block text-center p-2 rounded-lg tool-btn cursor-pointer font-mono text-gray-400 bg-gray-900 border border-gray-800 transition text-[11px] uppercase">
                {tool}
            </label>
        </div>
        """ for tool in CORE_API_ENDPOINTS])

        sandbox_grid_html = "".join([f"""
        <button type="button" onclick="bindSandboxTarget(this, '{tool}')" class="p-2 rounded-lg tool-btn text-center font-mono text-[11px] uppercase tracking-wider text-gray-400 {'active' if idx == 0 else ''}">
            {tool}
        </button>
        """ for idx, tool in enumerate(CORE_API_ENDPOINTS)])

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Nexus Cyber Terminal | {DEVELOPER_NAME}</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ 
                    background-color: #020205; 
                    color: #00ffcc; 
                    font-family: 'Courier New', Courier, monospace;
                }}
                .glow-panel {{ 
                    background: #05070f; 
                    border: 1px solid #00ffcc; 
                    box-shadow: 0 0 15px rgba(0, 255, 204, 0.15);
                }}
                .glow-panel-purple {{ 
                    background: #07050f; 
                    border: 1px solid #9d4edd; 
                    box-shadow: 0 0 15px rgba(157, 78, 221, 0.15);
                }}
                input, select {{ 
                    background-color: #000000 !important; 
                    color: #00ffcc !important; 
                    border: 1px solid #00ffcc !important; 
                    text-shadow: 0 0 5px #00ffcc;
                    outline: none; 
                }}
                input:focus, select:focus {{ 
                    box-shadow: 0 0 10px #00ffcc; 
                }}
                .tool-btn {{
                    background: #000;
                    border: 1px solid #333;
                }}
                .tool-btn.active {{ 
                    border-color: #00ffcc !important; 
                    color: #00ffcc !important;
                    box-shadow: 0 0 8px #00ffcc;
                }}
                .api-checkbox:checked + label {{ 
                    border-color: #9d4edd !important; 
                    color: #9d4edd !important;
                    box-shadow: 0 0 8px #9d4edd;
                    background: rgba(157, 78, 221, 0.1);
                }}
                .neon-btn-green {{
                    background: #000; border: 1px solid #00ff66; color: #00ff66;
                    box-shadow: 0 0 10px rgba(0, 255, 102, 0.2);
                }}
                .neon-btn-green:hover {{ background: #00ff66; color: #000; box-shadow: 0 0 20px #00ff66; }}
                ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
                ::-webkit-scrollbar-thumb {{ background: #00ffcc; border-radius: 2px; }}
            </style>
        </head>
        <body class="p-2 sm:p-4 min-h-screen">
            <div class="max-w-7xl mx-auto space-y-4">
                
                <header class="flex flex-col sm:flex-row justify-between items-center border-b border-cyan-900 pb-3 gap-2">
                    <div class="text-center sm:text-left">
                        <h1 class="text-xl font-bold tracking-widest text-cyan-400" style="text-shadow: 0 0 10px #00ffff;">NEXUS QUANTUM CORE V2</h1>
                        <div class="text-xs font-mono text-purple-400">CONSOLE DEVELOPER: <a href="{CHANNEL_URL}" target="_blank" class="underline font-bold text-cyan-300">{DEVELOPER_NAME}</a></div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] bg-cyan-950 px-2.5 py-1 rounded border border-cyan-500 font-bold tracking-widest animate-pulse">SYSTEM_ONLINE</span>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <!-- CONTROLLER GENERATOR BOX -->
                    <div class="glow-panel p-4 rounded-xl space-y-4">
                        <form id="tokenGenerationForm" onsubmit="commitNewTokenToRegistry(event)" class="space-y-3 text-xs">
                            <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-wider border-b border-cyan-900 pb-1.5">PROVISION AUTH MATRIX</h2>
                            
                            <div>
                                <label class="block text-gray-400 mb-1 font-mono">CLIENT IDENTIFIER TAG</label>
                                <input type="text" id="inputClientName" placeholder="Client Username" required class="w-full rounded-lg p-2 font-mono">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1 font-mono">SECRET ACCESS LICENSE KEY</label>
                                <div class="flex gap-2">
                                    <input type="text" id="inputLicenseKey" placeholder="VX-XXXXX" required class="w-full rounded-lg p-2 font-mono text-yellow-400">
                                    <button type="button" onclick="triggerKeyGen()" class="bg-gray-900 border border-cyan-600 px-3 rounded-lg font-mono text-cyan-400 hover:bg-cyan-950">AUTO</button>
                                </div>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-gray-400 mb-1 font-mono">VALIDITY TIMELINE</label>
                                    <select id="validitySelector" onchange="updateCalculatedExpiry()" class="w-full rounded-lg p-2 bg-black font-mono">
                                        <option value="1s">1 Second</option>
                                        <option value="1m">1 Minute</option>
                                        <option value="1h">1 Hour</option>
                                        <option value="1">1 Day</option>
                                        <option value="7">7 Days</option>
                                        <option value="30">30 Days</option>
                                        <option value="lifetime">Lifetime Plan</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1 font-mono">LIMIT THRESHOLD</label>
                                    <input type="number" id="inputQuotaLimit" value="100" class="w-full rounded-lg p-2 font-mono">
                                </div>
                            </div>

                            <div class="p-2 bg-black border border-cyan-900 rounded-lg text-[11px] font-mono">
                                <span class="text-purple-400">SYNC EXPIRY LOCK (UTC):</span>
                                <div id="expiryPreviewDisplay" class="text-green-400 font-bold mt-0.5"></div>
                            </div>

                            <div>
                                <label class="block text-gray-400 mb-1 uppercase text-[10px] font-mono">MODULE METRIC PERMISSIONS</label>
                                <div class="max-h-40 overflow-y-auto border border-cyan-950 p-2 rounded-lg space-y-1.5 bg-black">
                                    <input type="checkbox" id="scope_all" value="all" checked onchange="handleAllScopeToggle(this)" class="hidden api-checkbox">
                                    <label for="scope_all" class="block text-center p-1.5 rounded-lg tool-btn cursor-pointer text-purple-400 bg-gray-950 border border-purple-900 font-bold">⭐ UNRESTRICTED CORE INJECTION</label>
                                    <div class="grid grid-cols-2 gap-1">{checkbox_grid_html}</div>
                                </div>
                            </div>

                            <button type="submit" class="w-full neon-btn-green font-bold py-2.5 rounded-lg uppercase tracking-widest font-mono text-xs transition">INJECT KEY TARGET</button>
                        </form>
                    </div>

                    <!-- NETWORK DATABASE CONTAINER BOX -->
                    <div class="lg:col-span-2 glow-panel-purple p-4 rounded-xl flex flex-col h-[520px]">
                        <h2 class="text-xs font-bold text-purple-400 uppercase tracking-wider border-b border-purple-900 pb-1.5 mb-2">ACTIVE SYSTEM AUTH REGISTRY</h2>
                        <div class="overflow-x-auto overflow-y-auto flex-1 w-full text-[11px]">
                            <table class="w-full text-left min-w-[700px]">
                                <thead>
                                    <tr class="border-b border-purple-950 text-gray-500 font-mono text-[10px]">
                                        <th class="pb-1.5">CLIENT TAG</th>
                                        <th class="pb-1.5">LICENCE TOKEN KEY</th>
                                        <th class="pb-1.5">QUOTA TRAFFIC</th>
                                        <th class="pb-1.5">TIME BLOCK EXPIRES</th>
                                        <th class="pb-1.5">STATE</th>
                                        <th class="pb-1.5 text-right">MANAGE ACTION NODE</th>
                                    </tr>
                                </thead>
                                <tbody id="registryTableElementRows" class="divide-y divide-purple-950 font-mono"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- LIVE VISUAL SEARCHING LOGBOX -->
                <div class="glow-panel p-4 rounded-xl space-y-2">
                    <div class="flex justify-between items-center border-b border-cyan-900 pb-1.5">
                        <h2 class="text-xs font-bold text-cyan-400 tracking-wider">LIVE TRAFFIC INBOUND LOGS (USER SEARCHES)</h2>
                        <button onclick="syncTelemetryLogsFeed()" class="text-[9px] bg-black border border-cyan-600 text-cyan-400 px-2 py-0.5 rounded">SYNC ENGINE</button>
                    </div>
                    <div class="overflow-x-auto max-h-40 text-[11px] font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-gray-500 border-b border-cyan-950 text-[10px]">
                                    <th class="pb-1">TIMESTAMP UTC</th>
                                    <th class="pb-1">REQUEST KEY</th>
                                    <th class="pb-1">TARGET MODULE</th>
                                    <th class="pb-1">EXTRACTED SEARCH QUERY METRIC</th>
                                </tr>
                            </thead>
                            <tbody id="telemetryPacketStreamBodyRows" class="divide-y divide-gray-950 text-cyan-300">
                                <tr><td colspan="4" class="py-4 text-center text-gray-700">Awaiting runtime socket transaction data feeds...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- SANDBOX SIMULATOR BOX -->
                <div class="glow-panel p-4 rounded-xl space-y-3">
                    <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-wider border-b border-cyan-900 pb-1">INTERACTIVE INJECTION SANDBOX</h2>
                    <div class="grid grid-cols-4 sm:grid-cols-7 lg:grid-cols-10 gap-1 text-[10px]">{sandbox_grid_html}</div>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] items-end">
                        <div>
                            <label class="block text-gray-500 mb-1 font-mono">TARGET PATH</label>
                            <input type="text" id="targetSandboxPathField" value="adv" class="w-full rounded-lg p-2 font-mono" readonly>
                        </div>
                        <div>
                            <label class="block text-gray-500 mb-1 font-mono">INJECT REGISTRY KEY</label>
                            <input type="text" id="targetSandboxKeyField" class="w-full rounded-lg p-2 font-mono text-yellow-400" placeholder="Click any key string inside active list table...">
                        </div>
                        <button onclick="executeSandboxProbeRequest()" class="w-full neon-btn-green py-2 rounded-lg font-mono uppercase text-xs font-bold">LAUNCH SECURE ATTACK PROBE</button>
                    </div>
                    <div id="sandboxResponseTerminal" class="hidden p-3 bg-black border border-red-900 rounded-lg font-mono text-[11px] text-green-400 max-h-64 overflow-y-auto whitespace-pre-wrap"></div>
                </div>

            </div>

            <script>
                function updateCalculatedExpiry() {{
                    const selection = document.getElementById('validitySelector').value;
                    const preview = document.getElementById('expiryPreviewDisplay');
                    
                    if(selection === "lifetime") {{
                        preview.innerText = "Lifetime";
                        return;
                    }}
                    
                    const expiryDate = new Date();
                    if(selection === "1s") expiryDate.setSeconds(expiryDate.getSeconds() + 1);
                    else if(selection === "1m") expiryDate.setMinutes(expiryDate.getMinutes() + 1);
                    else if(selection === "1h") expiryDate.setHours(expiryDate.getHours() + 1);
                    else expiryDate.setDate(expiryDate.getDate() + parseInt(selection));
                    
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

                    for(const [key, profile] of Object.entries(db)) {{
                        let timeStatusHtml = profile.expires_at;
                        let isExpired = false;
                        
                        if(profile.expires_at !== "Lifetime") {{
                            isExpired = new Date() > new Date(profile.expires_at.replace(' ', 'T') + 'Z');
                            if(isExpired) timeStatusHtml = `<span class="text-red-500 font-bold animate-pulse">[EXPIRED]</span>`;
                        }}

                        const isLimitReached = profile.used >= profile.limit;
                        const quotaDisplay = isLimitReached 
                            ? `<span class="text-red-500 font-bold">${{profile.used}}/${{profile.limit}} [FINISHED]</span>`
                            : `<span class="text-green-400">${{profile.used}}/${{profile.limit}}</span>`;

                        const stateSuspended = profile.suspended === true;
                        
                        let statusBadge = `<span class="text-green-400 border border-green-500 px-1.5 py-0.5 rounded text-[9px]">RUNNING</span>`;
                        if(stateSuspended) statusBadge = `<span class="text-yellow-500 border border-yellow-500 px-1.5 py-0.5 rounded text-[9px]">SUSPENDED</span>`;
                        else if(isExpired || isLimitReached) statusBadge = `<span class="text-red-500 border border-red-500 px-1.5 py-0.5 rounded text-[9px]">LOCKED</span>`;

                        const suspendActionBtn = stateSuspended
                            ? `<button onclick="toggleKeySuspensionState('${{key}}', false)" class="text-green-400 hover:underline mr-1.5">UNSUSPEND</button>`
                            : `<button onclick="toggleKeySuspensionState('${{key}}', true)" class="text-yellow-500 hover:underline mr-1.5">SUSPEND</button>`;

                        targetBody.innerHTML += `
                            <tr class="hover:bg-purple-950 hover:bg-opacity-20 transition-colors">
                                <td class="py-2.5 text-white font-bold border-b border-purple-950">${{profile.name}}</td>
                                <td class="py-2.5 text-cyan-300 font-bold cursor-pointer border-b border-purple-950" onclick="document.getElementById('targetSandboxKeyField').value='${{key}}'">${{key}}</td>
                                <td class="py-2.5 border-b border-purple-950">${{quotaDisplay}}</td>
                                <td class="py-2.5 border-b border-purple-950 text-[10px] text-gray-400">${{timeStatusHtml}}</td>
                                <td class="py-2.5 border-b border-purple-950">${{statusBadge}}</td>
                                <td class="py-2.5 text-right text-[10px] border-b border-purple-950">
                                    ${{suspendActionBtn}}
                                    <button onclick="resetKeyQuotaCounter('${{key}}')" class="text-blue-400 hover:underline mr-1.5">RE-LIMIT</button>
                                    <button onclick="purgeKey('${{key}}')" class="text-red-500 hover:underline font-bold">DELETE</button>
                                </td>
                            </tr>
                        `;
                    }}
                }}

                function toggleKeySuspensionState(key, setSuspended) {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(db[key]) {{
                        db[key].suspended = setSuspended;
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                function resetKeyQuotaCounter(key) {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(db[key]) {{
                        db[key].used = 0;
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                function purgeKey(key) {{
                    if(confirm(`Completely destroy authorization metadata routing registry for key: "${{key}}"?`)) {{
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
                    activeDb[key] = {{ name, limit, used: 0, expires_at: expiryTime, allowed_tools: compileScopes(), suspended: false }};
                    
                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(activeDb));
                    document.getElementById('tokenGenerationForm').reset();
                    triggerKeyGen();
                    updateCalculatedExpiry();
                    loadRegistriesViewTableMatrix();
                }}

                function triggerKeyGen() {{
                    document.getElementById('inputLicenseKey').value = "VX-" + Math.random().toString(36).substring(2, 6).toUpperCase() + "-" + Math.random().toString(36).substring(2, 6).toUpperCase();
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

                    if(!key) return alert("Select or type an validation core registry key!");
                    
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const p = db[key] || {{ name: "Probe", limit: 100, used: 0, expires_at: "Lifetime", allowed_tools: "all", suspended: false }};

                    terminal.classList.remove('hidden');
                    terminal.innerText = "Transmitting cyber transaction encryption stream payloads...";

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
                    }} catch(e) {{ terminal.innerText = "Error: " + e.toString(); }}
                    syncTelemetryLogsFeed();
                }}

                async function syncTelemetryLogsFeed() {{
                    try {{
                        const response = await fetch('/admin/logs');
                        const data = await response.json();
                        const logsTbody = document.getElementById('telemetryPacketStreamBodyRows');
                        logsTbody.innerHTML = '';

                        if(!data.logs || data.logs.length === 0) {{
                            logsTbody.innerHTML = `<tr><td colspan="4" class="py-4 text-center text-gray-600">No runtime traffic analyzed yet.</td></tr>`;
                            return;
                        }}

                        data.logs.forEach(log => {{
                            logsTbody.innerHTML += `
                                <tr class="border-b border-gray-950 hover:bg-gray-900">
                                    <td class="py-1.5 text-gray-500">${{log.timestamp}}</td>
                                    <td class="py-1.5 text-yellow-500 font-bold">${{log.key}}</td>
                                    <td class="py-1.5 text-cyan-400">/api/${{log.endpoint}}</td>
                                    <td class="py-1.5 text-purple-300 max-w-xs truncate" title="${{log.params}}">${{log.params}}</td>
                                </tr>
                            `;
                        }});
                    }} catch(e) {{}}
                }}

                window.onload = function() {{
                    triggerKeyGen();
                    updateCalculatedExpiry();
                    loadRegistriesViewTableMatrix();
                    syncTelemetryLogsFeed();
                    setInterval(syncTelemetryLogsFeed, 7000);
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
