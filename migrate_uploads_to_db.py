import os
import io
from contextlib import suppress
from flask import Flask

from app import app, db
from models import (
    StoredFile,
    News,
    Event,
    Teacher,
    Facility,
    Syllabus,
    SchoolSetting,
)

# Fields to migrate: mapping of (Model, field_name)
TARGETS = [
    (News, "image_path"),
    (Event, "image_path"),
    (Teacher, "image_path"),
    (Facility, "image_path"),
    (Syllabus, "file_path"),
    (SchoolSetting, "school_logo_path"),
]


def ensure_db_file_from_local(filename: str) -> str | None:
    """
    Given a local filename (relative to static/uploads), read bytes,
    store into StoredFile, and return "/files/<id>". Returns None if not found.
    """
    if not filename or filename.startswith("/files/"):
        return filename

    # Resolve path from app config
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if not upload_folder:
        return None

    path = os.path.join(upload_folder, filename)
    if not os.path.exists(path):
        return None

    # Detect mimetype by extension (simple)
    lower = filename.lower()
    if lower.endswith((".jpg", ".jpeg")):
        mimetype = "image/jpeg"
    elif lower.endswith(".png"):
        mimetype = "image/png"
    elif lower.endswith(".gif"):
        mimetype = "image/gif"
    elif lower.endswith(".pdf"):
        mimetype = "application/pdf"
    else:
        mimetype = "application/octet-stream"

    with open(path, "rb") as f:
        data = f.read()

    sf = StoredFile(filename=filename, mimetype=mimetype, data=data)
    db.session.add(sf)
    db.session.commit()
    return f"/files/{sf.id}"


def migrate():
    migrated = 0
    with app.app_context():
        for Model, field in TARGETS:
            for obj in Model.query.all():
                val = getattr(obj, field, None)
                if not val or (isinstance(val, str) and val.startswith("/files/")):
                    continue
                new_path = ensure_db_file_from_local(val)
                if new_path:
                    setattr(obj, field, new_path)
                    migrated += 1
            db.session.commit()
    return migrated


if __name__ == "__main__":
    count = migrate()
    print(f"Migrated {count} file references to DB-backed /files/<id> paths.")
