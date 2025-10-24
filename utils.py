import os
import uuid
import json
import logging
import io
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image, ImageOps
from database import db
from models import StoredFile
from supabase import create_client
import requests

def allowed_file(filename, allowed_extensions):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_folder, crop_data=None):
    """
    Save an uploaded file and return the filename
    Process images with simple cropping if crop_data is provided
    """
    # Generate unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"

    # Log the upload attempt
    logging.info(f"Attempting to save file: {filename} as {unique_filename}")

    # Process image if it's an image file
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        try:
            # Reset file pointer to beginning
            file.seek(0)
            # Read file data first for fallback
            file_data = file.read()
            file.seek(0)  # Reset again for PIL

            # Open the image
            img = Image.open(file)
            logging.info(f"Successfully opened image: {img.size}, mode: {img.mode}")

            # Get original dimensions
            orig_width, orig_height = img.size

            # Resize very large images to reasonable size for processing
            max_dimension = 1200
            if max(orig_width, orig_height) > max_dimension:
                if orig_width > orig_height:
                    new_width = max_dimension
                    new_height = int((orig_height * max_dimension) / orig_width)
                else:
                    new_height = max_dimension
                    new_width = int((orig_width * max_dimension) / orig_height)

                img = img.resize((new_width, new_height), Image.LANCZOS)
                orig_width, orig_height = new_width, new_height

            # Default values
            position_type = 'teaching'  # Default
            zoom = 1.0
            pos_x = 0
            pos_y = 0

            if crop_data:
                try:
                    crop_info = json.loads(crop_data)
                    position_type = crop_info.get('positionType', 'teaching')

                    # Get zoom and position data if available
                    zoom = float(crop_info.get('zoom', 1.0))
                    # Clamp zoom to a sane range to avoid degenerate crops
                    if not (zoom > 0):
                        zoom = 1.0
                    zoom = max(1.0, min(zoom, 6.0))
                    pos_x = float(crop_info.get('posX', 0))
                    pos_y = float(crop_info.get('posY', 0))

                    logging.info(f"Processing image with zoom: {zoom}, posX: {pos_x}, posY: {pos_y}, position type: {position_type}")
                except Exception as e:
                    logging.error(f"Error parsing crop data: {str(e)}")

            # Simplified robust crop: always produce a 400x400 thumbnail using cover-fit
            target_width = 400
            target_height = 400
            try:
                img = ImageOps.fit(img, (target_width, target_height), Image.LANCZOS, centering=(0.5, 0.5))
            except Exception as e:
                logging.error(f"ImageOps.fit failed: {e}; falling back to basic resize and center-crop")
                # Fallback: basic resize keeping aspect, then center crop
                img.thumbnail((max(target_width, target_height)*2, max(target_width, target_height)*2), Image.LANCZOS)
                w, h = img.size
                left = max(0, (w - target_width)//2)
                top = max(0, (h - target_height)//2)
                img = img.crop((left, top, left+target_width, top+target_height))

            # Save the processed image with proper format while preserving background/transparency
            buf = io.BytesIO()
            # Choose format based on original extension
            save_format = 'JPEG' if filename.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
            if save_format == 'JPEG':
                # JPEG does not support transparency; flatten only for JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    # Use alpha as mask if present
                    alpha_src = img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                    bg.paste(img, mask=alpha_src)
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            else:
                # PNG supports transparency; keep as-is. Convert palette to RGBA to preserve alpha correctly.
                if img.mode == 'P':
                    img = img.convert('RGBA')

            img.save(buf, save_format, quality=95, optimize=True)
            file_bytes = buf.getvalue()
            logging.info(f"Image processed and buffered successfully ({target_width}x{target_height}), {len(file_bytes)} bytes")

        except Exception as e:
            logging.error(f"Error processing image: {str(e)}")
            # If there's an error, fall back to using the raw uploaded bytes
            file_bytes = file_data or file.read()
    else:
        # Save the original file if not an image
        file.seek(0)
        file_bytes = file.read()
        logging.info(f"Buffered non-image file: {len(file_bytes)} bytes")
    mimetype = getattr(file, 'content_type', None) or (
        'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg')) else
        'image/png' if filename.lower().endswith('.png') else
        'application/octet-stream'
    )

    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    bucket = os.environ.get('SUPABASE_BUCKET', 'school')
    if not supabase_url or not supabase_key:
        stored = StoredFile(filename=unique_filename, mimetype=mimetype, data=file_bytes)
        db.session.add(stored)
        db.session.commit()
        return f"/files/{stored.id}"

    client = create_client(supabase_url, supabase_key)
    object_path = f"uploads/{unique_filename}"
    client.storage.from_(bucket).upload(
        object_path,
        file_bytes,
        file_options={
            'content-type': mimetype,
            'upsert': 'true'
        }
    )
    public_url = client.storage.from_(bucket).get_public_url(object_path)
    # Normalize to string URL
    url_str = None
    try:
        if isinstance(public_url, dict):
            data = public_url.get('data') if hasattr(public_url, 'get') else None
            if isinstance(data, dict) and 'publicUrl' in data:
                url_str = data['publicUrl']
            elif 'publicUrl' in public_url:
                url_str = public_url['publicUrl']
        if not url_str:
            url_str = str(public_url)
    except Exception:
        url_str = str(public_url)

    # Validate URL is reachable; fallback to DB storage if not
    try:
        resp = requests.head(url_str, timeout=5)
        if resp.status_code >= 200 and resp.status_code < 400:
            return url_str
        # Try GET as some providers don't support HEAD
        resp = requests.get(url_str, stream=True, timeout=8)
        if resp.status_code >= 200 and resp.status_code < 400:
            return url_str
        logging.warning(f"Supabase public URL not reachable (status {resp.status_code}); falling back to DB storage")
    except Exception as e:
        logging.warning(f"Error validating public URL: {e}; falling back to DB storage")

    stored = StoredFile(filename=unique_filename, mimetype=mimetype, data=file_bytes)
    db.session.add(stored)
    db.session.commit()
    return f"/files/{stored.id}"

def delete_storage_url(url: str):
    try:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        bucket = os.environ.get('SUPABASE_BUCKET', 'school')
        if not supabase_url or not supabase_key:
            return
        marker = '/storage/v1/object/public/'
        if marker not in url:
            return
        after = url.split(marker, 1)[1]
        parts = after.split('/', 1)
        if len(parts) != 2:
            return
        bucket_in_url, object_path = parts
        if bucket_in_url != bucket:
            return
        client = create_client(supabase_url, supabase_key)
        client.storage.from_(bucket).remove([object_path])
    except Exception:
        pass
