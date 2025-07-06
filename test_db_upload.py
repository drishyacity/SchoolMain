from app import app
from models import GalleryImage
from database import db
from datetime import datetime
import os

# Path to a test image file (use the placeholder image we already have)
source_image_path = "static/uploads/placeholder.jpg"

# Create the database with the new schema
with app.app_context():
    # Read the image file
    with open(source_image_path, 'rb') as f:
        image_data = f.read()
    
    # Create a new gallery image entry
    gallery_image = GalleryImage(
        title="Test Database Image",
        caption="This is a test image stored directly in the database",
        image_data=image_data,
        image_filename="test_db_image.jpg",
        image_mimetype="image/jpeg",
        upload_date=datetime.now()
    )
    
    # Add to database
    db.session.add(gallery_image)
    db.session.commit()
    
    print(f"Added image to database with ID: {gallery_image.id}")
    print(f"Image size: {len(image_data)} bytes")
    
    # Verify it's in the database
    images = GalleryImage.query.all()
    print(f"Total images in database: {len(images)}")
    for img in images:
        print(f"ID: {img.id}, Title: {img.title}, Filename: {img.image_filename}, Size: {len(img.image_data)} bytes")
