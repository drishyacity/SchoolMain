from app import app
from models import GalleryImage
from database import db
from datetime import datetime
import os

# Path to a test image file
test_image_path = "static/uploads/placeholder.jpg"

print(f"Checking if test image exists at: {test_image_path}")
if not os.path.exists(test_image_path):
    print(f"ERROR: Test image not found at {test_image_path}")
    exit(1)

print(f"Test image found at: {test_image_path}")

# Create a new gallery image entry
with app.app_context():
    # Read the image file
    print(f"Reading image file: {test_image_path}")
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"Read {len(image_data)} bytes from image file")
    
    # Create a new gallery image entry
    print("Creating new gallery image entry...")
    gallery_image = GalleryImage(
        title="Test Upload Image",
        caption="This is a test upload image",
        image_data=image_data,
        image_filename="test_upload_image.jpg",
        image_mimetype="image/jpeg",
        upload_date=datetime.now()
    )
    
    # Add to database
    db.session.add(gallery_image)
    db.session.commit()
    
    print(f"Added image to database with ID: {gallery_image.id}")
    
    # Verify it's in the database
    images = GalleryImage.query.all()
    print(f"Total images in database: {len(images)}")
    for img in images:
        print(f"ID: {img.id}, Title: {img.title}, Filename: {img.image_filename}, Size: {len(img.image_data)} bytes")
    
    print("Done!")
