from app import app
from models import GalleryImage
from database import db

with app.app_context():
    images = GalleryImage.query.all()
    print(f"Found {len(images)} gallery images in database:")
    for img in images:
        print(f"ID: {img.id}, Title: {img.title}, Path: {img.image_path}")
