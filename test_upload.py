import os
import shutil
from datetime import datetime
from app import app
from models import GalleryImage
from database import db

# Path to a test image file (use the placeholder image we already have)
source_image = "static/uploads/placeholder.jpg"

# Create a new filename
new_filename = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
destination = os.path.join("static/uploads", new_filename)

# Copy the file
print(f"Copying {source_image} to {destination}")
shutil.copy2(source_image, destination)

# Verify the file exists
if os.path.exists(destination):
    print(f"File successfully copied to {destination}")
    
    # Add to database
    with app.app_context():
        gallery_image = GalleryImage(
            title="Test Image",
            caption="This is a test image",
            image_path=new_filename,
            upload_date=datetime.now()
        )
        db.session.add(gallery_image)
        db.session.commit()
        print(f"Added image to database with ID: {gallery_image.id}")
        
        # Verify it's in the database
        images = GalleryImage.query.all()
        print(f"Total images in database: {len(images)}")
        for img in images:
            print(f"ID: {img.id}, Title: {img.title}, Path: {img.image_path}")
else:
    print(f"ERROR: Failed to copy file to {destination}")
