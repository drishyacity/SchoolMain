import os
import uuid
import json
import logging
import io
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
from database import db
from models import StoredFile
from supabase import create_client

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
                    pos_x = float(crop_info.get('posX', 0))
                    pos_y = float(crop_info.get('posY', 0))

                    logging.info(f"Processing image with zoom: {zoom}, posX: {pos_x}, posY: {pos_y}, position type: {position_type}")
                except Exception as e:
                    logging.error(f"Error parsing crop data: {str(e)}")

            # If cropping data is provided, perform crop to target aspect; otherwise, keep original aspect.
            if crop_data:
                # Set target dimensions based on position type per requested layout
                if position_type == 'leadership':
                    target_width = 300
                    target_height = 400
                else:
                    target_width = 400
                    target_height = 400

                # Apply cropping with user's zoom and position data
                try:
                    scaled_width = orig_width * zoom
                    scaled_height = orig_height * zoom
                    center_x = (scaled_width / 2) + pos_x
                    center_y = (scaled_height / 2) + pos_y
                    crop_left = center_x - (target_width / 2)
                    crop_top = center_y - (target_height / 2)
                    crop_right = crop_left + target_width
                    crop_bottom = crop_top + target_height
                    orig_crop_left = max(0, min(crop_left / zoom, orig_width))
                    orig_crop_top = max(0, min(crop_top / zoom, orig_height))
                    orig_crop_right = max(0, min(crop_right / zoom, orig_width))
                    orig_crop_bottom = max(0, min(crop_bottom / zoom, orig_height))
                    img = img.crop((orig_crop_left, orig_crop_top, orig_crop_right, orig_crop_bottom))
                    logging.info(f"Image cropped from ({orig_crop_left}, {orig_crop_top}) to ({orig_crop_right}, {orig_crop_bottom})")
                except Exception as crop_error:
                    logging.error(f"Error in cropping: {str(crop_error)}, using center crop instead")
                    left = max(0, (orig_width - target_width) // 2)
                    top = max(0, (orig_height - target_height) // 2)
                    right = min(orig_width, left + target_width)
                    bottom = min(orig_height, top + target_height)
                    img = img.crop((left, top, right, bottom))

                # Resize to exact target dimensions only when cropping
                img = img.resize((target_width, target_height), Image.LANCZOS)
            else:
                # No cropping requested: keep original aspect (already optionally downscaled)
                logging.info("No crop_data provided; saving image without cropping and preserving aspect ratio")

            # Save the processed image with proper format
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB for JPEG compatibility
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            # Save image to bytes
            buf = io.BytesIO()
            # Choose format based on original extension
            save_format = 'JPEG' if filename.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
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
    if isinstance(public_url, dict):
        data = public_url.get('data') if hasattr(public_url, 'get') else None
        if isinstance(data, dict) and 'publicUrl' in data:
            return data['publicUrl']
        # some versions may return {'publicUrl': '...'}
        if 'publicUrl' in public_url:
            return public_url['publicUrl']
    return str(public_url)

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
