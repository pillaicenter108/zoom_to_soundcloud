# app/config.py

import os
from dotenv import load_dotenv

# Current file path = app/config.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root path
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Load .env from project root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

ZOOM_ACCOUNTS = {
    "1": {
        "account_id": os.getenv("ZOOM1_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM1_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM1_CLIENT_SECRET"),
        "user_email": os.getenv("ZOOM1_HOST_EMAIL")
    },

    "2": {
        "account_id": os.getenv("ZOOM2_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM2_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM2_CLIENT_SECRET"),
        "user_email": os.getenv("ZOOM2_HOST_EMAIL")
    },

    "3": {
        "account_id": os.getenv("ZOOM3_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM3_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM3_CLIENT_SECRET"),
        "user_email": os.getenv("ZOOM3_HOST_EMAIL")
    }
}

# SoundCloud
SC_CLIENT_ID = os.getenv("SC_CLIENT_ID")
SC_CLIENT_SECRET = os.getenv("SC_CLIENT_SECRET")

# Absolute Paths
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "downloads")
REFRESH_FILE = os.path.join(PROJECT_ROOT, "refresh_token.txt")