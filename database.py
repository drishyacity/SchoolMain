import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Initialize SQLAlchemy with a base class
class Base(DeclarativeBase):
    pass

# Create a db instance
db = SQLAlchemy(model_class=Base)

# Database URL - using the provided PostgreSQL URL
DATABASE_URL = "postgresql://postgres.lugpddujngbtrfouxeld:viraj1316mp@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

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
