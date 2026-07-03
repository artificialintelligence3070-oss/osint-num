import os
import time
import httpx
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ---- CONFIGURATION ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"
DEVELOPER_NAME = "SHAYAN_EXPLORER"

# ---- DATABASE SETUP ----
DATABASE_URL = "sqlite:///./gateway.db"
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
    allowed_tools = Column(Text, default="all") # Comma-separated list or "all"
    is_active = Column(Boolean, default=True)

class RequestLog(Base):
    __tablename__ = "request_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key_used = Column(String, index=True)
    endpoint = Column(String)
    query_params = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

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

# ---- ADMINISTRATIVE AUTHENTICATION ----
def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin Credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ---- CORE PROXY GATEWAY LOGIC ----
@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request, key: str, db: Session = Depends(get_db)):
    # 1. Validate Custom API Key
    db_key = db.query(APIKey).filter(APIKey.key == key).first()
    if not db_key or not db_key.is_active:
        raise HTTPException(status_code=403, detail="Invalid or inactive API Key.")
    
    # 2. Check Expiration Date
    if datetime.utcnow() > db_key.expires_at:
        raise HTTPException(status_code=403, detail="API Key has expired.")
    
    # 3. Check Usage Limits
    if db_key.used >= db_key.limit:
        raise HTTPException(status_code=429, detail="API Key request limit reached.")
    
    # 4. Check Specific Tool Restrictions
    if db_key.allowed_tools != "all":
        allowed_list = [t.strip() for t in db_key.allowed_tools.split(",")]
        if endpoint not in allowed_list:
            raise HTTPException(status_code=403, detail=f"Your key does not have access to the '{endpoint}' tool.")

    # Extract dynamic parameters passing through
    params = dict(request.query_params)
    params.pop("key", None) # Remove client custom key
    
    # 5. Log the Query Payload
    log_entry = RequestLog(
        key_used=key,
        endpoint=endpoint,
        query_params=str(params)
    )
    db.add(log_entry)
    
    # Increment counter
    db_key.used += 1
    db.commit()

    # Append Upstream Master Key Auth
    params["key"] = MASTER_API_KEY

    # 6. Forward Request to Upstream Core Server
    upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(upstream_url, params=params, timeout=15.0)
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": "Upstream communication error", "details": str(e)}, status_code=502)

