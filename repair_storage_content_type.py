import os
import mimetypes
import requests
from urllib.parse import urlparse
from supabase import create_client
from app import app, db
from models import News, Event, Teacher, Facility, Syllabus, SchoolSetting, HomeSlider

PUBLIC_MARKER = "/storage/v1/object/public/"
BUCKET = os.environ.get('SUPABASE_BUCKET', 'school')

TARGETS = [
    (News, "image_path"),
    (Event, "image_path"),
    (Teacher, "image_path"),
    (Facility, "image_path"),
    (Syllabus, "file_path"),
    (SchoolSetting, "school_logo_path"),
    (HomeSlider, "image_path"),
]

def url_to_object_path(url: str) -> str | None:
    if PUBLIC_MARKER not in url:
        return None
    after = url.split(PUBLIC_MARKER, 1)[1]
    parts = after.split('/', 1)
    if len(parts) != 2:
        return None
    bucket_in_url, object_path = parts
    if bucket_in_url != BUCKET:
        return None
    return object_path


def infer_mimetype(url: str) -> str:
    # try queryless path for guessing
    path = urlparse(url).path
    mt, _ = mimetypes.guess_type(path)
    return mt or 'application/octet-stream'


def repair():
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")

    client = create_client(supabase_url, supabase_key)
    fixed = 0

    with app.app_context():
        for Model, field in TARGETS:
            rows = Model.query.all()
            for row in rows:
                value = getattr(row, field, None)
                if not value or PUBLIC_MARKER not in value:
                    continue
                object_path = url_to_object_path(value)
                if not object_path:
                    continue
                try:
                    # fetch current bytes
                    resp = requests.get(value, timeout=30)
                    if resp.status_code != 200 or not resp.content:
                        continue
                    mimetype = infer_mimetype(value)
                    client.storage.from_(BUCKET).upload(
                        object_path,
                        resp.content,
                        file_options={
                            'content-type': mimetype,
                            'upsert': 'true'
                        }
                    )
                    fixed += 1
                except Exception as e:
                    print(f"Failed to repair {Model.__tablename__}.{field} url={value}: {e}")
    print(f"Repaired content-type for {fixed} storage objects.")


if __name__ == '__main__':
    repair()
