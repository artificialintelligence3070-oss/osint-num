import os
import httpx
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ---- CONFIGURATION ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"
DEVELOPER_NAME = "SHAYAN_EXPLORER"

# ---- SERVERLESS SAFE DATABASE SETUP ----
# Vercel only allows write operations inside the /tmp directory
DATABASE_URL = "sqlite:////tmp/gateway.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"
    key = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    limit = Column(Integer, default=100)
    used = Column(Integer, default=0)
    allowed_tools = Column(Text, default="all")
    is_active = Column(Boolean, default=True)

class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key_used = Column(String, index=True)
    endpoint = Column(String)
    query_params = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Ensure tables are built smoothly inside /tmp
Base.metadata.create_all(bind=engine)

# ---- APP SETUP ----
app = FastAPI(title=f"API Gateway by {DEVELOPER_NAME}")
security = HTTPBasic()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- API PROXY SYSTEM ----
@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request, key: str, db: Session = Depends(get_db)):
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if not db_key or not db_key.is_active:
        raise HTTPException(status_code=403, detail="Invalid or inactive API Key.")
    
    if datetime.utcnow() > db_key.expires_at:
        raise HTTPException(status_code=403, detail="API Key has expired.")
    
    if db_key.used >= db_key.limit:
        raise HTTPException(status_code=429, detail="API Key request limit reached.")
    
    if db_key.allowed_tools != "all":
        allowed_list = [t.strip() for t in db_key.allowed_tools.split(",")]
        if endpoint not in allowed_list:
            raise HTTPException(status_code=403, detail=f"No access to tool: {endpoint}")

    params = dict(request.query_params)
    params.pop("key", None) 
    
    # Log the transaction
    log_entry = RequestLog(key_used=key, endpoint=endpoint, query_params=str(params))
    db.add(log_entry)
    
    db_key.used += 1
    db.commit()

    params["key"] = MASTER_API_KEY
    upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(upstream_url, params=params, timeout=15.0)
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": "Core API connection error", "details": str(e)}, status_code=502)

# ---- MANAGEMENT HUB DASHBOARD ----
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    keys = db.query(APIKey).all()
    logs = db.query(RequestLog).order_by(RequestLog.timestamp.desc()).limit(30).all()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Hub | {DEVELOPER_NAME}</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #0b0f19; color: #e2e8f0; font-family: monospace; }}
            .glass {{ background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.08); }}
            .neon {{ text-shadow: 0 0 8px #3b82f6; }}
        </style>
    </head>
    <body class="p-6">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
                <div>
                    <h1 class="text-2xl font-bold text-blue-500 neon">NEXUS ARCHITECTURE GATEWAY</h1>
                    <p class="text-xs text-gray-500 mt-1">DEVELOPER: {DEVELOPER_NAME}</p>
                </div>
                <span class="bg-green-900 text-green-300 px-3 py-1 rounded-full text-xs">LIVE</span>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Create Key Form -->
                <div class="glass p-5 rounded-xl">
                    <h2 class="text-lg font-bold mb-4 text-blue-400">Generate Client Key</h2>
                    <form action="/admin/create-key" method="post" class="space-y-3 text-sm">
                        <div>
                            <label class="block text-xs text-gray-400 mb-1">User / Client Name</label>
                            <input type="text" name="name" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-400 mb-1">Custom Key String</label>
                            <input type="text" name="key" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-400 mb-1">Total Max Limit (Requests)</label>
                            <input type="number" name="limit" value="1000" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-400 mb-1">Expiration Date & Time</label>
                            <input type="datetime-local" name="expires_at" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-400 mb-1">Allowed Scopes / Tools (or 'all')</label>
                            <input type="text" name="allowed_tools" value="all" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded transition">PROVISION MODULE</button>
                    </form>
                </div>

                <!-- Database Entries -->
                <div class="lg:col-span-2 glass p-5 rounded-xl overflow-x-auto">
                    <h2 class="text-lg font-bold mb-4 text-blue-400">Active Allocations</h2>
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="border-b border-gray-800 text-gray-400">
                                <th class="pb-2">Name</th>
                                <th class="pb-2">Token Key</th>
                                <th class="pb-2">Usage</th>
                                <th class="pb-2">Expires At</th>
                                <th class="pb-2">Scope</th>
                                <th class="pb-2">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800">
    """
    for k in keys:
        html_content += f"""
                            <tr>
                                <td class="py-2 text-white font-bold">{k.name}</td>
                                <td class="py-2 text-yellow-400">{k.key}</td>
                                <td class="py-2">{k.used} / {k.limit}</td>
                                <td class="py-2 text-gray-400">{k.expires_at}</td>
                                <td class="py-2 text-blue-400">{k.allowed_tools}</td>
                                <td class="py-2"><a href="/admin/delete-key?key={k.key}" class="text-red-500 hover:underline">Revoke</a></td>
                            </tr>
        """
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Logs Tracker -->
            <div class="mt-6 glass p-5 rounded-xl">
                <h2 class="text-lg font-bold mb-4 text-blue-400">System Logs Registry</h2>
                <div class="overflow-x-auto max-h-60 text-xs">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="border-b border-gray-800 text-gray-400">
                                <th class="pb-2">Timestamp</th>
                                <th class="pb-2">Key Identifier</th>
                                <th class="pb-2">Endpoint</th>
                                <th class="pb-2">Captured Arguments</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800">
    """
    for log in logs:
        html_content += f"""
                            <tr>
                                <td class="py-2 text-gray-500">{log.timestamp}</td>
                                <td class="py-2 text-yellow-600">{log.key_used}</td>
                                <td class="py-2 text-green-400">/api/{log.endpoint}</td>
                                <td class="py-2 text-gray-300 font-mono bg-gray-900 bg-opacity-30 px-1 rounded">{log.query_params}</td>
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
    return HTMLResponse(content=html_content)

@app.post("/admin/create-key")
async def create_key(
    name: str = Form(...), key: str = Form(...), limit: int = Form(...),
    expires_at: str = Form(...), allowed_tools: str = Form(...), db: Session = Depends(get_db)
):
    new_key = APIKey(
        key=key, name=name, limit=limit,
        expires_at=datetime.fromisoformat(expires_at),
        allowed_tools=allowed_tools, is_active=True
    )
    db.merge(new_key)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin/delete-key")
async def delete_key(key: str, db: Session = Depends(get_db)):
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if db_key:
        db.delete(db_key)
        db.commit()
    return RedirectResponse(url="/", status_code=303)
