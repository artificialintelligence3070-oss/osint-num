import os
import httpx
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string

# ---- CORE SYSTEM GATEWAY SETTINGS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "@vernexzz"
CHANNEL_URL = "https://t.me/shayan_explorer_channel"

# ---- SECURE CLOUD STORAGE GATEWAY ----
BIN_ID = "66f4c5e2a1b2c3d4e5f6a7b8"  
KV_DATABASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": "$2a$10$ExAmPlEkEyHeReDoNoTsHaReThIsStRiNg12345"} 

CORE_API_ENDPOINTS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", "number", 
    "pincode", "ip", "challan", "ff", "bgmi", "snap", "email", 
    "vehicle", "git", "insta", "tg", "tgidinfo", "numleak", "pk", 
    "name", "aadhar", "numtoupi", "pan", "veh2num", "adharfamily", "bomber"
]

GLOBAL_REGISTRY_BUFFER = {}
GLOBAL_LOGS_BUFFER = []
HAS_INITIALIZED = False

app = Flask(__name__)
app.url_map.strict_slashes = False

# ---- PERFECT TIMEZONE ENGINE ----
def get_current_ist() -> datetime:
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def fetch_cloud_state():
    global GLOBAL_REGISTRY_BUFFER, GLOBAL_LOGS_BUFFER, HAS_INITIALIZED
    if not HAS_INITIALIZED:
        try:
            with httpx.Client() as client:
                response = client.get(KV_DATABASE_URL, headers=HEADERS, timeout=3.5)
                if response.status_code == 200:
                    cloud_data = response.json().get("record", {})
                    reg = cloud_data.get("registry", {})
                    logs = cloud_data.get("logs", [])
                    if isinstance(reg, dict): GLOBAL_REGISTRY_BUFFER = reg
                    if isinstance(logs, list): GLOBAL_LOGS_BUFFER = logs
                    HAS_INITIALIZED = True
        except Exception:
            pass
    return GLOBAL_REGISTRY_BUFFER, GLOBAL_LOGS_BUFFER

def push_cloud_state(registry, logs):
    global GLOBAL_REGISTRY_BUFFER, GLOBAL_LOGS_BUFFER
    GLOBAL_REGISTRY_BUFFER = registry
    GLOBAL_LOGS_BUFFER = logs
    try:
        with httpx.Client() as client:
            client.put(KV_DATABASE_URL, json={"registry": registry, "logs": logs}, headers=HEADERS, timeout=3.5)
    except Exception:
        pass

def scrub_legacy_branding(data):
    if isinstance(data, dict):
        for k, v in list(data.items()):
            if isinstance(v, str):
                v_lower = v.lower()
                if any(x in v_lower for x in ["ftgamer", "bronex", "lynx_api"]):
                    if k == "by": data[k] = DEVELOPER_NAME
                    elif k == "channel": data[k] = CHANNEL_URL
                    else: data[k] = v.replace("@ftgamer2", DEVELOPER_NAME).replace("https://t.me/lynx_api", CHANNEL_URL).replace("@BronexUltra", DEVELOPER_NAME)
            else:
                scrub_legacy_branding(v)
    elif isinstance(data, list):
        for item in data: scrub_legacy_branding(item)
    return data

