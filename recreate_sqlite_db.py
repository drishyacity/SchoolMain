import os
from app import app
from database import db

# Delete the existing database file
db_file = 'school_portal.db'
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Deleted existing database file: {db_file}")

# Create the database with the new schema
with app.app_context():
    db.create_all()
    print("Created new database with updated schema")
    
    # Create a default admin user
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=generate_password_hash("admin123"),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Created default admin user (username: admin, password: admin123)")
    
    # Create default school settings
    from models import SchoolSetting
    
    settings = SchoolSetting(
        school_name="Shree Gyan Bharti High School",
        school_address="123 Education Street, Knowledge City",
        school_phone="+91 1234567890",
        school_email="info@gyanbharti.edu"
    )
    db.session.add(settings)
    db.session.commit()
    print("Created default school settings")
    
print("Database setup complete!")
