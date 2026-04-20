# app/zoom/recordings.py

import os
import re
import json
import time
import requests
from app.config import DOWNLOAD_DIR

def clean_name(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.replace(" ", "_")

def state_file(choice):
    return f"uploaded_recordings_{choice}.json"

def load_uploaded(choice):
    file = state_file(choice)

    if not os.path.exists(file):
        return set()

    with open(file, "r") as f:
        return set(json.load(f))

def save_uploaded(choice, ids):
    with open(state_file(choice), "w") as f:
        json.dump(list(ids), f, indent=2)

def get_recordings(token, zoom, from_date, to_date):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    all_meetings = []
    next_page_token = ""

    while True:
        url = f"https://api.zoom.us/v2/users/{zoom['user_email']}/recordings"

        params = {
            "from": from_date,
            "to": to_date,
            "page_size": 300
        }

        if next_page_token:
            params["next_page_token"] = next_page_token

        res = requests.get(url, headers=headers, params=params)

        if res.status_code != 200:
            print("Recording Fetch Failed:", res.text)
            break

        data = res.json()

        all_meetings.extend(data.get("meetings", []))

        next_page_token = data.get("next_page_token", "")

        if not next_page_token:
            break

    return all_meetings

def download_audio(token, meeting, file):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    topic = clean_name(meeting.get("topic", "meeting"))
    file_type = file.get("file_type", "m4a").lower()

    filename = f"{topic}_{file['id']}.{file_type}"
    path = os.path.join(DOWNLOAD_DIR, filename)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    for attempt in range(3):
        try:
            r = requests.get(
                file["download_url"],
                headers=headers,
                stream=True,
                timeout=60
            )

            if r.status_code == 200:
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)

                return path

        except Exception as e:
            print(f"Retry {attempt+1}/3 failed:", e)
            time.sleep(3)

    return None