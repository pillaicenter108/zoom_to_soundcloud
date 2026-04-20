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


def run_sync(choice, from_date, to_date):
    zoom = ZOOM_ACCOUNTS.get(choice)

    if not zoom:
        return {"status": "error", "message": "Invalid account"}

    uploaded = load_uploaded(choice)

    zoom_token = get_zoom_token(zoom)
    sc_token = get_sc_token()

    meetings = get_recordings(
        zoom_token,
        zoom,
        from_date,
        to_date
    )

    new_count = 0

    for meeting in meetings:
        topic = clean_name(meeting.get("topic", "meeting"))

        for file in meeting.get("recording_files", []):

            if file.get("status") != "completed":
                continue

            if file.get("file_type", "").lower() not in ["m4a", "mp3"]:
                continue

            rec_id = str(file["id"])

            if rec_id in uploaded:
                continue

            file_path = download_audio(zoom_token, meeting, file)

            if not file_path:
                continue

            ok = upload_track(sc_token, file_path, topic)

            if ok:
                uploaded.add(rec_id)
                save_uploaded(choice, uploaded)
                new_count += 1

    return {
        "status": "success",
        "meetings_fetched": len(meetings),
        "new_uploads": new_count
    }