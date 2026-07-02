import os
import json
import datetime
import httpx
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="SHAYAN_EXPLORER API Gateway")

# --- ADMINISTRATIVE CREDENTIALS ---
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"
BASE_TARGET_URL = "https://ft-osint-api.duckdns.org/api"
DEFAULT_UPSTREAM_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

# --- PASTE YOUR UPSTASH REDIS DETAILS HERE ---
# This ensures your keys never delete themselves when Vercel restarts!
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "REPLACE_WITH_YOUR_UPSTASH_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "REPLACE_WITH_YOUR_UPSTASH_REST_TOKEN")

HEADERS = {"Authorization": f"Bearer {UPSTASH_TOKEN}"}

def db_get(key: str, default):
    """Fetch database records directly from cloud persistence layer."""
    try:
        with httpx.Client() as client:
            res = client.post(f"{UPSTASH_URL}/get/{key}", headers=HEADERS)
            data = res.json().get("result")
            return json.loads(data) if data else default
    except Exception as e:
        print(f"Cloud DB Read Error: {e}")
        return default

def db_set(key: str, value):
    """Commit configuration states safely into permanent cloud database clusters."""
    try:
        with httpx.Client() as client:
            client.post(f"{UPSTASH_URL}/set/{key}", content=json.dumps(value), headers=HEADERS)
    except Exception as e:
        print(f"Cloud DB Write Error: {e}")

# Expanded Tools Blueprint Catalog
TOOLS_LIST = [
    {"id": "adv", "name": "Advanced Lookup", "param": "num"},
    {"id": "paytm", "name": "Paytm Lookup", "param": "num"},
    {"id": "imei", "name": "IMEI Lookup", "param": "imei"},
    {"id": "calltracer", "name": "Call Tracer", "param": "num"},
    {"id": "upi", "name": "UPI Verification", "param": "upi"},
    {"id": "ifsc", "name": "IFSC Details", "param": "ifsc"},
    {"id": "number", "name": "Standard Number Lookup", "param": "num"},
    {"id": "pincode", "name": "Pincode Details", "param": "pin"},
    {"id": "ip", "name": "IP Geolocation", "param": "ip"},
    {"id": "challan", "name": "Vehicle Challan", "param": "vehicle"},
    {"id": "ff", "name": "FreeFire UID Info", "param": "uid"},
    {"id": "bgmi", "name": "BGMI UID Info", "param": "uid"},
    {"id": "snap", "name": "Snapchat Info", "param": "username"},
    {"id": "email", "name": "Email to Info", "param": "email"},
    {"id": "vehicle", "name": "Vehicle Lookup", "param": "vehicle"},
    {"id": "git", "name": "GitHub Profile Lookup", "param": "username"},
    {"id": "insta", "name": "Instagram Info", "param": "username"},
    {"id": "tg", "name": "Telegram Username to Num", "param": "info"},
    {"id": "tgidinfo", "name": "Telegram ID to Num", "param": "id"},
    {"id": "numleak", "name": "Number Leak Database", "param": "num"},
    {"id": "pk", "name": "PK Database Lookup", "param": "num"},
    {"id": "name", "name": "Identity Name Search", "param": "name"},
    {"id": "aadhar", "name": "Identity Verification System", "param": "num"},
    {"id": "numtoupi", "name": "Number to UPI Mapping", "param": "num"},
    {"id": "pan", "name": "PAN Verification Check", "param": "pan"},
    {"id": "veh2num", "name": "Vehicle to Mobile Mapping", "param": "vehicle"},
    {"id": "adharfamily", "name": "Family Struct Verification", "param": "num"},
    {"id": "bomber", "name": "Verification SMS Engine", "param": "number"},
]

class LoginRequest(BaseModel):
    username: str
    password: str

class KeyGenRequest(BaseModel):
    key_name: str
    custom_key: str
    daily_limit: int
    expiry_date: str
    allowed_tools: List[str]

