from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import requests
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='public')
CORS(app)  # enable CORS

DB_PATH = 'database.sqlite'

# Initialize database and create table if not exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

CLIENT_ID = "2f86a5b5-bef6-4c1a-9ce6-1753df6c0f6b"
CLIENT_SECRET = "yw71gnmh3g"
REDIRECT_URI = "https://www.google.co.in/"  # As per your setup

# Serve index.html and other static files
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/login', methods=['GET'])
def login():
    # Manual auth code paste approach - frontend handles this
    auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return jsonify({"auth_url": auth_url})

@app.route('/generate-token', methods=['POST'])
def generate_token():
    data = request.get_json()
    auth_code = data.get('authCode')

    if not auth_code:
        return jsonify({"error": "Authorization code is required"}), 400

    token_url = "https://api.upstox.com/v2/login/authorization/token"
    params = {
        'code': auth_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        resp = requests.post(token_url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        access_token = data.get('access_token')

        if not access_token:
            return jsonify({"error": "Failed to get access token"}), 500

        # Save access token to DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tokens (access_token) VALUES (?)", (access_token,))
        conn.commit()
        conn.close()

        return jsonify({"accessToken": access_token})

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/option-chain', methods=['GET'])
def option_chain():
    expiry_date = request.args.get('expiryDate')
    if not expiry_date:
        return jsonify({"error": "expiryDate parameter is required"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT access_token FROM tokens ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "No access token found. Please login first."}), 400

    access_token = row[0]

    url = "https://api.upstox.com/v2/option/chain"
    params = {
        'mode': 'option_chain',
        'instrument_key': 'NSE_INDEX|Nifty 50',
        'expiry_date': expiry_date
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)
