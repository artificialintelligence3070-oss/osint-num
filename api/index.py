import os
import httpx
import json
import urllib.parse
from datetime import datetime

# ---- CORE GATEWAY CONFIGURATIONS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "SHAYAN_EXPLORER"

# ---- IN-MEMORY FALLBACK REGISTRY ----
MOCK_KEYS = {
    "VIP-SHAYAN": {
        "name": "Beta Tester",
        "limit": 5000,
        "used": 0,
        "expires_at": "2027-12-31 23:59:59",
        "allowed_tools": "all"
    }
}
MOCK_LOGS = []

# ---- UTILITY PARSERS ----
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

# ---- CORE ASGI APPLICATION INTERFACE ----
async def app(scope, receive, send):
    global MOCK_LOGS, MOCK_KEYS
    
    if scope['type'] != 'http':
        return

    path = scope['path']
    query_string = scope.get('query_string', b'').decode('utf-8')
    params = parse_query_string(query_string)

    # ====================================================
    # 1. CORE API ROUTER (Handles incoming /api/{endpoint})
    # ====================================================
    if path.startswith("/api/"):
        endpoint = path.replace("/api/", "", 1)
        client_key = params.get("key")

        if not client_key or client_key not in MOCK_KEYS:
            await send_json(send, {"error": "Invalid token configuration identifier."}, 403)
            return

        key_data = MOCK_KEYS[client_key]
        
        # Check Expiration Frame
        if datetime.utcnow() > datetime.strptime(key_data["expires_at"], "%Y-%m-%d %H:%M:%S"):
            await send_json(send, {"error": "Your allocated license access window has expired."}, 403)
            return

        # Check Usage Limitations
        if key_data["used"] >= key_data["limit"]:
            await send_json(send, {"error": "API daily/total query limitations exhausted."}, 429)
            return

        # Check Specific Tool Access Scope
        if key_data["allowed_tools"] != "all":
            allowed_list = [t.strip() for t in key_data["allowed_tools"].split(",")]
            if endpoint not in allowed_list:
                await send_json(send, {"error": f"Access denied to target sub-module: {endpoint}"}, 403)
                return

        # Clean query parameters for upstream delivery
        cleaned_params = {k: v for k, v in params.items() if k != "key"}
        
        # Log Transaction
        MOCK_LOGS.insert(0, {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "key": client_key,
            "endpoint": endpoint,
            "params": str(cleaned_params)
        })
        key_data["used"] += 1

        # Request Forwarding Engine
        cleaned_params["key"] = MASTER_API_KEY
        upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(upstream_url, params=cleaned_params, timeout=12.0)
                await send_json(send, response.json(), response.status_code)
                return
            except Exception as e:
                await send_json(send, {"error": "Core proxy connection timed out", "details": str(e)}, 502)
                return

    # ====================================================
    # 2. MANAGEMENT INTERFACE FORM POST OPERATIONS
    # ====================================================
    elif path == "/admin/create-key" and scope['method'] == 'POST':
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)
        
        try:
            form_data = parse_query_string(body.decode('utf-8'))
            k_name = urllib.parse.unquote(form_data.get("name", "Unknown")).replace("+", " ")
            k_val = urllib.parse.unquote(form_data.get("key", ""))
            k_limit = int(form_data.get("limit", 1000))
            k_expiry = urllib.parse.unquote(form_data.get("expires_at", "")).replace("T", " ")
            if len(k_expiry) == 16:  # Appends seconds precision if missing from HTML element
                k_expiry += ":00"
            k_tools = urllib.parse.unquote(form_data.get("allowed_tools", "all")).replace("+", " ")

            if k_val:
                MOCK_KEYS[k_val] = {
                    "name": k_name,
                    "limit": k_limit,
                    "used": 0,
                    "expires_at": k_expiry,
                    "allowed_tools": k_tools
                }
        except Exception:
            pass
        
        await send_redirect(send, "/")
        return

    # ====================================================
    # 3. ADMINISTRATIVE REVOCATION OPERATIONS
    # ====================================================
    elif path == "/admin/delete-key":
        target_key = params.get("key")
        if target_key in MOCK_KEYS:
            del MOCK_KEYS[target_key]
        await send_redirect(send, "/")
        return

    # ====================================================
    # 4. CENTRAL MANAGEMENT CONTROL MATRIX HUB UI (/)
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
                body {{ background-color: #060913; color: #cbd5e1; font-family: monospace; }}
                .panel {{ background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(59, 130, 246, 0.2); box-shadow: 0 0 15px rgba(0,0,0,0.6); }}
                .neon-txt {{ text-shadow: 0 0 10px #2563eb; }}
            </style>
        </head>
        <body class="p-6">
            <div class="max-w-7xl mx-auto">
                <header class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
                    <div>
                        <h1 class="text-2xl font-bold text-blue-500 neon-txt">NEXUS ZERO-DEPENDENCY APPARATUS</h1>
                        <p class="text-xs text-gray-500 mt-1">CORE ARCHITECT: {DEVELOPER_NAME}</p>
                    </div>
                    <span class="text-xs bg-green-900 text-green-300 px-3 py-1 rounded-full font-bold">100% OPERATIONAL</span>
                </header>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Key Provisioning Panel -->
                    <div class="panel p-5 rounded-xl">
                        <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Provision Access Token</h2>
                        <form action="/admin/create-key" method="post" class="space-y-4 text-xs">
                            <div>
                                <label class="block text-gray-400 mb-1">CLIENT NAME</label>
                                <input type="text" name="name" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1">CUSTOM API KEY</label>
                                <input type="text" name="key" placeholder="VIP-KEY-XYZ" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1">MAX QUERY LIMIT</label>
                                <input type="number" name="limit" value="1000" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1">EXPIRATION WINDOW</label>
                                <input type="datetime-local" name="expires_at" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                            </div>
                            <div>
                                <label class="block text-gray-400 mb-1">ALLOWED ENPOINTS SCOPE (or 'all')</label>
                                <input type="text" name="allowed_tools" value="all" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                            </div>
                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded tracking-widest uppercase transition">Inject Record</button>
                        </form>
                    </div>

                    <!-- Token Allocation Matrix -->
                    <div class="lg:col-span-2 panel p-5 rounded-xl overflow-x-auto">
                        <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Active Token Allocations</h2>
                        <table class="w-full text-left text-xs">
                            <thead>
                                <tr class="border-b border-gray-800 text-gray-400 font-mono">
                                    <th class="pb-2">CLIENT</th>
                                    <th class="pb-2">TOKEN KEY</th>
                                    <th class="pb-2">USAGE STATUS</th>
                                    <th class="pb-2">EXPIRATION TIMESTAMP</th>
                                    <th class="pb-2">SCOPE</th>
                                    <th class="pb-2">ACTION</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-800">
        """
        for k_str, k_info in MOCK_KEYS.items():
            html_content += f"""
                                <tr>
                                    <td class="py-2.5 text-white font-bold">{k_info['name']}</td>
                                    <td class="py-2.5 text-yellow-500 font-mono">{k_str}</td>
                                    <td class="py-2.5 font-mono">{k_info['used']} / {k_info['limit']}</td>
                                    <td class="py-2.5 text-gray-400">{k_info['expires_at']}</td>
                                    <td class="py-2.5 text-blue-400">{k_info['allowed_tools']}</td>
                                    <td class="py-2.5"><a href="/admin/delete-key?key={k_str}" class="text-red-500 hover:underline">Revoke</a></td>
                                </tr>
            """
        html_content += """
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Traffic Feed Monitor -->
                <div class="mt-6 panel p-5 rounded-xl">
                    <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Live Traffic Query Inspection Feed</h2>
                    <div class="overflow-x-auto max-h-60 text-xs font-mono">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="border-b border-gray-800 text-gray-400">
                                    <th class="pb-2">TIMESTAMP</th>
                                    <th class="pb-2">TOKEN REF</th>
                                    <th class="pb-2">ENDPOINT RESOURCE</th>
                                    <th class="pb-2">LOOKUP REQUEST METADATA RECORDS</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-800">
        """
        for log in MOCK_LOGS[:20]:
            html_content += f"""
                                <tr>
                                    <td class="py-2 text-gray-500">{log['timestamp']}</td>
                                    <td class="py-2 text-yellow-600 font-bold">{log['key']}</td>
                                    <td class="py-2 text-green-400">/api/{log['endpoint']}</td>
                                    <td class="py-2 text-gray-300 font-sans bg-gray-900 bg-opacity-60 px-2 py-0.5 rounded border border-gray-800">{log['params']}</td>
                                </tr>
            """
        html_content += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        await send_html(send, html_content)
        return

    # ====================================================
    # 5. CATCH-ALL ROUTE (Handles system matching fallbacks)
    # ====================================================
    else:
        await send_json(send, {"detail": f"Path '{path}' not found on Nexus Gateway Server."}, 404)

# ---- ASGI HIGH-SPEED LOWER STREAM DRIVERS ----
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
