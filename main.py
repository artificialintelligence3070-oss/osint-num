import os
import time
import json
import requests
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import APIKeyCookie

app = FastAPI(title="SHAYAN_EXPLORER LUXURY HUB")

# --- CONFIGURATION & SECURITY ---
TARGET_BASE_API = "https://ft-osint-api.duckdns.org/api"
MASTER_KEY = "explorer16"
ADMIN_USER = "vernex"
ADMIN_PASS = "vernex@16vx"

cookie_sec = APIKeyCookie(name="session_token", auto_error=False)

# ─── 🔒 PERMANENT HARDCODED KEYS MATRIX ──────────────────────────────────────
PERMANENT_STATIC_KEYS = {
    "shayan-vip": {
        "owner": "Shayan Owner Account",
        "token": "shayan-vip",
        "expiry": "LIFETIME ACCESS",
        "limit": 999999,
        "used": 0,
        "status": "Active",
        "scopes": ["ALL"]
    },
    "vx-osint": {
        "owner": "Master Default Access",
        "token": "vx-osint",
        "expiry": "2027-12-31 23:59:59",
        "limit": 50000,
        "used": 0,
        "status": "Active",
        "scopes": ["ALL"]
    }
}

# --- APPLICATION LIVE MEMORY DATABASE ---
API_KEYS_DB = {}
API_KEYS_DB.update(PERMANENT_STATIC_KEYS)
PIPELINE_LOGS = []
ROUTE_USAGE_COUNTER = {}

AVAILABLE_TOOLS = [
    "ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE",
    "IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", 
    "TG", "TGIDINFO", "NUMLEAK", "PK", "NAME", "AADHAR", "NUMTOUPI", "PAN", 
    "VEH2NUM", "ADHARFAMILY", "BOMBER"
]

for tool in AVAILABLE_TOOLS:
    ROUTE_USAGE_COUNTER[tool] = 0

def white_label_filter(raw_content: str) -> str:
    replacements = {
        "@ftgamer2": "@vernexzzz", "ftgamer2": "@vernexzzz", "ftgamer": "@vernexzzz",
        "https://t.me/lynx_api": "https://t.me/shayan_explorer_channel",
        "@bronex_ultra": "@vernexzzz", "@@bronex_ultra": "@vernexzzz",
        "@bornex_ultra": "@vernexzzz", "@@bornex_ultra": "@vernexzzz"
    }
    sanitized = raw_content
    for target, replacement in replacements.items():
        sanitized = sanitized.replace(target, replacement)
    return sanitized