# --- REVERSE PROXY GATEWAY ROUTE ---
@app.get("/gateway/{tool_id}")
async def gateway_router(tool_id: str, request: Request):
    api_keys_db = db_get("api_keys", {})
    query_params = dict(request.query_params)
    user_key = query_params.get("key")
    
    if not user_key or user_key not in api_keys_db:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    key_data = api_keys_db[user_key]
    
    if key_data["status"] == "suspended":
        raise HTTPException(status_code=403, detail="API Key is suspended")
        
    try:
        expiry = datetime.datetime.strptime(key_data["expiry"], "%Y-%m-%d").date()
        if datetime.date.today() > expiry:
            raise HTTPException(status_code=403, detail="API Key has expired")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid expiry format in cloud storage")
        
    if key_data["uses"] >= key_data["limit"]:
        raise HTTPException(status_code=429, detail="API Key request limit reached")
        
    if "all" not in key_data["tools"] and tool_id not in key_data["tools"]:
        raise HTTPException(status_code=403, detail="This key is not authorized to use this specific tool")

    tool_config = next((t for t in TOOLS_LIST if t["id"] == tool_id), None)
    search_query = query_params.get(tool_config["param"], "N/A") if tool_config else "N/A"

    # Log updating process
    search_logs = db_get("search_logs", [])
    search_logs.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key_name": key_data["name"],
        "key": user_key,
        "tool": tool_id,
        "query": search_query
    })
    db_set("search_logs", search_logs[-100:]) # keep last 100 entries
    
    key_data["uses"] += 1
    db_set("api_keys", api_keys_db)
    
    if not tool_config:
        raise HTTPException(status_code=404, detail="Tool Endpoint Not Found")
        
    forward_params = query_params.copy()
    forward_params["key"] = DEFAULT_UPSTREAM_KEY 
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_TARGET_URL}/{tool_id}", params=forward_params, timeout=12.0)
            if response.status_code == 200:
                try:
                    res_data = response.json()
                    if isinstance(res_data, dict):
                        res_data["by"] = "@vernexzzz"
                        res_data["channel"] = "https://t.me/shayan_explorer_channel"
                        if "creator" in res_data: res_data["creator"] = "@vernexzzz"
                        if "owner" in res_data: res_data["owner"] = "@vernexzzz"
                    return JSONResponse(status_code=response.status_code, content=res_data)
                except Exception:
                    pass
            return JSONResponse(status_code=response.status_code, content=response.json())
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": "Upstream server failure", "details": str(e)})

# --- ADMIN ENDPOINTS ---
@app.post("/api/admin/login")
def admin_login(data: LoginRequest):
    if data.username == ADMIN_USER and data.password == ADMIN_PASS:
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/api/admin/data")
def get_admin_data():
    return {
        "keys": list(db_get("api_keys", {}).values()),
        "logs": db_get("search_logs", []),
        "tools": TOOLS_LIST
    }

@app.post("/api/admin/keys")
def create_key(data: KeyGenRequest):
    api_keys_db = db_get("api_keys", {})
    if data.custom_key in api_keys_db:
        raise HTTPException(status_code=400, detail="Key already exists")
    
    api_keys_db[data.custom_key] = {
        "name": data.key_name,
        "key": data.custom_key,
        "limit": data.daily_limit,
        "uses": 0,
        "expiry": data.expiry_date,
        "tools": data.allowed_tools,
        "status": "active"
    }
    db_set("api_keys", api_keys_db)
    return {"status": "created"}

@app.post("/api/admin/keys/{key_id}/action")
def modify_key(key_id: str, action: dict):
    api_keys_db = db_get("api_keys", {})
    if key_id not in api_keys_db:
        raise HTTPException(status_code=404, detail="Key not found")
    
    act_type = action.get("type")
    if act_type == "delete":
        del api_keys_db[key_id]
    elif act_type == "suspend":
        api_keys_db[key_id]["status"] = "suspended"
    elif act_type == "activate":
        api_keys_db[key_id]["status"] = "active"
    elif act_type == "restart_limit":
        api_keys_db[key_id]["uses"] = 0
    elif act_type == "edit":
        api_keys_db[key_id]["limit"] = action.get("limit")
        api_keys_db[key_id]["expiry"] = action.get("expiry")
        
    db_set("api_keys", api_keys_db)
    return {"status": "updated"}

