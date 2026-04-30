# app/soundcloud/upload.py

import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.util.ssl_ import create_urllib3_context


class TLSAdapter(HTTPAdapter):
    """Force TLS 1.2+ and modern ciphers — fixes SSLEOFError on some hosts."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")  # relax cipher strictness slightly
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


def _make_session() -> requests.Session:
    session = requests.Session()

    # Retry up to 3 times on connection/SSL errors with backoff: 0s, 2s, 4s
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    adapter = TLSAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://",  adapter)
    return session


def upload_track(token: str, file_path: str, title: str) -> bool:
    url = "https://api.soundcloud.com/tracks"

    headers = {
        "Authorization": f"OAuth {token}"
    }

    session = _make_session()

    try:
        with open(file_path, "rb") as audio:
            files = {
                "track[title]":       (None, title.replace("_", " ")),
                "track[sharing]":     (None, "private"),
                "track[downloadable]":(None, "true"),
                "track[asset_data]":  audio,
            }
            res = session.post(url, headers=headers, files=files, timeout=300)

        return res.status_code == 201

    except requests.exceptions.SSLError as e:
        print(f"[upload] SSL error for '{title}': {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[upload] Connection error for '{title}': {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"[upload] Timeout uploading '{title}'")
        return False
    finally:
        session.close()