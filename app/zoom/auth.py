# app/zoom/auth.py

import requests
import base64

def get_zoom_token(zoom):
    url = "https://zoom.us/oauth/token"

    creds = f"{zoom['client_id']}:{zoom['client_secret']}"
    encoded = base64.b64encode(creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}"
    }

    params = {
        "grant_type": "account_credentials",
        "account_id": zoom["account_id"]
    }

    res = requests.post(url, headers=headers, params=params)

    if res.status_code != 200:
        print("Zoom Auth Failed:", res.text)
        return None

    return res.json()["access_token"]