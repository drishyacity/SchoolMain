import os
from supabase import create_client
from app import app, db
from models import StoredFile, News, Event, Teacher, Facility, Syllabus, SchoolSetting, HomeSlider

# List of (Model, field_name) to update
TARGETS = [
    (News, "image_path"),
    (Event, "image_path"),
    (Teacher, "image_path"),
    (Facility, "image_path"),
    (Syllabus, "file_path"),
    (SchoolSetting, "school_logo_path"),
    (HomeSlider, "image_path"),
]

PUBLIC_MARKER = "/storage/v1/object/public/"


def is_db_path(value: str) -> bool:
    return isinstance(value, str) and value.startswith("/files/")


def migrate_one(stored: StoredFile, client, bucket: str) -> str:
    object_path = f"uploads/{stored.filename}"
    client.storage.from_(bucket).upload(object_path, stored.data, {
        'contentType': stored.mimetype or 'application/octet-stream',
        'upsert': 'true'
    })
    public_url = client.storage.from_(bucket).get_public_url(object_path)
    if isinstance(public_url, dict) and 'publicUrl' in public_url:
        return public_url['publicUrl']
    return str(public_url)


def migrate():
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    bucket = os.environ.get('SUPABASE_BUCKET', 'school')
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing in environment")

    client = create_client(supabase_url, supabase_key)
    migrated_count = 0

    with app.app_context():
        for Model, field in TARGETS:
            rows = Model.query.all()
            for row in rows:
                value = getattr(row, field, None)
                if not value:
                    continue
                if PUBLIC_MARKER in value:
                    continue  # already in storage
                if not is_db_path(value):
                    continue  # not a DB /files/<id> reference
                try:
                    file_id = int(value.rsplit('/', 1)[-1])
                except Exception:
                    continue
                stored = StoredFile.query.get(file_id)
                if not stored or not stored.data:
                    continue
                try:
                    url = migrate_one(stored, client, bucket)
                    setattr(row, field, url)
                    db.session.add(row)
                    # delete stored file row after successful upload
                    db.session.delete(stored)
                    migrated_count += 1
                except Exception as e:
                    print(f"Failed to migrate file_id={file_id} for {Model.__tablename__}.{field}: {e}")
            db.session.commit()

    print(f"Migrated {migrated_count} references from DB to Supabase Storage bucket '{bucket}'.")


if __name__ == "__main__":
    migrate()
