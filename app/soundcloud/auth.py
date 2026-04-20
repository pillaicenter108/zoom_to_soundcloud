# app/soundcloud/auth.py

import os
import requests
from app.config import REFRESH_FILE, SC_CLIENT_ID, SC_CLIENT_SECRET

def load_refresh():
    if not os.path.exists(REFRESH_FILE):
        return None

    with open(REFRESH_FILE, "r") as f:
        return f.read().strip()

def save_refresh(token):
    with open(REFRESH_FILE, "w") as f:
        f.write(token)

def get_sc_token():
    refresh = load_refresh()

    if not refresh:
        return None

    url = "https://api.soundcloud.com/oauth2/token"

    data = {
        "client_id": SC_CLIENT_ID,
        "client_secret": SC_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh
    }

    res = requests.post(url, data=data)

    if res.status_code != 200:
        print("SoundCloud Auth Failed:", res.text)
        return None

    payload = res.json()

    if "refresh_token" in payload:
        save_refresh(payload["refresh_token"])

    return payload["access_token"]