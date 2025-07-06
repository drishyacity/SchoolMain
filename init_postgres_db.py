from app import app
from database import db
from models import User, SchoolSetting
from werkzeug.security import generate_password_hash

# Create the database tables
with app.app_context():
    # Create all tables
    db.create_all()
    print("Created database tables")
    
    # Check if admin user exists
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
    
print("Database initialization complete!")
