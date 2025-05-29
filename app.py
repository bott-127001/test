from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import sqlite3
from datetime import datetime, timedelta

app = FastAPI()

DB_FILE = "data.db"

CLIENT_ID = "2f86a5b5-bef6-4c1a-9ce6-1753df6c0f6b"
CLIENT_SECRET = "yw71gnmh3g"
REDIRECT_URI = "https://www.google.co.in/"

# Initialize DB and tables if not exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS access_token (
            id INTEGER PRIMARY KEY,
            token TEXT,
            expires_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS option_chain_data (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            raw_data TEXT,
            calculated_data TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class AuthCode(BaseModel):
    auth_code: str

@app.post("/auth/code")
async def exchange_auth_code(data: AuthCode):
    # Exchange auth code for access token from Upstox
    url = "https://api.upstox.com/v2/login/authorization/token"
    params = {
        "code": data.auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params, headers=headers)
    
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange auth code")

    resp_json = resp.json()
    access_token = resp_json.get("access_token")
    expires_in = resp_json.get("expires_in")  # usually in seconds

    if not access_token or not expires_in:
        raise HTTPException(status_code=400, detail="Invalid response from Upstox")

    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # Save token to DB (replace old token if exists)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM access_token")
    c.execute("INSERT INTO access_token (token, expires_at) VALUES (?, ?)", (access_token, expires_at.isoformat()))
    conn.commit()
    conn.close()

    return {"access_token": access_token, "expires_at": expires_at.isoformat()}

@app.get("/auth/token")
def get_access_token():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT token, expires_at FROM access_token ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No access token found. Please login.")

    token, expires_at_str = row
    expires_at = datetime.fromisoformat(expires_at_str)
    if datetime.utcnow() >= expires_at:
        raise HTTPException(status_code=401, detail="Access token expired. Please login again.")

    return {"access_token": token, "expires_at": expires_at_str}
