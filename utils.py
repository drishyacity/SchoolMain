import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

def allowed_file(filename, allowed_extensions):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_folder, subfolder=''):
    """Save an uploaded file and return the filename"""
    # Create subfolder if specified
    if subfolder:
        subfolder_path = os.path.join(upload_folder, subfolder)
        os.makedirs(subfolder_path, exist_ok=True)
        target_folder = subfolder_path
    else:
        target_folder = upload_folder
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
    
    # Save the file
    file_path = os.path.join(target_folder, unique_filename)
    file.save(file_path)
    
    # Return relative path for database storage
    if subfolder:
        return os.path.join(subfolder, unique_filename)
    else:
        return unique_filename
