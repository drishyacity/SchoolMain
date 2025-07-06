import os
import uuid
import json
import logging
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image

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

    # Create full path
    file_path = os.path.join(upload_folder, unique_filename)

    # Log the upload attempt
    logging.info(f"Attempting to save file: {filename} as {unique_filename}")
    logging.info(f"Upload folder: {upload_folder}")
    logging.info(f"Full path: {file_path}")

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

            # Set target dimensions based on position type
            if position_type == 'leadership':
                # Square crop for leadership (1:1 aspect ratio)
                target_width = 400
                target_height = 400
            else:
                # Rectangle crop for teaching (4:3 aspect ratio)
                target_width = 400
                target_height = 300

            # Simplified cropping logic
            if crop_data:
                # Apply cropping with user's zoom and position data
                try:
                    # Calculate the scaled image dimensions
                    scaled_width = orig_width * zoom
                    scaled_height = orig_height * zoom

                    # Calculate the center position of the scaled image
                    center_x = scaled_width / 2
                    center_y = scaled_height / 2

                    # Apply user's position offset (posX, posY are in preview coordinates)
                    center_x += pos_x
                    center_y += pos_y

                    # Calculate the crop area in the scaled image coordinates
                    crop_left = center_x - (target_width / 2)
                    crop_top = center_y - (target_height / 2)
                    crop_right = crop_left + target_width
                    crop_bottom = crop_top + target_height

                    # Convert back to original image coordinates
                    orig_crop_left = crop_left / zoom
                    orig_crop_top = crop_top / zoom
                    orig_crop_right = crop_right / zoom
                    orig_crop_bottom = crop_bottom / zoom

                    # Ensure we don't crop outside the original image bounds
                    orig_crop_left = max(0, min(orig_crop_left, orig_width))
                    orig_crop_top = max(0, min(orig_crop_top, orig_height))
                    orig_crop_right = max(0, min(orig_crop_right, orig_width))
                    orig_crop_bottom = max(0, min(orig_crop_bottom, orig_height))

                    # Crop the image
                    img = img.crop((orig_crop_left, orig_crop_top, orig_crop_right, orig_crop_bottom))
                    logging.info(f"Image cropped from ({orig_crop_left}, {orig_crop_top}) to ({orig_crop_right}, {orig_crop_bottom})")
                except Exception as crop_error:
                    logging.error(f"Error in cropping: {str(crop_error)}, using center crop instead")
                    # Fallback to center crop
                    left = max(0, (orig_width - target_width) // 2)
                    top = max(0, (orig_height - target_height) // 2)
                    right = min(orig_width, left + target_width)
                    bottom = min(orig_height, top + target_height)
                    img = img.crop((left, top, right, bottom))
            else:
                # Simple center crop if no zoom data
                left = max(0, (orig_width - target_width) // 2)
                top = max(0, (orig_height - target_height) // 2)
                right = min(orig_width, left + target_width)
                bottom = min(orig_height, top + target_height)
                img = img.crop((left, top, right, bottom))
                logging.info(f"Applied center crop to {target_width}x{target_height}")

            # Resize to exact target dimensions
            img = img.resize((target_width, target_height), Image.LANCZOS)

            # Save the processed image with proper format
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB for JPEG compatibility
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            # Save with high quality
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                img.save(file_path, 'JPEG', quality=95, optimize=True)
            else:
                img.save(file_path, quality=95, optimize=True)

            logging.info(f"Image processed and saved successfully to {file_path} ({target_width}x{target_height})")

        except Exception as e:
            logging.error(f"Error processing image: {str(e)}")
            # If there's an error, fall back to saving the original file
            try:
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                logging.info(f"Saved original file as fallback: {file_path}")
            except Exception as fallback_error:
                logging.error(f"Failed to save fallback file: {str(fallback_error)}")
                # Last resort - try with file pointer
                file.seek(0)
                with open(file_path, 'wb') as f:
                    f.write(file.read())
    else:
        # Save the original file if not an image
        file.seek(0)
        file_data = file.read()
        with open(file_path, 'wb') as f:
            f.write(file_data)
        logging.info(f"Saved non-image file: {file_path}")

    # Return just the filename for database storage
    return unique_filename
