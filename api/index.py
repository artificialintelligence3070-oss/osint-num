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
# SERVER-SIDE CENTRAL MEMORY FOR KEYS (Fixes External API Requests)
SERVER_KEY_REGISTRY = {}

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
            params[k] = urllib.parse.unquote(v)
        else:
            if pair:
                params[pair] = ""
    return params

def get_current_ist() -> datetime:
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

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
    global SYSTEM_LIVE_LOGS, SERVER_KEY_REGISTRY
    
    if scope['type'] != 'http':
        return

    path = scope['path']
    query_string = scope.get('query_string', b'').decode('utf-8')
    params = parse_query_string(query_string)

    # --- ADMIN CENTRAL REGISTRY SYNC PIPELINE ---
    if path == "/admin/sync_key":
        if scope['method'] == 'POST':
            try:
                body_bytes = b""
                more_body = True
                while more_body:
                    message = await receive()
                    body_bytes += message.get('body', b'')
                    more_body = message.get('more_body', False)
                
                sync_data = json.loads(body_bytes.decode('utf-8'))
                key = sync_data.get("key")
                if key:
                    SERVER_KEY_REGISTRY[key] = {
                        "name": sync_data.get("name"),
                        "limit": int(sync_data.get("limit", 10)),
                        "used": int(sync_data.get("used", 0)),
                        "expires_at": sync_data.get("expires_at", "Lifetime"),
                        "allowed_tools": sync_data.get("allowed_tools", "all"),
                        "suspended": sync_data.get("suspended", False),
                        "deleted": sync_data.get("deleted", False)
                    }
                await send_json(send, {"status": "success"})
                return
            except Exception as e:
                await send_json(send, {"status": "error", "message": str(e)}, 500)
                return

    elif path == "/admin/get_db":
        await send_json(send, SERVER_KEY_REGISTRY)
        return

    elif path == "/admin/logs":
        await send_json(send, {"logs": SYSTEM_LIVE_LOGS[:50]})
        return

    # --- ROUTE HANDLING FOR API ENDPOINTS ---
    elif path.startswith("/api/"):
        endpoint = path.replace("/api/", "", 1)
        client_key = params.get("key")

        if not client_key:
            await send_json(send, {"error": "Missing client authorization token. DM for new key purchased"}, 403)
            return

        # Fetch live data from Server-Side Dictionary or fallback to query params
        if client_key in SERVER_KEY_REGISTRY:
            key_profile = SERVER_KEY_REGISTRY[client_key]
        else:
            # Fallback if dictionary was cleared
            key_profile = {
                "limit": int(params.get("key_limit", 10)),
                "used": int(params.get("key_used", 0)),
                "expires_at": params.get("key_expires", "Lifetime"),
                "allowed_tools": params.get("key_tools", "all"),
                "suspended": str(params.get("key_suspended", "false")).lower() == "true",
                "deleted": str(params.get("key_deleted", "false")).lower() == "true"
            }

        # 1. CRITICAL DELETION CHECK
        if key_profile.get("deleted"):
            await send_json(send, {"error": "DM for new key purchased"}, 403)
            return

        # 2. CRITICAL SUSPENSION CHECK
        if key_profile.get("suspended"):
            await send_json(send, {"error": "The key is suspended by the author or admin"}, 403)
            return

        # 3. REALTIME EXPIRY CHECK (IST MATCH)
        key_expiry = key_profile.get("expires_at", "Lifetime")
        if key_expiry != "Lifetime" and key_expiry != "---":
            try:
                current_time = get_current_ist()
                expiry_dt = datetime.strptime(key_expiry, "%Y-%m-%d %H:%M:%S")
                if current_time >= expiry_dt:
                    await send_json(send, {"error": "The key is expired. Please buy a new key"}, 403)
                    return
            except Exception:
                pass

        # 4. QUOTA LIMIT FINISHED CHECK
        if key_profile.get("used", 0) >= key_profile.get("limit", 10):
            await send_json(send, {"error": "Your limit was finished. DM for new key purchased"}, 429)
            return

        # 5. ENDPOINT MATRIX LOCK
        allowed_tools = key_profile.get("allowed_tools", "all")
        if allowed_tools != "all":
            allowed_list = [t.strip().lower() for t in allowed_tools.split(",")]
            if endpoint.lower() not in allowed_list:
                await send_json(send, {"error": "Access Denied. Endpoint restriction active. DM for new key purchased"}, 403)
                return

        # Increment use count directly inside server side memory registry
        if client_key in SERVER_KEY_REGISTRY:
            SERVER_KEY_REGISTRY[client_key]["used"] += 1
        else:
            SERVER_KEY_REGISTRY[client_key] = key_profile
            SERVER_KEY_REGISTRY[client_key]["used"] += 1

        # Clean validation tokens from target destination params
        cleaned_params = {}
        for k, v in params.items():
            if k not in ["key", "client_name", "key_limit", "key_used", "key_expires", "key_tools", "key_suspended", "key_deleted"]:
                cleaned_params[k] = v
        
        SYSTEM_LIVE_LOGS.insert(0, {
            "timestamp": get_current_ist().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })

        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(upstream_url, params=cleaned_params, timeout=15.0)
                raw_response_json = response.json()
                scrubbed_response_json = scrub_legacy_branding(raw_response_json)
                await send_json(send, scrubbed_response_json, response.status_code)
                return
            except Exception:
                await send_json(send, {"error": "Target backend network timeout. DM for new key purchased"}, 502)
                return

    # --- MAIN HTML INTERFACE ---
    elif path == "/":
        checkbox_grid_html = "".join([f"""
        <div class="relative">
            <input type="checkbox" id="scope_{tool}" value="{tool}" class="hidden api-checkbox individual-scope">
            <label for="scope_{tool}" class="block text-center p-2 rounded-lg tool-btn cursor-pointer font-mono text-gray-400 bg-gray-950 border border-gray-800 transition text-[11px] uppercase">
                {tool}
            </label>
        </div>
        """ for tool in CORE_API_ENDPOINTS])

        sandbox_grid_html = "".join([f"""
        <button type="button" id="sandbox_btn_{tool}" onclick="bindSandboxTarget(this, '{tool}')" class="p-2 rounded-lg tool-btn text-center font-mono text-[11px] uppercase tracking-wider text-gray-400 {'active' if idx == 0 else ''}">
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
                    background-color: #010103; 
                    color: #00ffcc; 
                    font-family: 'Courier New', Courier, monospace;
                }}
                .glow-panel-cyan {{ 
                    background: #04060d; 
                    border: 1px solid #00ffcc; 
                    box-shadow: 0 0 20px rgba(0, 255, 204, 0.2);
                }}
                .glow-panel-purple {{ 
                    background: #05040d; 
                    border: 1px solid #b5179e; 
                    box-shadow: 0 0 20px rgba(181, 23, 158, 0.2);
                }}
                input, select {{ 
                    background-color: #000000 !important; 
                    color: #00ffcc !important; 
                    border: 1px solid #00ffcc !important; 
                    text-shadow: 0 0 5px #00ffcc;
                    outline: none; 
                }}
                input:focus, select:focus {{ 
                    box-shadow: 0 0 12px #00ffcc; 
                }}
                .tool-btn {{ background: #000; border: 1px solid #222; }}
                .tool-btn.active {{ 
                    border-color: #00ffcc !important; 
                    color: #00ffcc !important;
                    box-shadow: 0 0 10px #00ffcc;
                }}
                .api-checkbox:checked + label {{ 
                    border-color: #b5179e !important; 
                    color: #ff007f !important;
                    box-shadow: 0 0 10px #b5179e;
                    background: rgba(181, 23, 158, 0.1);
                }}
                .neon-btn-green {{
                    background: #000; border: 1px solid #00ff66; color: #00ff66;
                    box-shadow: 0 0 12px rgba(0, 255, 102, 0.2);
                }}
                .neon-btn-green:hover {{ background: #00ff66; color: #000; box-shadow: 0 0 25px #00ff66; }}
                ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
                ::-webkit-scrollbar-thumb {{ background: #00ffcc; }}
            </style>
        </head>
        <body class="p-2 sm:p-4 min-h-screen">
            <div class="max-w-7xl mx-auto space-y-4">
                
                <header class="flex flex-col sm:flex-row justify-between items-center border-b border-cyan-900 pb-3 gap-2">
                    <div class="text-center sm:text-left">
                        <h1 class="text-2xl font-bold tracking-widest text-cyan-400" style="text-shadow: 0 0 12px #00ffff;">NEXUS SYSTEM TERMINAL V3</h1>
                        <div class="text-xs font-mono text-purple-400">CONSOLE DEVELOPER: <a href="{CHANNEL_URL}" target="_blank" class="underline font-bold text-cyan-300">{DEVELOPER_NAME}</a></div>
                    </div>
                    <div>
                        <span class="text-[11px] bg-cyan-950 px-3 py-1 rounded border border-cyan-500 font-bold tracking-widest">IST_ENGINE_CONNECTED</span>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <!-- CONTROLLER GENERATOR -->
                    <div class="glow-panel-cyan p-4 rounded-xl space-y-4">
                        <form id="tokenGenerationForm" onsubmit="commitNewTokenToRegistry(event)" class="space-y-3 text-xs">
                            <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-wider border-b border-cyan-900 pb-1.5">GENERATE API ROUTE</h2>
                            
                            <div>
                                <label class="block text-gray-400 mb-1 font-mono">CLIENT ASSIGNMENT ID</label>
                                <input type="text" id="inputClientName" placeholder="Client Name" required class="w-full rounded-lg p-2 font-mono">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1 font-mono">SYSTEM INJECTION API KEY</label>
                                <div class="flex gap-2">
                                    <input type="text" id="inputLicenseKey" placeholder="VX-XXXXX" required class="w-full rounded-lg p-2 font-mono text-yellow-400">
                                    <button type="button" onclick="triggerKeyGen()" class="bg-gray-900 border border-cyan-600 px-3 rounded-lg font-mono text-cyan-400 hover:bg-cyan-950">AUTO</button>
                                </div>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-gray-400 mb-1 font-mono">EXPIRY METHOD</label>
                                    <select id="expiryModeSelector" onchange="toggleExpiryInputView()" class="w-full rounded-lg p-2 bg-black font-mono">
                                        <option value="custom">Select Month Chart</option>
                                        <option value="lifetime">Lifetime Access</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-1 font-mono">LIMIT THRESHOLD</label>
                                    <input type="number" id="inputQuotaLimit" value="10" required class="w-full rounded-lg p-2 font-mono">
                                </div>
                            </div>

                            <div id="customDateTimePickerBox">
                                <label class="block text-gray-400 mb-1 font-mono">CHOOSE EXPIRY DATE & TIME (IST)</label>
                                <input type="datetime-local" id="inputCustomDateTime" onchange="updateCalculatedExpiry()" class="w-full rounded-lg p-2 font-mono text-green-400">
                            </div>

                            <div class="p-2 bg-black border border-cyan-900 rounded-lg text-[11px] font-mono">
                                <span class="text-purple-400">TARGET LOCKED TIME (IST):</span>
                                <div id="expiryPreviewDisplay" class="text-green-400 font-bold mt-0.5">---</div>
                            </div>

                            <div>
                                <label class="block text-gray-400 mb-1 uppercase text-[10px] font-mono">MODULE MATRIX PERMISSIONS</label>
                                <div class="max-h-36 overflow-y-auto border border-cyan-950 p-2 rounded-lg space-y-1.5 bg-black">
                                    <input type="checkbox" id="scope_all" value="all" checked onchange="handleAllScopeToggle(this)" class="hidden api-checkbox">
                                    <label for="scope_all" class="block text-center p-1.5 rounded-lg tool-btn cursor-pointer text-purple-400 bg-gray-950 border border-purple-900 font-bold">⭐ UNRESTRICTED ALL ACCESS</label>
                                    <div class="grid grid-cols-2 gap-1">{checkbox_grid_html}</div>
                                </div>
                            </div>

                            <button type="submit" class="w-full neon-btn-green font-bold py-2.5 rounded-lg uppercase tracking-widest font-mono text-xs transition">INJECT KEY REGISTRY</button>
                        </form>
                    </div>

                    <!-- CLOUD DATABASE MATRIX -->
                    <div class="lg:col-span-2 glow-panel-purple p-4 rounded-xl flex flex-col h-[520px]">
                        <h2 class="text-xs font-bold text-purple-400 uppercase tracking-wider border-b border-purple-900 pb-1.5 mb-2">ACTIVE AUTHORIZATION DATABASE</h2>
                        <div class="overflow-x-auto overflow-y-auto flex-1 w-full text-[11px]">
                            <table class="w-full text-left min-w-[720px]">
                                <thead>
                                    <tr class="border-b border-purple-950 text-gray-500 font-mono text-[10px]">
                                        <th class="pb-1.5">CLIENT</th>
                                        <th class="pb-1.5">API KEY TOKEN</th>
                                        <th class="pb-1.5">QUOTA TRAFFIC</th>
                                        <th class="pb-1.5">EXPIRY (IST)</th>
                                        <th class="pb-1.5">STATUS</th>
                                        <th class="pb-1.5 text-right">SYSTEM ACTION CONTROL</th>
                                    </tr>
                                </thead>
                                <tbody id="registryTableElementRows" class="divide-y divide-purple-950 font-mono"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TRAFFIC VIEW LOGS -->
                <div class="glow-panel-cyan p-4 rounded-xl space-y-2">
                    <div class="flex justify-between items-center border-b border-cyan-900 pb-1.5">
                        <h2 class="text-xs font-bold text-cyan-400 tracking-wider">LIVE TRAFFIC VIEW LOGS (USER SEARCH HISTORIES)</h2>
                        <button onclick="syncTelemetryLogsFeed()" class="text-[10px] bg-black border border-cyan-600 text-cyan-400 px-2 py-0.5 rounded">FORCE REFRESH</button>
                    </div>
                    <div class="overflow-x-auto max-h-44 text-[11px] font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-gray-500 border-b border-cyan-950 text-[10px]">
                                    <th class="pb-1">TIMESTAMP (IST)</th>
                                    <th class="pb-1">AUTHENTICATED KEY</th>
                                    <th class="pb-1">MODULE PATH</th>
                                    <th class="pb-1">SEARCH PARAMETERS DETECTED</th>
                                </tr>
                            </thead>
                            <tbody id="telemetryPacketStreamBodyRows" class="divide-y divide-gray-950 text-cyan-300">
                                <tr><td colspan="4" class="py-3 text-center text-gray-700">Awaiting database connection log stream pipes...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- ATTACK SANDBOX PROBE CONSOLE -->
                <div class="glow-panel-cyan p-4 rounded-xl space-y-3">
                    <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-wider border-b border-cyan-900 pb-1">CYBER ATTACK PROBE SANDBOX CONSOLE</h2>
                    <div class="grid grid-cols-4 sm:grid-cols-7 lg:grid-cols-10 gap-1 text-[10px]">{sandbox_grid_html}</div>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] items-end">
                        <div>
                            <label class="block text-gray-500 mb-1 font-mono">TARGET PATH</label>
                            <input type="text" id="targetSandboxPathField" value="adv" class="w-full rounded-lg p-2 font-mono" readonly>
                        </div>
                        <div>
                            <label class="block text-gray-500 mb-1 font-mono">INJECT API KEY</label>
                            <input type="text" id="targetSandboxKeyField" class="w-full rounded-lg p-2 font-mono text-yellow-400" placeholder="Click any key token inside table registry...">
                        </div>
                        <button onclick="executeSandboxProbeRequest()" class="w-full neon-btn-green py-2 rounded-lg font-mono uppercase text-xs font-bold">FIRE EMULATED KEY REQUEST</button>
                    </div>
                    <div id="sandboxResponseTerminal" class="hidden p-3 bg-black border border-cyan-900 rounded-lg font-mono text-[11px] text-green-400 max-h-64 overflow-y-auto whitespace-pre-wrap"></div>
                </div>

            </div>

            <script>
                function toggleExpiryInputView() {{
                    const mode = document.getElementById('expiryModeSelector').value;
                    const box = document.getElementById('customDateTimePickerBox');
                    if(mode === "lifetime") {{
                        box.style.display = "none";
                        document.getElementById('expiryPreviewDisplay').innerText = "Lifetime";
                    }} else {{
                        box.style.display = "block";
                        updateCalculatedExpiry();
                    }}
                }}

                function updateCalculatedExpiry() {{
                    const mode = document.getElementById('expiryModeSelector').value;
                    if(mode === "lifetime") return;
                    
                    const inputVal = document.getElementById('inputCustomDateTime').value;
                    if(!inputVal) {{
                        document.getElementById('expiryPreviewDisplay').innerText = "---";
                        return;
                    }}
                    
                    const d = new Date(inputVal);
                    const yyyy = d.getFullYear();
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    const dd = String(d.getDate()).padStart(2, '0');
                    const hh = String(d.getHours()).padStart(2, '0');
                    const min = String(d.getMinutes()).padStart(2, '0');
                    
                    document.getElementById('expiryPreviewDisplay').innerText = `${{yyyy}}-${{mm}}-${{dd}} ${{hh}}:${{min}}:00`;
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

                function getSystemIstDateObject() {{
                    const d = new Date();
                    const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
                    return new Date(utc + (3600000 * 5.5));
                }}

                // Core logic to sync any state update straight to python server side memory
                async function syncKeyToServerRegistry(key, profileObj) {{
                    try {{
                        await fetch('/admin/sync_key', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ key: key, ...profileObj }})
                        }});
                    }} catch(e) {{ console.error("Sync failure", e); }}
                }}

                async function loadRegistriesViewTableMatrix() {{
                    // Pull real live state counts from python backend database first to display exact counts
                    let serverDb = {{}};
                    try {{
                        const res = await fetch('/admin/get_db');
                        serverDb = await res.json();
                    }} catch(e) {{}}

                    const localDb = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    
                    // Merge live server-side memory count data into frontend local storage configuration state
                    for(const key of Object.keys(localDb)) {{
                        if(serverDb[key]) {{
                            localDb[key].used = serverDb[key].used;
                            localDb[key].suspended = serverDb[key].suspended;
                            localDb[key].deleted = serverDb[key].deleted;
                        }}
                    }}
                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(localDb));

                    const targetBody = document.getElementById('registryTableElementRows');
                    targetBody.innerHTML = '';
                    const nowIST = getSystemIstDateObject();
                    
                    for(const [key, profile] of Object.entries(localDb)) {{
                        if (profile.deleted === true) continue;

                        let timeStatusHtml = profile.expires_at;
                        let isExpired = false;
                        
                        if(profile.expires_at !== "Lifetime" && profile.expires_at !== "---") {{
                            const expiryTime = new Date(profile.expires_at.replace(' ', 'T'));
                            if(nowIST >= expiryTime) {{
                                isExpired = true;
                                timeStatusHtml = `<span class="text-red-500 font-bold animate-pulse">[EXPIRED]</span>`;
                            }}
                        }}

                        const isLimitReached = parseInt(profile.used) >= parseInt(profile.limit);
                        const quotaDisplay = isLimitReached 
                            ? `<span class="text-red-500 font-bold">${{profile.used}}/${{profile.limit}} [FINISHED]</span>`
                            : `<span class="text-green-400 font-bold">${{profile.used}}/${{profile.limit}}</span>`;

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
                                <td class="py-2.5 text-cyan-300 font-bold cursor-pointer border-b border-purple-950" onclick="selectKeyToSandbox('${{key}}')">${{key}}</td>
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

                function selectKeyToSandbox(key) {{
                    document.getElementById('targetSandboxKeyField').value = key;
                }}

                async function toggleKeySuspensionState(key, setSuspended) {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(db[key]) {{
                        db[key].suspended = setSuspended;
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        await syncKeyToServerRegistry(key, db[key]);
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                async function resetKeyQuotaCounter(key) {{
                    const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    if(db[key]) {{
                        db[key].used = 0; 
                        localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                        await syncKeyToServerRegistry(key, db[key]);
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                async function purgeKey(key) {{
                    if(confirm(`Completely destroy authorization registry for key: "${{key}}"?`)) {{
                        const db = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                        if(db[key]) {{
                            db[key].deleted = true; 
                            localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(db));
                            await syncKeyToServerRegistry(key, db[key]);
                        }}
                        loadRegistriesViewTableMatrix();
                    }}
                }}

                async function commitNewTokenToRegistry(e) {{
                    e.preventDefault();
                    const name = document.getElementById('inputClientName').value;
                    const key = document.getElementById('inputLicenseKey').value.trim();
                    const limit = parseInt(document.getElementById('inputQuotaLimit').value);
                    const expiryTime = document.getElementById('expiryPreviewDisplay').innerText;
                    
                    const activeDb = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    const newProfile = {{ name, limit, used: 0, expires_at: expiryTime, allowed_tools: compileScopes(), suspended: false, deleted: false }};
                    
                    activeDb[key] = newProfile;
                    localStorage.setItem('NEXUS_REGISTRIES_DATABASE', JSON.stringify(activeDb));
                    
                    await syncKeyToServerRegistry(key, newProfile);

                    document.getElementById('tokenGenerationForm').reset();
                    triggerKeyGen();
                    document.getElementById('expiryModeSelector').value = "custom";
                    toggleExpiryInputView();
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

                    if(!key) return alert("Please select or write a valid execution API key token!");
                    
                    terminal.classList.remove('hidden');
                    terminal.innerText = "Transmitting framework routing packets downstream...";

                    const url = `/api/${{endpoint}}?key=${{key}}&num=7003741482`;

                    try {{
                        const res = await fetch(url);
                        const data = await res.json();
                        terminal.innerText = JSON.stringify(data, null, 4);
                    }} catch(e) {{ 
                        terminal.innerText = "Error framework stack: " + e.toString(); 
                    }}
                    await loadRegistriesViewTableMatrix();
                    syncTelemetryLogsFeed();
                }}

                async function syncTelemetryLogsFeed() {{
                    try {{
                        const response = await fetch('/admin/logs');
                        const data = await response.json();
                        const logsTbody = document.getElementById('telemetryPacketStreamBodyRows');
                        logsTbody.innerHTML = '';

                        if(!data.logs || data.logs.length === 0) {{
                            logsTbody.innerHTML = `<tr><td colspan="4" class="py-3 text-center text-gray-700">No runtime traffic analyzed yet.</td></tr>`;
                            return;
                        }}

                        data.logs.forEach(log => {{
                            logsTbody.innerHTML += `
                                <tr class="border-b border-gray-950 hover:bg-gray-900 transition-colors">
                                    <td class="py-1.5 text-gray-500">${{log.timestamp}}</td>
                                    <td class="py-1.5 text-yellow-500 font-bold">${{log.key}}</td>
                                    <td class="py-1.5 text-cyan-400">/api/${{log.endpoint}}</td>
                                    <td class="py-1.5 text-purple-300 max-w-xs truncate" title="${{log.params}}">${{log.params}}</td>
                                </tr>
                            `;
                        }});
                    }} catch(e) {{}}
                }}

                // Push current local items to server memory stack upon page wake initialization
                async function syncAllStoredKeysOnStartup() {{
                    const localDb = JSON.parse(localStorage.getItem('NEXUS_REGISTRIES_DATABASE') || '{{}}');
                    for (const [key, profile] of Object.entries(localDb)) {{
                        await syncKeyToServerRegistry(key, profile);
                    }}
                }}

                window.onload = async function() {{
                    triggerKeyGen();
                    const now = new Date();
                    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
                    document.getElementById('inputCustomDateTime').value = now.toISOString().slice(0,16);
                    
                    toggleExpiryInputView();
                    await syncAllStoredKeysOnStartup();
                    await loadRegistriesViewTableMatrix();
                    syncTelemetryLogsFeed();
                    
                    // Periodic auto sync update checking loops
                    setInterval(loadRegistriesViewTableMatrix, 3000);
                    setInterval(syncTelemetryLogsFeed, 4000);
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
