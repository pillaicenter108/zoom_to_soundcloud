# app/soundcloud/upload.py

import requests

def upload_track(token, file_path, title):
    url = "https://api.soundcloud.com/tracks"

    headers = {
        "Authorization": f"OAuth {token}"
    }

    files = {
        "track[title]": (None, title.replace("_", " ")),
        "track[sharing]": (None, "private"),
        "track[downloadable]": (None, "true"),
        "track[asset_data]": open(file_path, "rb")
    }

    res = requests.post(url, headers=headers, files=files)

    return res.status_code == 201