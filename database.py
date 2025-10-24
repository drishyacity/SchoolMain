import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Initialize SQLAlchemy with a base class
class Base(DeclarativeBase):
    pass

# Create a db instance
db = SQLAlchemy(model_class=Base)

# Database URL - using the provided PostgreSQL URL
DATABASE_URL = "postgresql://postgres:RcM6Fipm%2FN7Jy4t@db.fdwvijvptodpojjkfret.supabase.co:5432/postgres?sslmode=require"

def init_app(app):
    # Configure the database with the provided PostgreSQL URL
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", DATABASE_URL)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the database
    db.init_app(app)