# --- UI PREMIUM GLOWING LUXURY TEMPLATES ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SHAYAN EXPLORER - ATELIER</title>
    <style>
        body { background-color: #050505; color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #0c0c0e; border: 1px solid rgba(212, 175, 55, 0.3); padding: 50px 40px; border-radius: 8px; box-shadow: 0 0 30px rgba(212, 175, 55, 0.15), inset 0 0 15px rgba(212, 175, 55, 0.05); width: 340px; text-align: center; }
        h2 { color: #d4af37; font-weight: 300; font-size: 1.6rem; margin-bottom: 40px; letter-spacing: 4px; text-transform: uppercase; text-shadow: 0 0 10px rgba(212, 175, 55, 0.6); }
        .input-group { margin-bottom: 25px; text-align: left; }
        label { display: block; font-size: 0.7rem; color: #8e8e93; margin-bottom: 8px; letter-spacing: 2px; text-transform: uppercase; }
        input { width: 100%; padding: 12px; background: #121214; border: 1px solid #2c2c30; color: #fff; font-size: 0.9rem; box-sizing: border-box; transition: all 0.3s; border-radius: 4px; }
        input:focus { border-color: #d4af37; box-shadow: 0 0 12px rgba(212, 175, 55, 0.4); outline: none; }
        button { width: 100%; padding: 14px; background: #d4af37; border: none; color: #000; font-weight: 600; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; cursor: pointer; transition: all 0.3s; border-radius: 4px; box-shadow: 0 0 15px rgba(212, 175, 55, 0.4); }
        button:hover { background: #fff; box-shadow: 0 0 25px rgba(255, 255, 255, 0.6); }
        .error { color: #ff3b30; font-size: 0.75rem; margin-bottom: 20px; text-shadow: 0 0 8px rgba(255, 59, 48, 0.4); }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>SHAYAN EXPLORER</h2>
        <form method="POST" action="/login">
            <div class="input-group">
                <label>OPERATOR IDENTIFIER</label>
                <input type="text" name="username" required autocomplete="off">
            </div>
            <div class="input-group">
                <label>ACCESS SECURITY KEY</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">ENTER ATELIER</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SHAYAN EXPLORER CONSOLE</title>
    <style>
        html { scroll-behavior: smooth; }
        body { background-color: #040405; color: #e5e5e7; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; overflow-x: hidden; opacity: 0; animation: fadeInBody 0.8s ease forwards; }
        @keyframes fadeInBody { to { opacity: 1; } }
        
        .navbar { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(212, 175, 55, 0.2); padding: 20px 40px; background: #0a0a0c; position: sticky; top: 0; z-index: 99; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
        
        .profile-container { display: flex; align-items: center; gap: 15px; cursor: pointer; padding: 5px 12px; border-radius: 6px; transition: all 0.3s; border: 1px solid transparent; }
        .profile-container:hover { background: #121216; border-color: rgba(212, 175, 55, 0.3); box-shadow: 0 0 12px rgba(212, 175, 55, 0.2); }
        .avatar-frame { width: 42px; height: 42px; border-radius: 50%; border: 2px solid #d4af37; overflow: hidden; display: flex; justify-content: center; align-items: center; background: #1c1c22; box-shadow: 0 0 12px rgba(212,175,55,0.4); }
        .avatar-frame svg { width: 26px; height: 26px; fill: #d4af37; filter: drop-shadow(0 0 4px #d4af37); }
        .brand-title { color: #fff; font-weight: 300; font-size: 1.1rem; letter-spacing: 3px; text-transform: uppercase; text-shadow: 0 0 8px rgba(212, 175, 55, 0.5); }
        .brand-subtitle { font-size: 0.65rem; color: #8e8e93; letter-spacing: 1px; margin-top: 2px; }

        .sidebar-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 999; backdrop-filter: blur(6px); opacity: 0; transition: opacity 0.4s ease; }
        .sidebar { position: fixed; top: 0; left: -320px; width: 320px; height: 100%; background: #09090b; border-right: 1px solid rgba(212,175,55,0.2); z-index: 1000; box-shadow: 10px 0 30px rgba(0,0,0,0.5); transition: left 0.4s cubic-bezier(0.05, 0.74, 0.2, 0.99); padding: 40px 30px; box-sizing: border-box; display: flex; flex-direction: column; }
        .sidebar.open { left: 0; }
        .sidebar-overlay.open { display: block; opacity: 1; }
        
        .sidebar-header { margin-bottom: 50px; border-bottom: 1px solid #1c1c22; padding-bottom: 20px; text-align: center; }
        .sidebar-avatar-large { width: 80px; height: 80px; border-radius: 50%; border: 2px solid #d4af37; margin: 0 auto 15px; display: flex; justify-content: center; align-items: center; background: #121216; box-shadow: 0 0 15px rgba(212,175,55,0.3); }
        .sidebar-user { font-size: 0.75rem; color: #8e8e93; letter-spacing: 2px; text-transform: uppercase; }
        .sidebar-links { display: flex; flex-direction: column; gap: 12px; }
        .sidebar-item { background: #121216; border: 1px solid #222226; color: #e5e5e7; padding: 15px 20px; font-size: 0.8rem; text-decoration: none; letter-spacing: 1px; text-transform: uppercase; transition: all 0.3s; cursor: pointer; text-align: left; border-radius: 4px; }
        .sidebar-item:hover { background: #d4af37; color: #000; border-color: #d4af37; font-weight: 600; box-shadow: 0 0 15px rgba(212,175,55,0.4); }
        
        .main-container { padding: 40px; max-width: 1400px; margin: 0 auto; }
        .section-title { color: #d4af37; font-weight: 300; font-size: 1rem; margin-top: 50px; margin-bottom: 25px; letter-spacing: 3px; text-transform: uppercase; border-left: 3px solid #d4af37; padding-left: 15px; text-shadow: 0 0 10px rgba(212, 175, 55, 0.4); }
        .card { background: #0a0a0c; border: 1px solid #1c1c22; padding: 35px; margin-bottom: 30px; border-radius: 6px; box-shadow: 0 4px 25px rgba(0,0,0,0.4); }
        
        .grid-2 { display: grid; grid-template-columns: 1fr; gap: 25px; margin-bottom: 25px; }
        @media(min-width: 768px) { .grid-2 { grid-template-columns: 1fr 1fr; } }
        .input-box { display: flex; flex-direction: column; }
        .input-box label { font-size: 0.65rem; color: #8e8e93; margin-bottom: 8px; letter-spacing: 2px; text-transform: uppercase; }
        .input-box input, .input-box select { background: #121216; border: 1px solid #222226; padding: 14px; color: #fff; font-size: 0.85rem; font-family: inherit; transition: all 0.3s; border-radius: 4px; }
        .input-box input:focus { border-color: #d4af37; box-shadow: 0 0 12px rgba(212, 175, 55, 0.3); outline: none; }
        
        .analytics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; margin-bottom: 35px; }
        .analyzer-card { background: #0a0a0c; border: 1px solid rgba(212, 175, 55, 0.2); padding: 20px; position: relative; border-radius: 6px; box-shadow: 0 0 15px rgba(0,0,0,0.3); transition: all 0.3s; }
        .analyzer-card:hover { border-color: #d4af37; box-shadow: 0 0 18px rgba(212, 175, 55, 0.2); }
        .analyzer-title { font-size: 0.65rem; color: #c5a432; margin-bottom: 10px; letter-spacing: 2px; text-transform: uppercase; }
        .analyzer-value { font-size: 1.6rem; color: #fff; font-weight: 300; text-shadow: 0 0 8px rgba(255,255,255,0.1); }
        .metric-bar-bg { width: 100%; height: 4px; background: #1c1c22; margin-top: 15px; border-radius: 2px; overflow: hidden; }
        .metric-bar-fill { height: 100%; background: linear-gradient(90deg, #b89324, #d4af37); width: 0%; transition: width 1.2s ease; box-shadow: 0 0 8px #d4af37; }
        
        .tools-header { display: flex; justify-content: space-between; font-size: 0.65rem; margin-top: 30px; margin-bottom: 15px; color: #8e8e93; letter-spacing: 2px; text-transform: uppercase; }
        .tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
        .tool-check { background: #121216; border: 1px solid #222226; padding: 12px; display: flex; align-items: center; font-size: 0.75rem; cursor: pointer; color: #a1a1a6; transition: all 0.2s; border-radius: 4px; }
        .tool-check:hover { border-color: #d4af37; color: #fff; box-shadow: 0 0 10px rgba(212, 175, 55, 0.15); }
        .tool-check input { margin-right: 12px; accent-color: #d4af37; }
        
        .btn-container { display: flex; justify-content: flex-end; margin-top: 35px; }
        .submit-btn { background: #d4af37; border: none; color: #000; padding: 14px 40px; font-weight: 600; font-size: 0.75rem; letter-spacing: 2px; text-transform: uppercase; cursor: pointer; transition: all 0.3s; border-radius: 4px; box-shadow: 0 0 15px rgba(212,175,55,0.3); }
        .submit-btn:hover { background: #fff; box-shadow: 0 0 25px rgba(255,255,255,0.6); }
        
        table { width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left; }
        th { color: #8e8e93; font-weight: 400; padding-bottom: 15px; border-bottom: 1px solid #1c1c22; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.7rem; }
        td { padding: 16px 10px; border-bottom: 1px solid #121216; vertical-align: middle; color: #e5e5e7; }
        .badge-active { color: #30d158; font-weight: 500; text-shadow: 0 0 8px rgba(48,209,88,0.4); }
        .badge-suspended { color: #ff453a; font-weight: 500; text-shadow: 0 0 8px rgba(255,69,58,0.4); }
        .badge-scope { background: #121216; padding: 3px 8px; color: #d4af37; border: 1px solid rgba(212,175,55,0.3); display: inline-block; margin: 2px; font-size: 0.65rem; border-radius: 3px; }
        
        .actions-wrapper { display: flex; flex-direction: row; flex-wrap: nowrap; gap: 6px; justify-content: flex-start; align-items: center; width: max-content; }
        .btn-action { padding: 6px 14px; font-size: 0.65rem; font-weight: 500; text-decoration: none; cursor: pointer; border: 1px solid transparent; display: inline-block; text-align: center; transition: all 0.2s; letter-spacing: 1px; text-transform: uppercase; border-radius: 3px; }
        .btn-edit { background: transparent; border-color: #d4af37; color: #d4af37; }
        .btn-edit:hover { background: #d4af37; color: #000; box-shadow: 0 0 10px rgba(212,175,55,0.4); }
        .btn-reset { background: transparent; border-color: #0a84ff; color: #0a84ff; }
        .btn-reset:hover { background: #0a84ff; color: #fff; box-shadow: 0 0 10px rgba(10,132,255,0.4); }
        .btn-toggle { background: transparent; border-color: #30d158; color: #30d158; }
        .btn-toggle:hover { background: #30d158; color: #000; box-shadow: 0 0 10px rgba(48,209,88,0.4); }
        .btn-toggle.suspended { border-color: #ff453a; color: #ff453a; }
        .btn-toggle.suspended:hover { background: #ff453a; color: #fff; box-shadow: 0 0 10px rgba(255,69,58,0.4); }
        .btn-del { background: #ff453a; color: #fff; border-color: #ff453a; }
        .btn-del:hover { background: #ff3b30; box-shadow: 0 0 10px rgba(255,59,48,0.4); }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; z-index: 1001; backdrop-filter: blur(6px); }
        .modal-content { background: #0c0c0e; border: 1px solid rgba(212,175,55,0.3); padding: 40px; width: 90%; max-width: 650px; max-height: 85vh; overflow-y: auto; border-radius: 8px; box-shadow: 0 0 30px rgba(212,175,55,0.2); }
        .modal-title { color: #d4af37; font-weight: 300; font-size: 1.2rem; margin-bottom: 25px; letter-spacing: 2px; text-transform: uppercase; text-shadow: 0 0 8px rgba(212,175,55,0.4); }
        .close-modal { float: right; color: #8e8e93; cursor: pointer; font-size: 1.5rem; }
        .close-modal:hover { color: #fff; }
        .alert-banner { background: rgba(214,175,55,0.03); border: 1px solid rgba(212,175,55,0.4); padding: 18px 25px; color: #d4af37; font-size: 0.75rem; margin-bottom: 35px; line-height: 1.6; border-radius: 4px; box-shadow: inset 0 0 10px rgba(212,175,55,0.05); }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="profile-container" onclick="openSidebarMenu()">
            <div class="avatar-frame">
                <svg viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-12.5c-2.48 0-4.5 2.02-4.5 4.5s2.02 4.5 4.5 4.5 4.5-2.02 4.5-4.5-2.02-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                </svg>
            </div>
            <div>
                <div class="brand-title">SHAYAN EXPLORER</div>
                <div class="brand-subtitle">RAILWAY PROXY LIVE SYSTEM</div>
            </div>
        </div>
    </div>

    <div class="sidebar-overlay" id="menuOverlay" onclick="closeSidebarMenu()"></div>
    <div class="sidebar" id="menuSidebar">
        <div class="sidebar-header">
            <div class="sidebar-avatar-large">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="#d4af37">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z"/>
                </svg>
            </div>
            <div class="sidebar-user">OPERATOR: </div>
        </div>
        <div class="sidebar-links">
            <a class="sidebar-item" onclick="closeSidebarMenu(); scrollToSection('analytics-anchor');">📊 OVERVIEW DEVIATION METRICS</a>
            <a class="sidebar-item" onclick="closeSidebarMenu(); scrollToSection('provision-anchor');">🔑 PROVISION SYSTEM KEY</a>
            <a class="sidebar-item" onclick="closeSidebarMenu(); scrollToSection('registry-anchor');">🗂️ KEY REGISTRY MATRIX</a>
            <button class="sidebar-item" onclick="closeSidebarMenu(); openApisModal();">🌐 VIEW GATEWAY ROUTE URLS</button>
            <a href="/logout" class="sidebar-item" style="margin-top: 30px; border-color: #ff453a; color: #ff453a;">❌ SHUTDOWN SESSION</a>
        </div>
    </div>

    <div class="main-container">
        
        <div class="alert-banner">
            ✨ <strong>RAILWAY PROXY LIVE ENGINE ACTIVE:</strong> Your platform is now continuously powered. To preserve operational API tokens across code revisions or git updates, ensure you document critical keys within the <code>PERMANENT_STATIC_KEYS</code> code structure located inside the backend source.
        </div>

        <div id="analytics-anchor" class="section-title">📊 CALL TRANSACTION CALCULATION MATRIX</div>
        <div class="analytics-grid">
            </div>

        <div id="provision-anchor" class="section-title">🔑 PROPOSE SYSTEM COMMUNICATIONS KEY</div>
        <div class="card">
            <form method="POST" action="/keys/generate">
                <div class="grid-2">
                    <div class="input-box">
                        <label>TARGET OWNER IDENTITY NAME</label>
                        <input type="text" name="owner" placeholder="e.g. Prestige Client Profile" required autocomplete="off">
                    </div>
                    <div class="input-box">
                        <label>CUSTOM ASSIGNMENT TRACKING STRING (TOKEN KEY)</label>
                        <input type="text" name="token" placeholder="Leave empty for automated system generation hash" autocomplete="off">
                    </div>
                </div>
                <div class="grid-2">
                    <div class="input-box">
                        <label>DAILY CALL VOLUME VELOCITY LIMIT</label>
                        <input type="number" name="limit" value="5000" required>
                    </div>
                    <div class="input-box">
                        <label>EXPIRATION LIFECYCLE DATE & TIME (YYYY-MM-DD HH:MM:SS)</label>
                        <input type="text" name="expiry_date" placeholder="Type 'LIFETIME ACCESS' or specify an exact timestamp" value="LIFETIME ACCESS">
                    </div>
                </div>
                
                <div class="tools-header">
                    <div>ROUTE AUTHORIZATION PRIVILEGES MATRIX SCOPES</div>
                    <div style="color: #d4af37; cursor:pointer;" onclick="toggleAllTools('create-form')">[ SELECT ALL TOOLS ]</div>
                </div>
                <div class="tools-grid" id="create-form">
                    </div>
                <div class="btn-container">
                    <button type="submit" class="submit-btn">PROVISION GATEWAY KEY</button>
                </div>
            </form>
        </div>

        <div id="registry-anchor" class="section-title">🗂️ AUTHORIZED REGISTRY CONFIGURATION MATRIX</div>
        <div class="card" style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>OWNER IDENTITY</th>
                        <th>AUTHORIZATION TOKEN KEY</th>
                        <th>EXPIRY TIMELINE STATE</th>
                        <th>USAGE VELOCITY TRACKER</th>
                        <th>STATUS LAYERS</th>
                        <th>AUTHORIZED SCOPES</th>
                        <th>SYSTEM INTERVENTIONS</th>
                    </tr>
                </thead>
                <tbody>
                    </tbody>
            </table>
        </div>

        <div class="section-title">📡 LIVE INTERCEPTED REQUEST STREAMS PIPELINE LOGS</div>
        <div class="card" style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>TIMESTAMP INTERCEPTED</th>
                        <th>EXECUTING KEY STRING TOKEN</th>
                        <th>TARGET GATEWAY ROUTE</th>
                        <th>QUERY METRIC ARGUMENTS PASSED</th>
                    </tr>
                </thead>
                <tbody>
                    </tbody>
            </table>
        </div>

    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeEditModal()">&times;</span>
            <div class="modal-title">🔧 MODIFY MATRIX AUTHORIZATION PRIVILEGES</div>
            <form method="POST" action="/keys/edit">
                <input type="hidden" name="old_token" id="edit_old_token">
                <div class="grid-2">
                    <div class="input-box">
                        <label>OWNER IDENTITY</label>
                        <input type="text" name="owner" id="edit_owner" required autocomplete="off">
                    </div>
                    <div class="input-box">
                        <label>RE-ASSIGN SECURE STRING KEY</label>
                        <input type="text" name="token" id="edit_token" required autocomplete="off">
                    </div>
                </div>
                <div class="grid-2">
                    <div class="input-box">
                        <label>LIMIT VOLUME VELOCITY</label>
                        <input type="number" name="limit" id="edit_limit" required>
                    </div>
                    <div class="input-box">
                        <label>EXPIRATION LIFECYCLE DATE TIME</label>
                        <input type="text" name="expiry_date" id="edit_expiry" required>
                    </div>
                </div>
                <div class="tools-header">
                    <div>ROUTE PRIVILEGES MATRIX SCOPES</div>
                    <div style="color: #d4af37; cursor:pointer;" onclick="toggleAllTools('edit-form')">[ TOGGLE ALL SCOPES ]</div>
                </div>
                <div class="tools-grid" id="edit-form">
                    </div>
                <div class="btn-container">
                    <button type="submit" class="submit-btn" style="background: #fff; color:#000;">COMMIT UPDATED PARAMETERS</button>
                </div>
            </form>
        </div>
    </div>

    <div id="apisModal" class="modal">
        <div class="modal-content" style="max-width: 750px;">
            <span class="close-modal" onclick="closeApisModal()">&times;</span>
            <div class="modal-title">🌐 OPEN SYSTEM PATHWAYS (ACCESS WITHOUT KEYS VIEW)</div>
            <div style="font-size:0.75rem; color:#8e8e93; margin-bottom:20px;">Direct query routing paths for your system client requests:</div>
            <div id="urls-list" style="max-height: 50vh; overflow-y:auto; font-family: monospace; background:#121216; padding:20px; border:1px solid #1c1c22; border-radius:4px;">
            </div>
        </div>
    </div>

    <script>
        function openSidebarMenu() {
            document.getElementById('menuOverlay').classList.add('open');
            document.getElementById('menuSidebar').classList.add('open');
        }
        function closeSidebarMenu() {
            document.getElementById('menuOverlay').classList.remove('open');
            document.getElementById('menuSidebar').classList.remove('open');
        }
        function scrollToSection(id) {
            const target = document.getElementById(id);
            if(target) { window.scrollTo({ top: target.offsetTop - 100, behavior: 'smooth' }); }
        }
        function toggleAllTools(containerId) {
            let checkboxes = document.querySelectorAll('#' + containerId + ' input[type="checkbox"]');
            let allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        }
        function openEditModal(oldToken, owner, limit, expiry, activeScopesJson) {
            document.getElementById('edit_old_token').value = oldToken;
            document.getElementById('edit_owner').value = owner;
            document.getElementById('edit_token').value = oldToken;
            document.getElementById('edit_limit').value = limit;
            document.getElementById('edit_expiry').value = expiry;
            
            let activeScopes = JSON.parse(activeScopesJson);
            let checkboxes = document.querySelectorAll('.edit-tool-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = activeScopes.includes('ALL') || activeScopes.includes(cb.value);
            });
            document.getElementById('editModal').style.display = 'flex';
        }
        function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }
        function openApisModal() {
            let currentHost = window.location.origin;
            let tools = ["ADV", "PAYTM", "IMEI", "CALLTRACER", "UPI", "IFSC", "NUMBER", "PINCODE","IP", "CHALLAN", "FF", "BGMI", "SNAP", "EMAIL", "VEHICLE", "GIT", "INSTA", "TG", "TGIDINFO", "NUMLEAK", "PK", "NAME", "AADHAR", "NUMTOUPI", "PAN", "VEH2NUM", "ADHARFAMILY", "BOMBER"];
            let container = document.getElementById('urls-list');
            container.innerHTML = '';
            tools.forEach(t => {
                let lower = t.toLowerCase();
                container.innerHTML += `<div style="margin-bottom:14px; border-bottom:1px solid #1c1c22; padding-bottom:8px;"><span style="color:#d4af37; font-weight:bold;">[GET]</span> ${currentHost}/api/${lower}?key=<span style="color:#30d158;">YOUR_KEY</span>&param=value</div>`;
            });
            document.getElementById('apisModal').style.display = 'flex';
        }
        function closeApisModal() { document.getElementById('apisModal').style.display = 'none'; }
    </script>
</body>
</html>
"""

# --- AUTHENTICATION ENFORCEMENT ENGINE ---
def check_session(request: Request, session_token: Optional[str] = Depends(cookie_sec)):
    if not session_token or session_token != "authenticated_shayan_session":
        raise HTTPException(status_code=303, headers={"Location": "/"})
    return True

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303:
        return RedirectResponse(url=exc.headers.get("Location"), status_code=303)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --- PIPELINE ROUTING ENTRY POINTS ---

@app.get("/", response_class=HTMLResponse)
def get_login_page():
    return LOGIN_HTML.replace("", "")

@app.post("/login")
def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_token", value="authenticated_shayan_session", httponly=True)
        return response
    error_msg = '<div class="error">Access Denied: Invalid Security Operator Key</div>'
    return HTMLResponse(content=LOGIN_HTML.replace('', error_msg))

@app.get("/logout")
def handle_logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(auth: bool = Depends(check_session)):
    for k, v in PERMANENT_STATIC_KEYS.items():
        if k not in API_KEYS_DB: 
            API_KEYS_DB[k] = v

    rendered = DASHBOARD_HTML.replace("", ADMIN_USER)
    
    tools_html = "".join([f'<label class="tool-check"><input type="checkbox" name="scopes" value="{t}"> {t}</label>' for t in AVAILABLE_TOOLS])
    tools_edit_html = "".join([f'<label class="tool-check"><input type="checkbox" name="scopes" value="{t}" class="edit-tool-checkbox"> {t}</label>' for t in AVAILABLE_TOOLS])
    
    rendered = rendered.replace('', tools_html)
    rendered = rendered.replace('', tools_edit_html)

    total_calls = sum(ROUTE_USAGE_COUNTER.values())
    telemetry_list = sorted(ROUTE_USAGE_COUNTER.items(), key=lambda x: x[1], reverse=True)[:4]
    
    if total_calls == 0:
        telemetry_list = [("NUMBER", 0), ("UPI", 0), ("PAYTM", 0), ("VEHICLE", 0)]
    
    telemetry_html = ""
    for title, cnt in telemetry_list[:4]:
        pct = (cnt / total_calls * 100) if total_calls > 0 else 0
        telemetry_html += f"""
        <div class="analyzer-card">
            <div class="analyzer-title">ROUTE DEVIATION: {title}</div>
            <div class="analyzer-value">{cnt} <span style="font-size: 0.75rem; color:#8e8e93;">TRANSACTIONS</span></div>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: {pct}%;"></div>
            </div>
        </div>
        """
    rendered = rendered.replace('', telemetry_html)

    rows_list = []
    for k, v in API_KEYS_DB.items():
        scopes_badges = "".join([f'<span class="badge-scope">{s}</span>' for s in v["scopes"]])
        status_badge = f'<span class="badge-active">Active</span>' if v["status"] == "Active" else f'<span class="badge-suspended">Suspended</span>'
        scopes_json = json.dumps(v["scopes"]).replace('"', '&quot;')
        owner_escaped = v['owner'].replace("'", "\\'")
        
        row_ui = f"""
        <tr>
            <td>{v['owner']}</td>
            <td style="color: #d4af37; font-weight:500;">{v['token']}</td>
            <td style="color: #a1a1a6;">{v['expiry']}</td>
            <td>{v['used']} / {v['limit']}</td>
            <td>{status_badge}</td>
            <td>{scopes_badges}</td>
            <td>
                <div class="actions-wrapper">
                    <button class="btn-action btn-edit" onclick="openEditModal('{v['token']}', '{owner_escaped}', {v['limit']}, '{v['expiry']}', '{scopes_json}')">EDIT</button>
                    <a href="/keys/reset/{v['token']}" class="btn-action btn-reset">RESET</a>
                    <a href="/keys/toggle/{v['token']}" class="btn-action btn-toggle {'suspended' if v['status'] != 'Active' else ''}">TOGGLE</a>
                    <a href="/keys/delete/{v['token']}" class="btn-action btn-del">DEL</a>
                </div>
            </td>
        </tr>
        """
        rows_list.append(row_ui)
    rendered = rendered.replace("", "".join(rows_list))

    logs_list = []
    for log in reversed(PIPELINE_LOGS[-10:]):
        logs_list.append(f"""
        <tr>
            <td>{log['time']}</td>
            <td style="font-family:monospace; color:#8e8e93;">{log['token']}</td>
            <td><span class="badge-scope" style="color:#fff; border-color:#2c2c2e;">{log['route']}</span></td>
            <td style="font-family: monospace; color: #8e8e93;">{log['params']}</td>
        </tr>
        """)
    if not logs_list:
        logs_list.append('<tr><td colspan="4" style="text-align: center; color: #8e8e93; padding: 15px 0;">No active proxy execution tracking logs found.</td></tr>')
    rendered = rendered.replace("", "".join(logs_list))

    return rendered

# --- API LIFECYCLE CONTROLLERS ---

@app.post("/keys/generate")
def generate_key(owner: str = Form(...), token: Optional[str] = Form(None), limit: int = Form(...), expiry_date: Optional[str] = Form(None), scopes: List[str] = Form(None), auth: bool = Depends(check_session)):
    key_token = token.strip() if token and token.strip() else f"vx-{int(time.time())}"
    assigned_scopes = scopes if scopes else ["ALL"]
    expiry_str = expiry_date.strip() if expiry_date and expiry_date.strip() else "LIFETIME ACCESS"

    API_KEYS_DB[key_token] = {
        "owner": owner, "token": key_token, "expiry": expiry_str,
        "limit": limit, "used": 0, "status": "Active", "scopes": assigned_scopes
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/keys/edit")
def edit_key(old_token: str = Form(...), token: str = Form(...), owner: str = Form(...), limit: int = Form(...), expiry_date: str = Form(...), scopes: List[str] = Form(None), auth: bool = Depends(check_session)):
    assigned_scopes = scopes if scopes else ["ALL"]
    previous_usage_count = 0
    previous_status = "Active"
    
    if old_token in API_KEYS_DB:
        previous_usage_count = API_KEYS_DB[old_token]["used"]
        previous_status = API_KEYS_DB[old_token]["status"]
        del API_KEYS_DB[old_token]

    API_KEYS_DB[token] = {
        "owner": owner, "token": token, "expiry": expiry_date,
        "limit": limit, "used": previous_usage_count, "status": previous_status, "scopes": assigned_scopes
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/toggle/{token}")
def toggle_key(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB:
        current = API_KEYS_DB[token]["status"]
        API_KEYS_DB[token]["status"] = "Suspended" if current == "Active" else "Active"
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/reset/{token}")
def reset_key_usage(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB:
        API_KEYS_DB[token]["used"] = 0
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/keys/delete/{token}")
def delete_key(token: str, auth: bool = Depends(check_session)):
    if token in API_KEYS_DB: del API_KEYS_DB[token]
    if token in PERMANENT_STATIC_KEYS: del PERMANENT_STATIC_KEYS[token]
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# --- CORE BACKEND PROXY GATEWAY ROUTE ---
@app.get("/api/{route}")
def proxy_gateway(route: str, request: Request, key: str):
    for k, v in PERMANENT_STATIC_KEYS.items():
        if k not in API_KEYS_DB: API_KEYS_DB[k] = v

    if key not in API_KEYS_DB:
        return JSONResponse(status_code=403, content={"error": "Access Revoked: Invalid Identification Matrix Token"})
    
    key_profile = API_KEYS_DB[key]
    if key_profile["status"] != "Active":
        return JSONResponse(status_code=403, content={"error": "Access Denied: Suspended Token Identification Framework"})

    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query_params = dict(request.query_params)
    if "key" in query_params: del query_params["key"]
    
    PIPELINE_LOGS.append({"time": current_time_str, "token": key, "route": route.upper(), "params": str(query_params)})
    
    route_upper = route.upper()
    ROUTE_USAGE_COUNTER[route_upper] = ROUTE_USAGE_COUNTER.get(route_upper, 0) + 1

    if "ALL" not in key_profile["scopes"] and route_upper not in key_profile["scopes"]:
        return JSONResponse(status_code=403, content={"error": f"Unauthorized Access Scope Framework for Sub-Tool: {route_upper}"})

    if key_profile["expiry"] != "LIFETIME ACCESS":
        try:
            if current_time_str > key_profile["expiry"]:
                return JSONResponse(status_code=403, content={"error": "Token lifecycle operation window has expired."})
        except Exception:
            pass
            
    if key_profile["used"] >= key_profile["limit"]:
        return JSONResponse(status_code=429, content={"error": "Transaction call allocation volume limits fully exhausted."})

    key_profile["used"] += 1

    upstream_params = dict(request.query_params)
    upstream_params["key"] = MASTER_KEY 
    
    try:
        target_url = f"{TARGET_BASE_API}/{route}"
        upstream_response = requests.get(target_url, params=upstream_params, timeout=12)
        cleaned_text_payload = white_label_filter(upstream_response.text)
        try:
            return JSONResponse(status_code=upstream_response.status_code, content=json.loads(cleaned_text_payload))
        except json.JSONDecodeError:
            return HTMLResponse(status_code=upstream_response.status_code, content=cleaned_text_payload)
    except requests.exceptions.RequestException as exc:
        return JSONResponse(status_code=502, content={"error": "Upstream communication gateway failure", "details": str(exc)})
