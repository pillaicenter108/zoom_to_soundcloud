# app/services/sync_service.py

from app.config import ZOOM_ACCOUNTS
from app.zoom.auth import get_zoom_token
from app.zoom.recordings import (
    get_recordings,
    download_audio,
    load_uploaded,
    save_uploaded,
    clean_name
)
from app.soundcloud.auth import get_sc_token
from app.soundcloud.upload import upload_track
from app.services.cleanup_service import cleanup_downloads


def run_sync(choice, from_date, to_date, logs: list = None):
    # Accept a shared live list from the caller (main.py background thread)
    # so every append is instantly visible via /status — fall back to a local
    # list when called directly (e.g. tests or CLI).
    if logs is None:
        logs = []

    logs.append("🚀 Starting Zoom → SoundCloud Sync")

    zoom = ZOOM_ACCOUNTS.get(choice)

    if not zoom:
        logs.append("❌ Invalid Zoom account selected")
        return {
            "status": "error",
            "logs": logs,
            "meetings_fetched": 0,
            "new_uploads": 0
        }

    uploaded = load_uploaded(choice)

    # Zoom Auth
    zoom_token = get_zoom_token(zoom)

    if not zoom_token:
        logs.append("❌ Zoom authentication failed")
        return {
            "status": "error",
            "logs": logs,
            "meetings_fetched": 0,
            "new_uploads": 0
        }

    logs.append("✅ Zoom authenticated")

    # SoundCloud Auth
    sc_token = get_sc_token()

    if not sc_token:
        logs.append("❌ SoundCloud authentication failed")
        return {
            "status": "error",
            "logs": logs,
            "meetings_fetched": 0,
            "new_uploads": 0
        }

    logs.append("✅ SoundCloud authenticated")

    # Fetch Meetings
    meetings = get_recordings(zoom_token, zoom, from_date, to_date)

    logs.append(f"📥 Meetings fetched: {len(meetings)}")

    new_count = 0
    recordings_fetched = 0

    for meeting in meetings:
        topic = clean_name(meeting.get("topic", "meeting"))

        for file in meeting.get("recording_files", []):

            if file.get("status") != "completed":
                continue

            if file.get("file_type", "").lower() not in ["m4a", "mp3"]:
                continue

            recordings_fetched += 1

            rec_id = str(file["id"])

            if rec_id in uploaded:
                logs.append(f"⏭ Already uploaded: {topic}")
                continue

            # Download
            file_path = download_audio(zoom_token, meeting, file)

            if not file_path:
                logs.append(f"❌ Download failed: {topic}")
                continue

            logs.append(f"⬇️ Downloaded: {topic}")

            # Upload
            ok = upload_track(sc_token, file_path, topic)

            if ok:
                uploaded.add(rec_id)
                save_uploaded(choice, uploaded)
                logs.append(f"🎧 Uploaded: {topic}")
                new_count += 1
            else:
                logs.append(f"❌ Upload failed: {topic}")

    logs.append(f"✅ Sync completed | New uploads: {new_count}")

    # Silently clean up downloads folder in a background thread — no logs
    import threading
    threading.Thread(target=cleanup_downloads, args=([],), daemon=True).start()

    return {
        "status": "success",
        "logs": logs,
        "meetings_fetched": recordings_fetched,
        "new_uploads": new_count
    }