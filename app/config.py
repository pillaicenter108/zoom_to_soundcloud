# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

ZOOM_ACCOUNTS = {
    "1": {
        "account_id": os.getenv("ZOOM1_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM1_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM1_CLIENT_SECRET"),
        "user_email": os.getenv('ZOOM1_HOST_EMAIL')
    },
    "2": {
        "account_id": os.getenv("ZOOM2_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM2_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM2_CLIENT_SECRET"),
        "user_email": os.getenv('ZOOM2_HOST_EMAIL')
        },
    "3": {
        "account_id": os.getenv("ZOOM3_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM3_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM3_CLIENT_SECRET"),
        "user_email": os.getenv('ZOOM3_HOST_EMAIL')
    }
}

SC_CLIENT_ID = os.getenv("SC_CLIENT_ID")
SC_CLIENT_SECRET = os.getenv("SC_CLIENT_SECRET")

DOWNLOAD_DIR = "downloads"
REFRESH_FILE = "refresh_token.txt"