# --- HTML ADVANCED CYBER UI MATRIX ---
@app.route('/', methods=['GET'])
def render_dashboard_panel():
    try:
        checkbox_grid_html = "".join([f"""
        <div class="relative">
            <input type="checkbox" id="scope_{tool}" value="{tool}" class="hidden api-checkbox individual-scope">
            <label for="scope_{tool}" class="block text-center p-1.5 rounded border border-gray-800 font-mono text-gray-500 bg-black cursor-pointer transition text-[10px] uppercase">{tool}</label>
        </div>
        """ for tool in CORE_API_ENDPOINTS])

        sandbox_grid_html = "".join([f"""
        <button type="button" id="sandbox_btn_{tool}" onclick="bindSandboxTarget(this, '{tool}')" class="p-1.5 rounded border border-gray-900 bg-black text-center font-mono text-[10px] uppercase tracking-wider text-gray-500 {'active' if idx == 0 else ''}">{tool}</button>
        """ for idx, tool in enumerate(CORE_API_ENDPOINTS)])

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Nexus Cyber Ops Terminal v4</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ background-color: #020205; color: #00ffcc; font-family: 'Courier New', Courier, monospace; }}
                .glow-panel-cyan {{ background: #040712; border: 1px solid #00ffcc; box-shadow: 0 0 15px rgba(0, 255, 204, 0.15); }}
                .glow-panel-purple {{ background: #060412; border: 1px solid #b5179e; box-shadow: 0 0 15px rgba(181, 23, 158, 0.15); }}
                input, select {{ background-color: #000000 !important; color: #00ffcc !important; border: 1px solid #333 !important; font-weight: bold; }}
                input:focus, select:focus {{ border-color: #00ffcc !important; box-shadow: 0 0 8px #00ffcc; }}
                .tool-btn {{ background: #000; border: 1px solid #222; }}
                .tool-btn.active {{ border-color: #00ffcc !important; color: #00ffcc !important; box-shadow: 0 0 8px #00ffcc; }}
                .api-checkbox:checked + label {{ border-color: #b5179e !important; color: #ff007f !important; box-shadow: 0 0 8px #b5179e; background: rgba(181, 23, 158, 0.1); }}
                .neon-btn-green {{ background: #000; border: 1px solid #00ff66; color: #00ff66; text-shadow: 0 0 5px #00ff66; transition: all 0.2s; }}
                .neon-btn-green:hover {{ background: #00ff66; color: #000; box-shadow: 0 0 15px #00ff66; }}
                
                @keyframes warningBlink {{ 0%, 100% {{ opacity: 1; color: #eab308; }} 50% {{ opacity: 0.4; color: #854d0e; }} }}
                @keyframes criticalBlink {{ 0%, 100% {{ opacity: 1; color: #ef4444; }} 50% {{ opacity: 0.2; color: #7f1d1d; }} }}
                .blink-warning {{ animation: warningBlink 1.2s infinite; font-weight: bold; }}
                .blink-critical {{ animation: criticalBlink 0.8s infinite; font-weight: bold; }}
                ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
                ::-webkit-scrollbar-thumb {{ background: #00ffcc; }}
            </style>
        </head>
        <body class="p-2 sm:p-4 min-h-screen">

            <!-- PROTECTION AUTH GATEWAY -->
            <div id="cyberAuthShieldGateway" class="fixed inset-0 z-50 bg-black flex items-center justify-center p-4">
                <div class="w-full max-w-md p-6 rounded-xl border border-cyan-500 bg-gray-950 shadow-2xl space-y-4">
                    <div class="text-center">
                        <h2 class="text-xl font-bold tracking-widest text-cyan-400" style="text-shadow: 0 0 8px #00ffff;">TERMINAL AUTH SHIELD</h2>
                        <p class="text-xs text-purple-400 mt-1 font-mono">AUTHORIZED PERSONNEL ONLY</p>
                    </div>
                    <hr class="border-cyan-900">
                    <form onsubmit="verifyGatewayCredentials(event)" class="space-y-3 text-xs font-mono">
                        <div>
                            <label class="block text-gray-400 mb-1">SECURE IDENTITY SPEC</label>
                            <input type="text" id="authGatewayUser" placeholder="Username" required class="w-full p-2.5 rounded">
                        </div>
                        <div>
                            <label class="block text-gray-400 mb-1">ACCESS CODE MAPPING</label>
                            <input type="password" id="authGatewayPass" placeholder="Password" required class="w-full p-2.5 rounded">
                        </div>
                        <div id="authGatewayErrorMessage" class="hidden text-red-500 font-bold text-center animate-pulse pt-1">
                            ❌ ACCESS VIOLATION: INVALID TERMINAL SIGNATURE!
                        </div>
                        <button type="submit" class="w-full neon-btn-green font-bold py-2.5 rounded uppercase tracking-widest">INITIATE ENGINE OVERRIDE</button>
                    </form>
                </div>
            </div>

            <!-- MAIN OPS INTERFACE WIDGET -->
            <div id="terminalAppMainWrapper" class="hidden max-w-7xl mx-auto space-y-4">
                
                <header class="flex flex-col sm:flex-row justify-between items-center border-b border-cyan-900 pb-3 gap-2">
                    <div class="text-center sm:text-left">
                        <h1 class="text-2xl font-bold tracking-widest text-cyan-400" style="text-shadow: 0 0 12px #00ffff;">NEXUS COMMAND CENTER V4</h1>
                        <div class="text-xs font-mono text-purple-400">LEAD ARCHITECT: <a href="{CHANNEL_URL}" target="_blank" class="underline font-bold text-cyan-300">{DEVELOPER_NAME}</a></div>
                    </div>
                    <!-- METRICS ENGINE ANALYTICS BOARD -->
                    <div class="grid grid-cols-4 gap-2 text-[10px] font-mono">
                        <div class="bg-gray-950 border border-cyan-900 px-2 py-1 rounded text-center">TOTAL: <span id="mTotal" class="text-white font-bold">0</span></div>
                        <div class="bg-gray-950 border border-green-900 px-2 py-1 rounded text-center">LIVE: <span id="mActive" class="text-green-400 font-bold">0</span></div>
                        <div class="bg-gray-950 border border-yellow-900 px-2 py-1 rounded text-center">WARN: <span id="mWarn" class="text-yellow-400 font-bold">0</span></div>
                        <div class="bg-gray-950 border border-red-900 px-2 py-1 rounded text-center">LOCK: <span id="mLock" class="text-red-500 font-bold">0</span></div>
                    </div>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <!-- LEFT COLUMN PANEL: CREATION CONTROLS -->
                    <div class="glow-panel-cyan p-4 rounded-xl space-y-4">
                        <form id="tokenGenerationForm" onsubmit="commitNewTokenToRegistry(event)" class="space-y-3 text-xs">
                            <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-wider border-b border-cyan-900 pb-1.5">INJECT LICENSE RECORD</h2>
                            
                            <div>
                                <label class="block text-gray-400 mb-0.5 font-mono">CLIENT IDENTITY TAG</label>
                                <input type="text" id="inputClientName" placeholder="Client Name / ID" required class="w-full rounded p-2 font-mono">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-0.5 font-mono">LICENSE TOKEN ROUTE</label>
                                <div class="flex gap-2">
                                    <input type="text" id="inputLicenseKey" placeholder="VX-XXXXX" required class="w-full rounded p-2 font-mono text-yellow-400">
                                    <button type="button" onclick="triggerKeyGen()" class="bg-gray-900 border border-cyan-600 px-3 rounded font-mono text-cyan-400">AUTO</button>
                                </div>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-gray-400 mb-0.5 font-mono">EXPIRY METHOD</label>
                                    <select id="expiryModeSelector" onchange="toggleExpiryInputView()" class="w-full rounded p-2 bg-black font-mono">
                                        <option value="custom">Custom Clock Target</option>
                                        <option value="lifetime">Lifetime Access</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-gray-400 mb-0.5 font-mono">QUOTA THROTTLE</label>
                                    <input type="number" id="inputQuotaLimit" value="100" required class="w-full rounded p-2 font-mono">
                                </div>
                            </div>

                            <div id="customDateTimePickerBox">
                                <label class="block text-gray-400 mb-0.5 font-mono">CHOOSE EXPIRY (STRICT INDIAN TIME - IST)</label>
                                <input type="datetime-local" id="inputCustomDateTime" oninput="updateCalculatedExpiry()" onchange="updateCalculatedExpiry()" class="w-full rounded p-2 font-mono text-green-400">
                            </div>

                            <div class="p-2 bg-black border border-cyan-900 rounded text-[11px] font-mono">
                                <span class="text-purple-400">TARGET LOCKED CLOCK (IST):</span>
                                <div id="expiryPreviewDisplay" class="text-green-400 font-bold mt-0.5">---</div>
                            </div>

                            <div>
                                <label class="block text-gray-400 mb-1 text-[10px] font-mono">MODULE MATRIX RIGHTS</label>
                                <div class="max-h-32 overflow-y-auto border border-cyan-950 p-2 rounded space-y-1.5 bg-black">
                                    <input type="checkbox" id="scope_all" value="all" checked onchange="handleAllScopeToggle(this)" class="hidden api-checkbox">
                                    <label for="scope_all" class="block text-center p-1 rounded tool-btn cursor-pointer text-purple-400 bg-gray-950 border border-purple-900 font-bold">⭐ UNRESTRICTED ALL ACCESS</label>
                                    <div class="grid grid-cols-2 gap-1">{checkbox_grid_html}</div>
                                </div>
                            </div>

                            <button type="submit" class="w-full neon-btn-green font-bold py-2.5 rounded uppercase tracking-widest text-xs">COMMIT KEY DATA</button>
                        </form>

                        <!-- DEVELOPER CONFIG MATRIX CONFIGURATOR -->
                        <div class="border border-purple-900 p-3 rounded bg-black bg-opacity-40 space-y-2 text-[11px]">
                            <h3 class="text-purple-400 font-bold uppercase tracking-wider text-[10px] border-b border-purple-9ENTIAL pb-1">Live Engine Switchboard</h3>
                            <div>
                                <label class="text-gray-500 block">Upstream Gateway Endpoint</label>
                                <input type="text" id="cfgBaseUrl" value="{TARGET_BASE_URL}" class="w-full p-1 rounded text-xs opacity-70">
                            </div>
                            <button onclick="alert('Engine Pipeline Variables Cached Locally!')" class="w-full bg-purple-950 text-purple-300 border border-purple-700 py-1 rounded text-[10px]">Update Core Routing Parameters</button>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN PANEL: SEARCH, CONTROLS, DATABASE -->
                    <div class="lg:col-span-2 glow-panel-purple p-4 rounded-xl flex flex-col h-[580px] space-y-3">
                        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-purple-900 pb-2">
                            <h2 class="text-xs font-bold text-purple-400 uppercase tracking-wider">ACTIVE ACCESS REGISTRY REPOSITORY</h2>
                            <!-- SEARCH FIELD SYSTEM -->
                            <div class="w-full sm:w-auto">
                                <input type="text" id="databaseSearchQueryField" oninput="triggerDatabaseLocalFilter()" placeholder="🔍 Quick Filter Registry..." class="w-full sm:w-48 p-1.5 rounded text-xs">
                            </div>
                        </div>

                        <!-- BULK ACTIONS MANAGER TOOLBOX -->
                        <div class="flex flex-wrap gap-2 p-2 bg-black border border-purple-950 rounded text-[10px]">
                            <span class="text-gray-500 font-bold self-center mr-1">BULK CONTROLS:</span>
                            <button onclick="executeBulkOperation('purge_expired')" class="bg-red-950 text-red-400 border border-red-800 px-2 py-0.5 rounded hover:bg-red-900">Purge Expired Keys</button>
                            <button onclick="executeBulkOperation('reset_quota')" class="bg-blue-950 text-blue-400 border border-blue-800 px-2 py-0.5 rounded hover:bg-blue-900">Reset All Quotas</button>
                            <button onclick="triggerDatabaseExport()" class="bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded hover:bg-cyan-900 ml-auto">📦 Export DB Backup</button>
                        </div>

                        <div class="overflow-x-auto overflow-y-auto flex-1 w-full text-[11px]">
                            <table class="w-full text-left min-w-[760px]">
                                <thead>
                                    <tr class="border-b border-purple-950 text-gray-500 font-mono text-[10px]">
                                        <th class="pb-1.5">CLIENT TARGET</th>
                                        <th class="pb-1.5">KEY SIGNATURE SECURE TOKEN</th>
                                        <th class="pb-1.5">QUOTA HITS</th>
                                        <th class="pb-1.5">EXPIRY OR RE-ALERTS (IST)</th>
                                        <th class="pb-1.5">STATUS</th>
                                        <th class="pb-1.5 text-right">SYSTEM FRAMEWORK OPERATION</th>
                                    </tr>
                                </thead>
                                <tbody id="registryTableElementRows" class="divide-y divide-purple-950 font-mono"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- LIVE CONSOLE CONTROLS PIPELINE -->
                <div class="glow-panel-cyan p-4 rounded-xl space-y-2">
                    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-cyan-900 pb-1.5 gap-2">
                        <h2 class="text-xs font-bold text-cyan-400 tracking-wider">LIVE TELEMETRY TRAFFIC FEED SOCK PIPELINE</h2>
                        <div class="flex gap-2 w-full sm:w-auto">
                            <input type="text" id="logSearchQueryField" oninput="triggerLogLocalFilter()" placeholder="Filter logs..." class="p-1 text-xs rounded w-full sm:w-36">
                            <button onclick="refreshDashboardMatrix(true)" class="text-[10px] bg-black border border-cyan-600 text-cyan-400 px-2 py-1 rounded whitespace-nowrap">FORCE HARD SYNC</button>
                        </div>
                    </div>
                    <div class="overflow-x-auto max-h-40 text-[11px] font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-gray-500 border-b border-cyan-950 text-[10px]">
                                    <th class="pb-1">TIMESTAMP (IST)</th>
                                    <th class="pb-1">AUTHENTICATED KEY</th>
                                    <th class="pb-1">ENDPOINT MODULE</th>
                                    <th class="pb-1">INJECTED STRUCT DETECTED PARAMETERS</th>
                                </tr>
                            </thead>
                            <tbody id="telemetryPacketStreamBodyRows" class="divide-y divide-gray-950 text-cyan-300">
                                <tr><td colspan="4" class="py-3 text-center text-gray-700">Connecting telemetry pipeline grid nodes...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- INTEGRATION HELPER MATRIX SCRIPT BUILDER -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- CYBERATTACK SANDBOX TESTING UNIT -->
                    <div class="glow-panel-cyan p-4 rounded-xl space-y-3">
                        <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-wider border-b border-cyan-900 pb-1">PROBE REQUEST SIMULATOR CONSOLE</h2>
                        <div class="grid grid-cols-4 sm:grid-cols-7 gap-1 text-[9px]">{sandbox_grid_html}</div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] items-end">
                            <div>
                                <label class="block text-gray-500 mb-0.5">TARGET</label>
                                <input type="text" id="targetSandboxPathField" value="adv" class="w-full rounded p-1.5" readonly>
                            </div>
                            <div>
                                <label class="block text-gray-500 mb-0.5">INJECTED API KEY</label>
                                <input type="text" id="targetSandboxKeyField" class="w-full rounded p-1.5 text-yellow-400" placeholder="Click key signature token...">
                            </div>
                            <button onclick="executeSandboxProbeRequest()" class="w-full neon-btn-green py-1.5 rounded font-bold text-xs uppercase">EXECUTE REQUEST</button>
                        </div>
                        <div id="sandboxResponseTerminal" class="hidden p-2 bg-black border border-cyan-900 rounded font-mono text-[10px] text-green-400 max-h-48 overflow-y-auto whitespace-pre-wrap"></div>
                    </div>

                    <!-- CLIENT API INTEGRATION SNIPPETS GENERATOR -->
                    <div class="glow-panel-purple p-4 rounded-xl space-y-3 flex flex-col justify-between">
                        <div>
                            <h2 class="text-xs font-bold text-purple-400 uppercase tracking-wider border-b border-purple-900 pb-1 mb-2">Automated SDK Client Documentation Builder</h2>
                            <div class="flex gap-2 text-[10px] font-mono mb-2">
                                <button onclick="renderIntegrationCodeSnippet('curl')" class="px-2 py-0.5 bg-purple-950 rounded border border-purple-700 text-purple-300">cURL Request</button>
                                <button onclick="renderIntegrationCodeSnippet('python')" class="px-2 py-0.5 bg-purple-950 rounded border border-purple-700 text-purple-300">Python Script</button>
                                <button onclick="renderIntegrationCodeSnippet('node')" class="px-2 py-0.5 bg-purple-950 rounded border border-purple-700 text-purple-300">NodeJS Framework</button>
                            </div>
                            <pre id="codeSnippetTerminalBox" class="p-2 bg-black border border-purple-950 rounded text-[9px] text-purple-300 font-mono whitespace-pre overflow-x-auto min-h-[100px]">Select any client payload structure blueprint to copy...</pre>
                        </div>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('codeSnippetTerminalBox').innerText); alert('Snippet Copied!')" class="w-full border border-purple-500 bg-black text-purple-400 text-xs py-1 rounded hover:bg-purple-950 font-mono">📋 Copy Snippet Frame Payload</button>
                    </div>
                </div>

                <footer class="text-center text-[11px] font-mono text-gray-600 pt-2 border-t border-gray-950">
                    <p>CORE GATEWAY DEPLOYMENT OK &bull; SYSTEMS OPERATIONAL UNDER <span class="text-cyan-500 font-bold">{DEVELOPER_NAME}</span></p>
                </footer>

            </div>

            <script>
                let METADATA_REGISTRY_CACHE = {{}};
                let METADATA_LOGS_CACHE = [];

                function verifyGatewayCredentials(event) {{
                    event.preventDefault();
                    if (document.getElementById('authGatewayUser').value.trim() === "vernex" && document.getElementById('authGatewayPass').value.trim() === "vernex@16vx") {{
                        sessionStorage.setItem("NEXUS_SESSION_GATE", "GRANTED");
                        document.getElementById('cyberAuthShieldGateway').style.display = "none";
                        document.getElementById('terminalAppMainWrapper').classList.remove('hidden');
                        initializeSystemDashboardCore();
                    }} else {{
                        document.getElementById('authGatewayErrorMessage').classList.remove('hidden');
                        document.getElementById('authGatewayPass').value = "";
                    }}
                }}

                function toggleExpiryInputView() {{
                    document.getElementById('customDateTimePickerBox').style.display = (document.getElementById('expiryModeSelector').value === "lifetime") ? "none" : "block";
                    updateCalculatedExpiry();
                }}

                function updateCalculatedExpiry() {{
                    if(document.getElementById('expiryModeSelector').value === "lifetime") {{
                        document.getElementById('expiryPreviewDisplay').innerText = "Lifetime";
                        return;
                    }}
                    const val = document.getElementById('inputCustomDateTime').value;
                    if(!val) return document.getElementById('expiryPreviewDisplay').innerText = "---";
                    const d = new Date(val);
                    document.getElementById('expiryPreviewDisplay').innerText = isNaN(d.getTime()) ? "---" : formatIstString(d);
                }}

                function formatIstString(d) {{
                    return `${{d.getFullYear()}}-${{String(d.getMonth()+1).padStart(2,'0')}}-${{String(d.getDate()).padStart(2,'0')}} ${{String(d.getHours()).padStart(2,'0')}}:${{String(d.getMinutes()).padStart(2,'0')}}:00`;
                }}

                function handleAllScopeToggle(master) {{
                    document.querySelectorAll('.individual-scope').forEach(box => {{ box.checked = false; box.disabled = master.checked; }});
                }}

                function compileScopes() {{
                    if(document.getElementById('scope_all').checked) return "all";
                    let checked = [];
                    document.querySelectorAll('.individual-scope').forEach(box => {{ if(box.checked) checked.push(box.value); }});
                    return checked.length > 0 ? checked.join(', ') : "all";
                }}

                // ---- ALERTS ENGINE MODULE WITH CONDITIONAL CRITICAL MAPPINGS ----
                function buildDynamicExpiryMessage(expiresAtStr) {{
                    if (expiresAtStr === "Lifetime" || expiresAtStr === "---") {{
                        return `<span class="text-cyan-400 font-bold tracking-widest uppercase text-[10px]">🧬 Lifetime Key</span>`;
                    }}

                    // কারেন্ট ডেট অবজেক্ট জেনারেট (Perfect User Context IST Clock Mapping)
                    const nowIST = new Date(new Date().getTime() + (3600000 * 5.5));
                    const targetDate = new Date(expiresAtStr.replace(' ', 'T'));
                    const diffMs = targetDate - nowIST;

                    // ১. এক্সপায়ার হয়ে গেলে সম্পূর্ণ রে‍ড ব্লিংকিং লকড সাইন শো করবে
                    if (diffMs <= 0) {{
                        return `<span class="blink-critical">🔒 LOCK: KEY EXPIRED</span>`;
                    }}

                    const totalSeconds = Math.floor(diffMs / 1000);
                    const diffDays = diffMs / (1000 * 60 * 60 * 24);

                    // ২. এক্সপায়ার হতে ২৪ ঘণ্টার কম বাকি থাকলে টাইমার কাউন্টডাউন শো করবে
                    if (diffMs <= 86400000) {{
                        const hours = Math.floor(totalSeconds / 3600);
                        const mins = Math.floor((totalSeconds % 3600) / 60);
                        const secs = totalSeconds % 60;
                        return `<span class="blink-warning bg-yellow-950 bg-opacity-40 px-1.5 py-0.5 border border-yellow-800 rounded">
                            ⚠️ Expiring within: ${{hours}}h ${{mins}}m ${{secs}}s
                        </span>`;
                    }}

                    // ৩. এক্সপায়ার হতে ১ থেকে ৩ দিন বাকি থাকলে ইয়োলো অ্যালার্ট মেসেজ ব্লিংক করবে
                    if (diffDays <= 3.0) {{
                        return `<span class="blink-warning text-yellow-400">⚠️ Expiring soon (${{expiresAtStr}})</span>`;
                    }}

                    // ৪. ৩ দিনের বেশি সময় বাকি থাকলে সাধারণ গ্রিন টেক্সট শো করবে
                    return `<span class="text-green-400">${{expiresAtStr}}</span>`;
                }}

                async function refreshDashboardMatrix(forceCloudFetch = false) {{
                    try {{
                        const res = await fetch('/admin/get_db');
                        const serverData = await res.json();
                        METADATA_REGISTRY_CACHE = serverData.registry || {{}};
                        METADATA_LOGS_CACHE = serverData.logs || [];
                        
                        renderRegistryTableRows(METADATA_REGISTRY_CACHE);
                        renderTelemetryLogsRows(METADATA_LOGS_CACHE);
                        updateSystemAnalyticsCounter(METADATA_REGISTRY_CACHE);
                    }} catch(e) {{ console.error(e); }}
                }}

                function renderRegistryTableRows(registryMap) {{
                    const tableBody = document.getElementById('registryTableElementRows');
                    tableBody.innerHTML = '';
                    const nowIST = new Date(new Date().getTime() + (3600000 * 5.5));

                    for(const [key, profile] of Object.entries(registryMap)) {{
                        const rawExpiry = profile.expires_at || "Lifetime";
                        const timeDisplayHtml = buildDynamicExpiryMessage(rawExpiry);
                        
                        let isExpired = (rawExpiry !== "Lifetime" && rawExpiry !== "---" && nowIST >= new Date(rawExpiry.replace(' ', 'T')));
                        const isLimitReached = parseInt(profile.used) >= parseInt(profile.limit);
                        const isSuspended = profile.suspended === true || profile.suspended === "true";

                        const quotaHtml = isLimitReached 
                            ? `<span class="text-red-500 font-bold">${{profile.used}}/${{profile.limit}}</span>`
                            : `<span class="text-green-400 font-bold">${{profile.used}}/${{profile.limit}}</span>`;

                        let badge = `<span class="text-green-400 border border-green-500 px-1 py-0.5 rounded text-[9px] bg-green-950 bg-opacity-20">ACTIVE</span>`;
                        if(isSuspended) badge = `<span class="text-yellow-500 border border-yellow-500 px-1 py-0.5 rounded text-[9px] bg-yellow-950 bg-opacity-20">SUSPENDED</span>`;
                        else if(isExpired || isLimitReached) badge = `<span class="text-red-500 border border-red-500 px-1 py-0.5 rounded text-[9px] bg-red-950 bg-opacity-20">LOCKED</span>`;

                        const suspendAction = isSuspended
                            ? `<button onclick="updateKeyCloudState('${{key}}', 'unsuspend')" class="text-green-400 hover:underline">UNSUSPEND</button>`
                            : `<button onclick="updateKeyCloudState('${{key}}', 'suspend')" class="text-yellow-500 hover:underline">SUSPEND</button>`;

                        tableBody.innerHTML += `
                            <tr class="hover:bg-purple-950 hover:bg-opacity-20 transition-colors data-row-item" data-key="${{key.toLowerCase()}}" data-name="${{profile.name.toLowerCase()}}">
                                <td class="py-2 text-white font-bold border-b border-purple-950">${{profile.name}}</td>
                                <td class="py-2 text-cyan-300 font-bold cursor-pointer border-b border-purple-950" onclick="selectKeyToSandbox('${{key}}')">${{key}}</td>
                                <td class="py-2 border-b border-purple-950">${{quotaHtml}}</td>
                                <td class="py-2 border-b border-purple-950 text-[10px]">${{timeDisplayHtml}}</td>
                                <td class="py-2 border-b border-purple-950">${{badge}}</td>
                                <td class="py-2 text-right text-[10px] border-b border-purple-950 space-x-1.5">
                                    ${{suspendAction}}
                                    <button onclick="editKeyDirectly('${{key}}', \`${{JSON.stringify(profile)}}\`)" class="text-purple-400 hover:underline">EDIT</button>
                                    <button onclick="updateKeyCloudState('${{key}}', 'relimit')" class="text-blue-400 hover:underline">RESET</button>
                                    <button onclick="updateKeyCloudState('${{key}}', 'delete')" class="text-red-500 hover:underline font-bold">DELETE</button>
                                </td>
                            </tr>
                        `;
                    }}
                }

                function renderTelemetryLogsRows(logsArray) {{
                    const logsBody = document.getElementById('telemetryPacketStreamBodyRows');
                    if(logsArray.length === 0) {{
                        logsBody.innerHTML = `<tr><td colspan="4" class="py-3 text-center text-gray-700">No logs found.</td></tr>`;
                        return;
                    }}
                    logsBody.innerHTML = logsArray.map(log => `
                        <tr class="border-b border-gray-950 hover:bg-gray-900 data-log-item" data-search="${{log.key.toLowerCase()}} ${{log.endpoint.toLowerCase()}}">
                            <td class="py-1 text-gray-500 text-[10px]">${{log.timestamp}}</td>
                            <td class="py-1 text-yellow-500 font-bold">${{log.key}}</td>
                            <td class="py-1 text-cyan-400">/api/${{log.endpoint}}</td>
                            <td class="py-1 text-purple-300 truncate max-w-xs" title="${{log.params}}">${{log.params}}</td>
                        </tr>
                    `).join('');
                }}

                function updateSystemAnalyticsCounter(reg) {{
                    let total = Object.keys(reg).length;
                    let active = 0, warn = 0, lock = 0;
                    const nowIST = new Date(new Date().getTime() + (3600000 * 5.5));

                    for(const p of Object.values(reg)) {{
                        const rawExpiry = p.expires_at || "Lifetime";
                        let isExpired = (rawExpiry !== "Lifetime" && rawExpiry !== "---" && nowIST >= new Date(rawExpiry.replace(' ', 'T')));
                        let isLimitReached = parseInt(p.used) >= parseInt(p.limit);
                        
                        if(p.suspended || isExpired || isLimitReached) lock++;
                        else if (rawExpiry !== "Lifetime" && rawExpiry !== "---" && (new Date(rawExpiry.replace(' ', 'T')) - nowIST) <= 259200000) warn++;
                        else active++;
                    }}
                    document.getElementById('mTotal').innerText = total;
                    document.getElementById('mActive').innerText = active;
                    document.getElementById('mWarn').innerText = warn;
                    document.getElementById('mLock').innerText = lock;
                }}

                // ---- INTUITIVE INSTANT SEARCH FILTERS ----
                function triggerDatabaseLocalFilter() {{
                    let query = document.getElementById('databaseSearchQueryField').value.toLowerCase().trim();
                    document.querySelectorAll('.data-row-item').forEach(tr => {{
                        let match = tr.getAttribute('data-key').includes(query) || tr.getAttribute('data-name').includes(query);
                        tr.style.display = match ? '' : 'none';
                    }});
                }}

                function triggerLogLocalFilter() {{
                    let query = document.getElementById('logSearchQueryField').value.toLowerCase().trim();
                    document.querySelectorAll('.data-log-item').forEach(tr => {{
                        tr.style.display = tr.getAttribute('data-search').includes(query) ? '' : 'none';
                    }});
                }}

                // ---- BULK OPERATIONS ENGINE INTERFACE ----
                async function executeBulkOperation(action) {{
                    if(!confirm("Are you sure you want to execute this destructive bulk matrix command?")) return;
                    let updatedRegistry = {{...METADATA_REGISTRY_CACHE}};
                    const nowIST = new Date(new Date().getTime() + (3600000 * 5.5));

                    if(action === 'purge_expired') {{
                        for(const [k, p] of Object.entries(updatedRegistry)) {{
                            if(p.expires_at !== "Lifetime" && p.expires_at !== "---" && nowIST >= new Date(p.expires_at.replace(' ', 'T'))) {{
                                delete updatedRegistry[k];
                            }}
                        }}
                    }} else if(action === 'reset_quota') {{
                        for(const k of Object.keys(updatedRegistry)) updatedRegistry[k].used = 0;
                    }}

                    await fetch('/admin/sync_all', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ registry: updatedRegistry }})
                    }});
                    await refreshDashboardMatrix();
                }}

                function triggerDatabaseExport() {{
                    let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(METADATA_REGISTRY_CACHE, null, 4));
                    let dlAnchor = document.createElement('a');
                    dlAnchor.setAttribute("href", dataStr);
                    dlAnchor.setAttribute("download", "nexus_db_backup_" + formatIstString(new Date()).replace(/[: ]/g, '_') + ".json");
                    document.body.appendChild(dlAnchor);
                    dlAnchor.click();
                    dlAnchor.remove();
                }}

                function renderIntegrationCodeSnippet(lang) {{
                    let key = document.getElementById('targetSandboxKeyField').value || "YOUR_CLIENT_KEY";
                    let ep = document.getElementById('targetSandboxPathField').value || "number";
                    let box = document.getElementById('codeSnippetTerminalBox');
                    let host = window.location.origin;

                    if(lang === 'curl') box.innerText = `curl -X GET "${{host}}/api/${{ep}}?key=${{key}}&num=7003741482"`;
                    else if(lang === 'python') box.innerText = `import requests\n\nurl = "${{host}}/api/${{ep}}"\nparams = {{"key": "${{key}}", "num": "7003741482"}}\nresponse = requests.get(url, params=params)\nprint(response.json())`;
                    else if(lang === 'node') box.innerText = `const axios = require('axios');\n\naxios.get('${{host}}/api/${{ep}}', {{\n    params: {{ key: '${{key}}', num: '7003741482' }}\n}})\n.then(res => console.log(res.data))\n.catch(err => console.error(err));`;
                }}

                async function updateKeyCloudState(key, action) {{
                    let registry = {{...METADATA_REGISTRY_CACHE}};
                    if(action === 'delete') {{ if(!confirm(`Purge token "${{key}}"?`)) return; delete registry[key]; }}
                    else if(action === 'suspend') registry[key].suspended = true;
                    else if(action === 'unsuspend') registry[key].suspended = false;
                    else if(action === 'relimit') registry[key].used = 0;

                    await fetch('/admin/sync_all', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ registry: registry }}) }});
                    await refreshDashboardMatrix();
                }}

                async function commitNewTokenToRegistry(e) {{
                    e.preventDefault();
                    const name = document.getElementById('inputClientName').value;
                    const key = document.getElementById('inputLicenseKey').value.trim();
                    const limit = parseInt(document.getElementById('inputQuotaLimit').value);
                    const expiryTime = document.getElementById('expiryPreviewDisplay').innerText;

                    let registry = {{...METADATA_REGISTRY_CACHE}};
                    let historicalUsed = registry[key] ? parseInt(registry[key].used || 0) : 0;
                    registry[key] = {{ name: name, limit: limit, used: historicalUsed, expires_at: expiryTime, allowed_tools: compileScopes(), suspended: false }};

                    document.getElementById('tokenGenerationForm').reset();
                    triggerKeyGen();
                    document.getElementById('expiryModeSelector').value = "custom";
                    toggleExpiryInputView();

                    await fetch('/admin/sync_all', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ registry: registry }}) }});
                    setTimeout(refreshDashboardMatrix, 250);
                }}

                function editKeyDirectly(key, profileStr) {{
                    const profile = JSON.parse(profileStr);
                    document.getElementById('inputClientName').value = profile.name;
                    document.getElementById('inputLicenseKey').value = key;
                    document.getElementById('inputQuotaLimit').value = profile.limit;
                    if(profile.expires_at.includes("Lifetime")) {{
                        document.getElementById('expiryModeSelector').value = "lifetime";
                    }} else {{
                        document.getElementById('expiryModeSelector').value = "custom";
                        try {{ document.getElementById('inputCustomDateTime').value = profile.expires_at.substring(0,10) + 'T' + profile.expires_at.substring(11,16); }} catch(e) {{}}
                    }}
                    toggleExpiryInputView();
                    if(profile.allowed_tools === "all") {{
                        document.getElementById('scope_all').checked = true;
                    }} else {{
                        document.getElementById('scope_all').checked = false;
                        const tools = profile.allowed_tools.split(',').map(t => t.trim().toLowerCase());
                        document.querySelectorAll('.individual-scope').forEach(box => box.checked = tools.includes(box.value.toLowerCase()));
                    }}
                    handleAllScopeToggle(document.getElementById('scope_all'));
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }}

                function selectKeyToSandbox(key) {{ document.getElementById('targetSandboxKeyField').value = key; renderIntegrationCodeSnippet('curl'); }}
                function triggerKeyGen() {{ document.getElementById('inputLicenseKey').value = "VX-" + Math.random().toString(36).substring(2,6).toUpperCase() + "-" + Math.random().toString(36).substring(2,6).toUpperCase(); }}
                function bindSandboxTarget(btn, path) {{ document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active'); document.getElementById('targetSandboxPathField').value = path; renderIntegrationCodeSnippet('curl'); }}

                async function executeSandboxProbeRequest() {{
                    const endpoint = document.getElementById('targetSandboxPathField').value;
                    const key = document.getElementById('targetSandboxKeyField').value.trim();
                    const terminal = document.getElementById('sandboxResponseTerminal');
                    if(!key) return alert("Select an active Key Signature Target!");
                    terminal.classList.remove('hidden'); terminal.innerText = "Injecting payload execution framework stream...";
                    try {{
                        const res = await fetch(`/api/${{endpoint}}?key=${{key}}&num=7003741482`);
                        terminal.innerText = JSON.stringify(await res.json(), null, 4);
                    }} catch(e) {{ terminal.innerText = "System Fault: " + e.toString(); }}
                    await refreshDashboardMatrix();
                }}

                async function initializeSystemDashboardCore() {{
                    triggerKeyGen();
                    const now = new Date(); now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
                    document.getElementById('inputCustomDateTime').value = now.toISOString().slice(0,16);
                    toggleExpiryInputView();
                    await refreshDashboardMatrix();
                    setInterval(refreshDashboardMatrix, 1000); // ১ সেকেন্ড পরপর নিখুঁত লাইভ ক্লক টাইমার সিঙ্ক
                }}

                window.onload = function() {{
                    if (sessionStorage.getItem("NEXUS_SESSION_GATE") === "GRANTED") {{
                        document.getElementById('cyberAuthShieldGateway').style.display = "none";
                        document.getElementById('terminalAppMainWrapper').classList.remove('hidden');
                        initializeSystemDashboardCore();
                    }}
                }}
            </script>
        </body>
        </html>
        """
        return render_template_string(html_content)
    except Exception as e:
        return f"Dashboard Error: {str(e)}", 500

# --- ADMIN GATEWAYS ---
@app.route('/admin/sync_all', methods=['POST'])
def admin_sync_all():
    try:
        payload = request.get_json() or {}
        registry = payload.get("registry", {})
        _, current_logs = fetch_cloud_state()
        push_cloud_state(registry, current_logs)
        return jsonify({"status": "success", "count": len(registry)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin/get_db', methods=['GET'])
def admin_get_db():
    try:
        registry, logs = fetch_cloud_state()
        return jsonify({"registry": registry, "logs": logs})
    except Exception as e:
        return jsonify({"registry": {}, "logs": [], "error": str(e)})

# --- MAIN ENGINE API ROUTING PROCESSOR (STRICT USER TIMING ALGORITHMS) ---
@app.route('/api/<endpoint>', methods=['GET'])
def handle_api_routing(endpoint):
    try:
        client_key = request.args.get("key")
        registry, logs = fetch_cloud_state()

        if not client_key or client_key not in registry:
            return jsonify({"error": "Invalid API Key signature token. Purchase a new license profile."}), 403

        key_profile = registry[client_key]

        if str(key_profile.get("suspended")).lower() in ["true", "1", "yes"]:
            return jsonify({"error": "The key is suspended by the author or admin"}), 403

        # ---- STRICT IST TIME VALIDATION ENGINE ----
        key_expiry = key_profile.get("expires_at", "Lifetime")
        if "Lifetime" not in key_expiry and "---" not in key_expiry:
            try:
                current_time = get_current_ist()
                expiry_dt = datetime.strptime(key_expiry, "%Y-%m-%d %H:%M:%S")
                
                # যদি এক্সপায়ার টাইম পার হয়ে যায়, তবে স্ট্রিক্ট ব্লকিং রিকোয়েস্ট ফায়ার হবে
                if current_time >= expiry_dt:
                    return jsonify({"error": f"The key is expired on {key_expiry} (IST). Please buy a new key"}), 403
            except Exception:
                pass

        if int(key_profile.get("used", 0)) >= int(key_profile.get("limit", 100)):
            return jsonify({"error": "Your limit was finished. DM for new key purchased"}), 429

        allowed_tools = key_profile.get("allowed_tools", "all")
        if allowed_tools != "all":
            allowed_list = [t.strip().lower() for t in allowed_tools.split(",")]
            if endpoint.lower() not in allowed_list:
                return jsonify({"error": "Access Denied. Endpoint restriction active. DM for new key purchased"}), 403

        # কোটা ট্র্যাকিং হিট রেন্ডার
        registry[client_key]["used"] = int(registry[client_key].get("used", 0)) + 1
        
        cleaned_params = {k: v for k, v in request.args.items() if k != "key"}
        logs.insert(0, {
            "timestamp": get_current_ist().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })
        logs = logs[:100] # মেমোরি বাফার ক্যাশ ম্যানেজমেন্ট

        push_cloud_state(registry, logs)

        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        with httpx.Client() as client:
            response = client.get(upstream_url, params=cleaned_params, timeout=20.0)
            raw_response_json = response.json()
            scrubbed_response_json = scrub_legacy_branding(raw_response_json)
            return jsonify(scrubbed_response_json), response.status_code
    except Exception as e:
        return jsonify({"error": f"Internal Command Center Exception: {str(e)}"}), 500
