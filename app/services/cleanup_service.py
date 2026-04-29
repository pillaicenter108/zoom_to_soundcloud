# app/services/cleanup_service.py
#
# Deletes all files and subfolders inside DOWNLOAD_DIR after a sync run.
# The downloads/ folder itself is preserved.

import os
import shutil
from app.config import DOWNLOAD_DIR


def cleanup_downloads(logs: list[str]) -> dict:
    """
    Remove every file and subdirectory inside DOWNLOAD_DIR.
    Appends human-readable log lines to the provided `logs` list.
    Returns a small summary dict: { deleted_files, deleted_dirs, errors }
    """
    deleted_files = 0
    deleted_dirs  = 0
    errors        = 0

    if not os.path.isdir(DOWNLOAD_DIR):
        logs.append(f"⚠️  downloads/ folder not found at {DOWNLOAD_DIR} — skipping cleanup.")
        return {"deleted_files": 0, "deleted_dirs": 0, "errors": 0}

    logs.append(f"🧹 Starting cleanup of downloads folder: {DOWNLOAD_DIR}")

    for entry in os.scandir(DOWNLOAD_DIR):
        try:
            if entry.is_file() or entry.is_symlink():
                os.remove(entry.path)
                logs.append(f"  🗑️  Deleted file: {entry.name}")
                deleted_files += 1
            elif entry.is_dir():
                shutil.rmtree(entry.path)
                logs.append(f"  🗑️  Deleted folder: {entry.name}/")
                deleted_dirs += 1
        except Exception as exc:
            logs.append(f"  ❌ Failed to delete {entry.name}: {exc}")
            errors += 1

    summary = (
        f"✅ Cleanup complete — "
        f"{deleted_files} file(s), {deleted_dirs} folder(s) deleted"
        + (f", {errors} error(s)" if errors else "")
        + "."
    )
    logs.append(summary)

    return {"deleted_files": deleted_files, "deleted_dirs": deleted_dirs, "errors": errors}