# ---- MANAGEMENT DASHBOARD INTERFACE ----
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    # Basic Auth enforced using headers manually for simple template routing
    auth = request.headers.get("Authorization")
    if not auth:
        return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    keys = db.query(APIKey).all()
    logs = db.query(RequestLog).order_by(RequestLog.timestamp.desc()).limit(50).all()
    
    # Cyberpunk / Tech Professional 3D-styled theme
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Hub | {DEVELOPER_NAME}</title>
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #0b0f19; color: #e2e8f0; font-family: 'Courier New', Courier, monospace; }}
            .glass {{ background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 20px 50px rgba(0,0,0,0.3); }}
            .neon-text {{ text-shadow: 0 0 10px #3b82f6, 0 0 20px #3b82f6; }}
            .neon-border:focus {{ border-color: #3b82f6; box-shadow: 0 0 10px #3b82f6; }}
        </style>
    </head>
    <body class="p-6">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center mb-10 border-b border-gray-800 pb-4">
                <div>
                    <h1 class="text-3xl font-bold text-blue-500 neon-text">NEXUS CONTROL SYSTEM</h1>
                    <p class="text-xs text-gray-400 mt-1">SYSTEM ARCHITECT: {DEVELOPER_NAME}</p>
                </div>
                <div class="text-right">
                    <span class="bg-green-900 text-green-300 px-3 py-1 rounded-full text-xs font-mono tracking-wider">GATEWAY ONLINE</span>
                </div>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Key Generation Provisioning Form -->
                <div class="glass p-6 rounded-xl h-fit">
                    <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-800 pb-2">Generate License Key</h2>
                    <form action="/admin/create-key" method="post" class="space-y-4">
                        <div>
                            <label class="block text-xs uppercase text-gray-400 mb-1">Client Identification Name</label>
                            <input type="text" name="name" required class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none neon-border">
                        </div>
                        <div>
                            <label class="block text-xs uppercase text-gray-400 mb-1">Custom Key Value String</label>
                            <input type="text" name="key" placeholder="e.g., VIP-SHAYAN-XYZ" required class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none neon-border">
                        </div>
                        <div>
                            <label class="block text-xs uppercase text-gray-400 mb-1">Total Request Quota Limit</label>
                            <input type="number" name="limit" value="1000" required class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none neon-border">
                        </div>
                        <div>
                            <label class="block text-xs uppercase text-gray-400 mb-1">Expiration ISO Date-Time</label>
                            <input type="datetime-local" name="expires_at" required class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none neon-border">
                        </div>
                        <div>
                            <label class="block text-xs uppercase text-gray-400 mb-1">Allowed System Endpoints (Tools)</label>
                            <input type="text" name="allowed_tools" value="all" placeholder="e.g., number,paytm,upi or all" required class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none neon-border">
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded text-sm tracking-wide transition duration-200">PROVISION KEY</button>
                    </form>
                </div>

                <!-- Live Master Inventory Keys Status -->
                <div class="lg:col-span-2 glass p-6 rounded-xl overflow-x-auto">
                    <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-800 pb-2">Active Database Registries</h2>
                    <table class="w-full text-left text-xs font-mono">
                        <thead>
                            <tr class="border-b border-gray-800 text-gray-400 uppercase">
                                <th class="pb-2">Client Name</th>
                                <th class="pb-2">Key String</th>
                                <th class="pb-2">Quota Usage</th>
                                <th class="pb-2">Expiration Window</th>
                                <th class="pb-2">Scope</th>
                                <th class="pb-2">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800">
    """
    
    for k in keys:
        html_content += f"""
                            <tr>
                                <td class="py-3 text-white font-bold">{k.name}</td>
                                <td class="py-3 text-yellow-400">{k.key}</td>
                                <td class="py-3">{k.used} / {k.limit}</td>
                                <td class="py-3 text-gray-400">{k.expires_at}</td>
                                <td class="py-3 text-blue-400">{k.allowed_tools}</td>
                                <td class="py-3">
                                    <a href="/admin/delete-key?key={k.key}" class="text-red-500 hover:underline">Revoke</a>
                                </td>
                            </tr>
        """
        
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Operational Inspection Query Logs Tracking -->
            <div class="mt-8 glass p-6 rounded-xl">
                <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-800 pb-2">Central Security Access Registry Logs (Real-time Analytics)</h2>
                <div class="overflow-x-auto max-h-96">
                    <table class="w-full text-left text-xs font-mono">
                        <thead>
                            <tr class="border-b border-gray-800 text-gray-400">
                                <th class="pb-2">TIMESTAMP (UTC)</th>
                                <th class="pb-2">TOKEN REF</th>
                                <th class="pb-2">RESOURCE ENDPOINT</th>
                                <th class="pb-2">CAPTURE RECORDED QUERY DATA</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800 text-gray-300">
    """
    
    for log in logs:
        html_content += f"""
                            <tr>
                                <td class="py-2 text-gray-500">{log.timestamp}</td>
                                <td class="py-2 text-yellow-600">{log.key_used}</td>
                                <td class="py-2 text-green-400">/api/{log.endpoint}</td>
                                <td class="py-2 text-blue-300 font-sans bg-gray-900 bg-opacity-40 p-1 rounded font-mono">{log.query_params}</td>
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

# ---- ACTIONS ----
@app.post("/admin/create-key")
async def create_key(
    name: str = Form(...),
    key: str = Form(...),
    limit: int = Form(...),
    expires_at: str = Form(...),
    allowed_tools: str = Form(...),
    db: Session = Depends(get_db)
):
    expiry_dt = datetime.fromisoformat(expires_at)
    new_key = APIKey(
        key=key,
        name=name,
        limit=limit,
        expires_at=expiry_dt,
        allowed_tools=allowed_tools,
        is_active=True
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