# --- USER CONTROL DASHBOARD UI ---
@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHAYAN_EXPLORER // CONTROL SUITE</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;600;800&family=Space+Grotesk:wght=400;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #040406; overflow-x: hidden; position: relative; }
            .mono { font-family: 'Space Grotesk', sans-serif; }
            #snow-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
            #loginView, #appView { position: relative; z-index: 10; }
        </style>
    </head>
    <body class="text-slate-200 min-h-screen">
        <canvas id="snow-canvas"></canvas>

        <!-- LOGIN SCREEN -->
        <div id="loginView" class="fixed inset-0 bg-[#040406]/90 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
            <div class="w-full max-w-md bg-[#0a0b12] border border-slate-900 rounded-2xl p-8 shadow-2xl">
                <div class="mb-8 text-center">
                    <span class="text-xs uppercase tracking-widest text-indigo-400 font-bold mono">Developed by @vernexzzz</span>
                    <h1 class="text-3xl font-extrabold text-white mt-1">SHAYAN_EXPLORER</h1>
                </div>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs uppercase tracking-wider text-slate-400 mb-1 font-semibold">Admin Username</label>
                        <input id="admUser" type="text" class="w-full bg-[#111222] border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-xs uppercase tracking-wider text-slate-400 mb-1 font-semibold">Passphrase</label>
                        <input id="admPass" type="password" class="w-full bg-[#111222] border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none">
                    </div>
                    <button onclick="attemptLogin()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-4 rounded-xl shadow-lg mt-2 transition-all">
                        Enter Workspace Terminal
                    </button>
                    <p id="loginErr" class="text-xs text-rose-400 mt-2 hidden text-center mono">Invalid Credentials.</p>
                </div>
            </div>
        </div>

        <!-- APP DASHBOARD -->
        <div id="appView" class="hidden min-h-screen flex flex-col">
            <header class="border-b border-slate-900 bg-[#07080f]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <div class="h-3 w-3 rounded-full bg-indigo-500 animate-pulse"></div>
                    <span class="font-bold tracking-tight text-lg text-white">SHAYAN_EXPLORER <span class="text-indigo-400 text-xs px-2 py-0.5 rounded border border-indigo-500/20 bg-indigo-500/5 ml-1">BY @VERNEXZZZ</span></span>
                </div>
                <div class="flex items-center gap-3">
                    <a href="https://t.me/shayan_explorer_channel" target="_blank" class="text-xs font-bold text-indigo-400 bg-indigo-500/5 border border-indigo-500/20 px-3 py-2 rounded-xl">📢 Official Channel Link</a>
                    <button onclick="toggleEndpoints()" class="text-xs font-semibold px-4 py-2 bg-[#111322] border border-slate-800 rounded-xl">📋 Live Proxy URIs</button>
                </div>
            </header>

            <div id="endpointsDrawer" class="hidden bg-[#0a0b12]/90 border-b border-slate-900 p-6">
                <div class="max-w-7xl mx-auto">
                    <h3 class="text-sm font-bold uppercase tracking-wider text-indigo-400 mb-3 mono">Target API Direct Routes (Click to Copy)</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3" id="rawUrlsList"></div>
                </div>
            </div>

            <main class="flex-1 p-6 max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-1 space-y-6">
                    <div class="bg-[#080911]/80 backdrop-blur-md border border-slate-900 rounded-2xl p-6">
                        <h2 class="text-lg font-bold text-white mb-4">🔑 Generate Dynamic Token</h2>
                        <div class="space-y-4">
                            <div>
                                <label class="block text-xs uppercase text-slate-400 mb-1">User Label</label>
                                <input id="keyName" type="text" placeholder="Client Name" class="w-full bg-[#121324] border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-xs uppercase text-slate-400 mb-1">Custom Passkey Core</label>
                                <input id="keyString" type="text" placeholder="shayan-key-xxxx" class="w-full bg-[#121324] border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none">
                            </div>
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-xs uppercase text-slate-400 mb-1">Limit Request</label>
                                    <input id="keyLimit" type="number" value="500" class="w-full bg-[#121324] border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white">
                                </div>
                                <div>
                                    <label class="block text-xs uppercase text-slate-400 mb-1">Expiration</label>
                                    <input id="keyExpiry" type="date" class="w-full bg-[#121324] border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white">
                                </div>
                            </div>
                            <div>
                                <label class="block text-xs uppercase text-slate-400 mb-2">Scope Mapping</label>
                                <div class="flex gap-2 mb-3">
                                    <button id="toolScopeAll" onclick="setScopeMode('all')" class="flex-1 py-1.5 rounded-lg text-xs font-bold border border-indigo-500 bg-indigo-500/10 text-indigo-400">All Modules</button>
                                    <button id="toolScopeSpec" onclick="setScopeMode('spec')" class="flex-1 py-1.5 rounded-lg text-xs font-bold border border-slate-800 bg-[#121324] text-slate-400">Custom Isolate</button>
                                </div>
                                <div id="specificToolsGrid" class="hidden grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 bg-[#0a0b12] rounded-xl border border-slate-900"></div>
                            </div>
                            <button onclick="generateKey()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-4 rounded-xl text-sm transition-all shadow-lg">Provision Key Ruleset</button>
                        </div>
                    </div>
                </div>

                <div class="lg:col-span-2 space-y-6">
                    <div class="bg-[#080911]/80 backdrop-blur-md border border-slate-900 rounded-2xl p-6">
                        <h2 class="text-lg font-bold text-white mb-4">Live Cryptographic Allocation Mapping</h2>
                        <div class="space-y-3 max-h-[380px] overflow-y-auto pr-1" id="keysContainer"></div>
                    </div>
                    <div class="bg-[#080911]/80 backdrop-blur-md border border-slate-900 rounded-2xl p-6">
                        <h2 class="text-lg font-bold text-white mb-4">📡 Live Activity Lookup Telemetry</h2>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead>
                                    <tr class="border-b border-slate-900 text-slate-400 font-mono">
                                        <th class="py-2">Timestamp</th>
                                        <th class="py-2">Key Owner</th>
                                        <th class="py-2">Trigger Link</th>
                                        <th class="py-2">Logged Query</th>
                                    </tr>
                                </thead>
                                <tbody id="logsTableBody" class="divide-y divide-slate-900 text-slate-300 mono"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </div>

        <script>
            let currentScopeMode = 'all';
            let globalToolsList = [];
            document.getElementById('keyExpiry').value = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0];

            // --- LAG-FREE SNOW ENGINE ---
            const canvas = document.getElementById('snow-canvas');
            const ctx = canvas.getContext('2d');
            let flakes = [];
            function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();

            function initSnow() {
                flakes = [];
                const maxFlakes = window.innerWidth < 768 ? 30 : 80;
                for (let i = 0; i < maxFlakes; i++) {
                    flakes.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2 + 1, speed: Math.random() * 0.8 + 0.4 });
                }
            }
            function drawSnow() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = 'rgba(230, 242, 255, 0.4)';
                ctx.beginPath();
                for (let i = 0; i < flakes.length; i++) {
                    const f = flakes[i];
                    ctx.moveTo(f.x, f.y);
                    ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2, true);
                }
                ctx.fill();
                for (let i = 0; i < flakes.length; i++) {
                    flakes[i].y += flakes[i].speed;
                    flakes[i].x += Math.sin(flakes[i].y / 25) * 0.3;
                    if (flakes[i].y > canvas.height) { flakes[i].y = -10; flakes[i].x = Math.random() * canvas.width; }
                }
                requestAnimationFrame(drawSnow);
            }
            initSnow(); drawSnow();

            // --- SUITE LOGIC ---
            async function attemptLogin() {
                const username = document.getElementById('admUser').value;
                const password = document.getElementById('admPass').value;
                const res = await fetch('/api/admin/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ username, password }) });
                if (res.ok) {
                    document.getElementById('loginView').classList.add('hidden');
                    document.getElementById('appView').classList.remove('hidden');
                    refreshTelemetry(); setInterval(refreshTelemetry, 3000); 
                } else { document.getElementById('loginErr').classList.remove('hidden'); }
            }

            function setScopeMode(mode) {
                currentScopeMode = mode;
                document.getElementById('specificToolsGrid').classList.toggle('hidden', mode === 'all');
                document.getElementById('toolScopeAll').className = mode === 'all' ? "flex-1 py-1.5 rounded-lg text-xs font-bold border border-indigo-500 bg-indigo-500/10 text-indigo-400" : "flex-1 py-1.5 rounded-lg text-xs font-bold border border-slate-800 bg-[#121324] text-slate-400";
                document.getElementById('toolScopeSpec').className = mode === 'spec' ? "flex-1 py-1.5 rounded-lg text-xs font-bold border border-indigo-500 bg-indigo-500/10 text-indigo-400" : "flex-1 py-1.5 rounded-lg text-xs font-bold border border-slate-800 bg-[#121324] text-slate-400";
            }
            function toggleEndpoints() { document.getElementById('endpointsDrawer').classList.toggle('hidden'); }
            function copyToClipboard(text) { navigator.clipboard.writeText(text); alert("Route Path Blueprint Copied."); }

            async function refreshTelemetry() {
                const res = await fetch('/api/admin/data');
                const data = await res.json();
                
                const grid = document.getElementById('specificToolsGrid');
                if(!grid.children.length) {
                    grid.innerHTML = data.tools.map(t => `<label class="flex items-center gap-2 p-1.5 rounded bg-[#070810] text-[11px] text-slate-300 cursor-pointer border border-slate-900"><input type="checkbox" value="${t.id}" class="accent-indigo-500"><span class="truncate">${t.name}</span></label>`).join('');
                }

                document.getElementById('rawUrlsList').innerHTML = data.tools.map(t => `
                    <div onclick="copyToClipboard('${window.location.origin}/gateway/${t.id}?key=YOUR_KEY&${t.param}=')" class="p-2.5 bg-[#07080f] border border-slate-800 rounded-xl cursor-pointer text-xs font-mono truncate transition-all hover:border-indigo-500/50">
                        <span class="text-indigo-400 font-bold">[${t.id.toUpperCase()}]</span><br>${window.location.origin}/gateway/${t.id}
                    </div>
                `).join('');

                document.getElementById('keysContainer').innerHTML = data.keys.length === 0 ? `<p class="text-xs text-slate-500 py-4 text-center mono">No active token signatures found.</p>` : data.keys.map(k => `
                    <div class="p-4 bg-[#0a0b14] border border-slate-900 rounded-xl space-y-3">
                        <div class="flex justify-between items-start">
                            <div>
                                <h4 class="font-bold text-sm text-white">${k.name}</h4>
                                <p class="text-xs font-mono text-indigo-300 bg-[#111222] px-2 py-0.5 rounded border border-slate-800 inline-block mt-1 select-all">${k.key}</p>
                            </div>
                            <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${k.status==='active'?'text-emerald-400 border-emerald-500/20 bg-emerald-500/5':'text-rose-400 border-rose-500/20 bg-rose-500/5'}">${k.status}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2 text-[11px] text-slate-400 mono">
                            <div>Hits: <span class="text-white font-bold">${k.uses}/${k.limit}</span></div>
                            <div>Exp: <span class="text-white font-bold">${k.expiry}</span></div>
                            <span class="truncate">Scope: ${k.tools.join(', ')}</span>
                        </div>
                        <div class="flex gap-1.5 pt-1 border-t border-slate-900/40 text-[10px]">
                            <button onclick="keyAction('${k.key}', 'restart_limit')" class="bg-slate-900 border border-slate-800 text-slate-300 px-2 py-1 rounded">Reset</button>
                            <button onclick="keyAction('${k.key}', '${k.status==='active'?'suspend':'activate'}')" class="bg-indigo-500/10 text-indigo-400 px-2 py-1 rounded">${k.status==='active'?'Suspend':'Activate'}</button>
                            <button onclick="keyAction('${k.key}', 'delete')" class="bg-rose-500/10 text-rose-400 px-2 py-1 rounded ml-auto">Delete</button>
                        </div>
                    </div>
                `).join('');

                document.getElementById('logsTableBody').innerHTML = data.logs.length === 0 ? `<tr><td colspan="4" class="py-4 text-center text-slate-600">Awaiting stream telemetry requests...</td></tr>` : data.logs.reverse().map(l => `
                    <tr><td class="py-2 text-slate-500">${l.timestamp}</td><td class="py-2 text-slate-300 font-semibold">${l.key_name}</td><td class="py-2 text-indigo-400 font-bold">[${l.tool.toUpperCase()}]</td><td class="py-2 text-slate-400">${l.query}</td></tr>
                `).join('');
            }

            async function generateKey() {
                const key_name = document.getElementById('keyName').value;
                const custom_key = document.getElementById('keyString').value;
                const daily_limit = parseInt(document.getElementById('keyLimit').value);
                const expiry_date = document.getElementById('keyExpiry').value;
                if(!key_name || !custom_key) return alert("Fill fields.");

                let allowed_tools = ['all'];
                if(currentScopeMode === 'spec') {
                    allowed_tools = Array.from(document.querySelectorAll('#specificToolsGrid input:checked')).map(el => el.value);
                    if(allowed_tools.length === 0) return alert("Select tools.");
                }

                const res = await fetch('/api/admin/keys', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ key_name, custom_key, daily_limit, expiry_date, allowed_tools }) });
                if(res.ok) { document.getElementById('keyName').value = ''; document.getElementById('keyString').value = ''; refreshTelemetry(); }
                else { alert("Key collision error."); }
            }

            async function keyAction(keyId, actionType) {
                await fetch(`/api/admin/keys/${keyId}/action`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ type: actionType }) });
                refreshTelemetry();
            }
        </script>
    </body>
    </html>
    """
