from app import app
from database import db
import os
from sqlalchemy import text

# Create the database with the new schema
with app.app_context():
    # Drop the gallery_images table to recreate it with the new schema
    db.session.execute(text('DROP TABLE IF EXISTS gallery_images'))
    db.session.commit()
    print("Dropped gallery_images table")

    # Create all tables
    db.create_all()
    print("Created new database schema")

    # Check if admin user exists
    from models import User
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user (username: admin, password: admin123)")
    else:
        print("Admin user already exists")

    # Check if school settings exist
    from models import SchoolSetting

    settings = SchoolSetting.query.first()
    if not settings:
        settings = SchoolSetting(
            school_name="Shree Gyan Bharti High School",
            school_address="123 Education Street, Knowledge City",
            school_phone="+91 1234567890",
            school_email="info@gyanbharti.edu"
        )
        db.session.add(settings)
        db.session.commit()
        print("Created default school settings")
    else:
        print("School settings already exist")

print("Database setup complete!")
