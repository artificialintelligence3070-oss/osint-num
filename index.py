from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Locate database.json at the root of the project
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'database.json')

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"keys": {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# 1. Main Data Lookup
@app.route('/api/number', methods=['GET'])
def get_number_info():
    user_key = request.args.get('key')
    phone_num = request.args.get('num')

    if not user_key or not phone_num:
        return jsonify({"status": "error", "message": "Missing 'key' or 'num' parameter"}), 400

    db = load_db()
    keys_data = db.get("keys", {})

    if user_key not in keys_data:
        return jsonify({"status": "error", "message": "Invalid API Key"}), 403

    key_info = keys_data[user_key]
    expiry_date = datetime.strptime(key_info['expiry'], '%Y-%m-%d').date()
    
    if datetime.now().date() > expiry_date:
        return jsonify({"status": "error", "message": "API Key has expired"}), 403

    if key_info['uses'] >= key_info['limit']:
        return jsonify({"status": "error", "message": "API Key limit exceeded"}), 429

    target_api_url = f"https://ft-osint-api.duckdns.org/api/number?key=vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f&num={phone_num}"
    
    try:
        response = requests.get(target_api_url, timeout=10)
        api_data = response.json()
        
        key_info['uses'] += 1
        save_db(db)
        
        return jsonify({
            "status": "success",
            "credits_remaining": key_info['limit'] - key_info['uses'],
            "data": api_data
        })
    except requests.exceptions.RequestException:
        return jsonify({"status": "error", "message": "Failed to fetch data from provider"}), 500

# 2. Key Generation
@app.route('/api/admin/generate-key', methods=['POST'])
def generate_key():
    data = request.json or {}
    custom_key = data.get('key')
    expiry = data.get('expiry')
    limit = data.get('limit')

    if not custom_key or not expiry or not limit:
        return jsonify({"status": "error", "message": "Missing key, expiry, or limit in body"}), 400

    try:
        datetime.strptime(expiry, '%Y-%m-%d')
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid expiry date format. Use YYYY-MM-DD"}), 400

    db = load_db()
    if custom_key in db["keys"]:
        return jsonify({"status": "error", "message": "Key already exists"}), 400

    db["keys"][custom_key] = {
        "expiry": expiry,
        "limit": int(limit),
        "uses": 0
    }
    save_db(db)
    return jsonify({"status": "success", "message": f"Key '{custom_key}' generated."})
