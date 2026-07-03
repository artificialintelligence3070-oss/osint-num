import os
import httpx
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ---- INITIALIZATION CONFIGS ----
MASTER_API_KEY = "vx-osint"
TARGET_BASE_URL = "https://ft-osint-api.duckdns.org/api"
DEVELOPER_NAME = "SHAYAN_EXPLORER"

# ---- SECURE SERVERLESS ENGINE SETUP ----
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # 1. Standardize legacy postgres:// strings for SQLAlchemy 2.x compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # 2. Append required SSL query arguments cleanly if missing
    if "sslmode" not in DATABASE_URL and "localhost" not in DATABASE_URL:
        DATABASE_URL += "&sslmode=require" if "?" in DATABASE_URL else "?sslmode=require"
else:
    # Fallback to local serverless isolated instance if Env variables aren't propagated yet
    DATABASE_URL = "sqlite:////tmp/fallback.db"

# Create database connection pooling
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 10})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---- SYSTEM DATABASES ----
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

# Fail-safe schema injection initialization
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

app = FastAPI(title="Nexus Gateway")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- SECURITY API PROXY ROUTE ----
@app.get("/api/{endpoint}")
async def proxy_gateway(endpoint: str, request: Request, key: str, db: Session = Depends(get_db)):
    try:
        db_key = db.query(APIKey).filter(APIKey.key == key).first()
    except Exception as db_err:
        raise HTTPException(status_code=500, detail=f"Database connectivity failure: {str(db_err)}")

    if not db_key or not db_key.is_active:
        raise HTTPException(status_code=403, detail="Invalid token configuration identifier.")
    
    if datetime.utcnow() > db_key.expires_at:
        raise HTTPException(status_code=403, detail="Your allocated license access window has expired.")
    
    if db_key.used >= db_key.limit:
        raise HTTPException(status_code=429, detail="API daily/total query limitations exhausted.")
    
    if db_key.allowed_tools != "all":
        allowed_list = [t.strip() for t in db_key.allowed_tools.split(",")]
        if endpoint not in allowed_list:
            raise HTTPException(status_code=403, detail=f"Access denied to target sub-module: {endpoint}")

    params = dict(request.query_params)
    params.pop("key", None)
    
    # Store request logs inside the cloud DB
    try:
        log_entry = RequestLog(key_used=key, endpoint=endpoint, query_params=str(params))
        db.add(log_entry)
        db_key.used += 1
        db.commit()
    except Exception:
        db.rollback()

    params["key"] = MASTER_API_KEY
    upstream_url = f"{TARGET_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(upstream_url, params=params, timeout=12.0)
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": "Upstream connection timed out", "details": str(e)}, status_code=502)

# ---- ADMINISTRATIVE MANAGEMENT CONSOLE ----
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(db: Session = Depends(get_db)):
    try:
        keys = db.query(APIKey).all()
        logs = db.query(RequestLog).order_by(RequestLog.id.desc()).limit(20).all()
    except Exception as db_err:
        return HTMLResponse(content=f"<h3>Database Connection Error: {str(db_err)}</h3><p>Verify your Vercel DATABASE_URL environment variable.</p>", status_code=500)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Hub | {DEVELOPER_NAME}</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #060913; color: #cbd5e1; font-family: monospace; }}
            .panel {{ background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(59, 130, 246, 0.2); }}
            .neon-txt {{ text-shadow: 0 0 10px #2563eb; }}
        </style>
    </head>
    <body class="p-6">
        <div class="max-w-7xl mx-auto">
            <header class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
                <div>
                    <h1 class="text-2xl font-bold text-blue-500 neon-txt">NEXUS CENTRAL CONTROL PANEL</h1>
                    <p class="text-xs text-gray-500 mt-1">SYSTEM ARCHITECT: {DEVELOPER_NAME}</p>
                </div>
                <span class="text-xs bg-blue-900 text-blue-300 px-3 py-1 rounded-full font-bold">SYSTEM ACTIVE</span>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Add User Key Form -->
                <div class="panel p-5 rounded-xl">
                    <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Provision Access Token</h2>
                    <form action="/admin/create-key" method="post" class="space-y-4 desert-form text-xs">
                        <div>
                            <label class="block text-gray-400 mb-1">CLIENT ASSIGNED NAME</label>
                            <input type="text" name="name" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-gray-400 mb-1">CUSTOM API LICENSE KEY</label>
                            <input type="text" name="key" placeholder="VIP-KEY-XYZ" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-gray-400 mb-1">MAX QUOTA REQUEST LIMIT</label>
                            <input type="number" name="limit" value="1000" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-gray-400 mb-1">EXPIRATION WINDOW DATE</label>
                            <input type="datetime-local" name="expires_at" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-gray-400 mb-1">ALLOWED ENPOINTS SCOPE (or 'all')</label>
                            <input type="text" name="allowed_tools" value="all" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:outline-none">
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded tracking-widest uppercase transition">Commit Records</button>
                    </form>
                </div>

                <!-- Database Registry Matrix Table -->
                <div class="lg:col-span-2 panel p-5 rounded-xl overflow-x-auto">
                    <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Token Allocation Matrix</h2>
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="border-b border-gray-800 text-gray-400 font-mono">
                                <th class="pb-2">CLIENT</th>
                                <th class="pb-2">TOKEN KEY</th>
                                <th class="pb-2">USAGE STATUS</th>
                                <th class="pb-2">EXPIRATION TIMINGS</th>
                                <th class="pb-2">SCOPE</th>
                                <th class="pb-2">ACTION</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800">
    """
    for k in keys:
        html_content += f"""
                            <tr>
                                <td class="py-2 text-white font-bold">{k.name}</td>
                                <td class="py-2 text-yellow-500 font-mono">{k.key}</td>
                                <td class="py-2 font-mono">{k.used} / {k.limit}</td>
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

            <!-- Global Analytics Feed -->
            <div class="mt-6 panel p-5 rounded-xl">
                <h2 class="text-sm font-bold mb-4 text-blue-400 uppercase tracking-wider">Gateway Query Tracker Traffic Feed</h2>
                <div class="overflow-x-auto max-h-60 text-xs">
                    <table class="w-full text-left font-mono">
                        <thead>
                            <tr class="border-b border-gray-800 text-gray-400">
                                <th class="pb-2">TIMESTAMP</th>
                                <th class="pb-2">TOKEN REF</th>
                                <th class="pb-2">ENDPOINT RESOURCE</th>
                                <th class="pb-2">LOOKUP DATA PARAMETERS</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800">
    """
    for log in logs:
        html_content += f"""
                            <tr>
                                <td class="py-2 text-gray-500">{log.timestamp}</td>
                                <td class="py-2 text-yellow-600 font-bold">{log.key_used}</td>
                                <td class="py-2 text-green-400">/api/{log.endpoint}</td>
                                <td class="py-2 text-gray-300 font-sans bg-gray-900 bg-opacity-50 px-2 py-0.5 rounded">{log.query_params}</td>
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
    try:
        new_key = APIKey(
            key=key, name=name, limit=limit,
            expires_at=datetime.fromisoformat(expires_at),
            allowed_tools=allowed_tools, is_active=True
        )
        db.merge(new_key)
        db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin/delete-key")
async def delete_key(key: str, db: Session = Depends(get_db)):
    try:
        db_key = db.query(APIKey).filter(APIKey.key == key).first()
        if db_key:
            db.delete(db_key)
            db.commit()
    except Exception:
        db.rollback()
    return RedirectResponse(url="/", status_code=303)
