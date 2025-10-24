import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

# Initialize SQLAlchemy with a base class
class Base(DeclarativeBase):
    pass

# Create a db instance
db = SQLAlchemy(model_class=Base)

# Database URL - using the provided PostgreSQL URL
DATABASE_URL = "postgresql://postgres:RcM6Fipm%2FN7Jy4t@db.fdwvijvptodpojjkfret.supabase.co:5432/postgres?sslmode=require"

def init_app(app):
    # Prefer pooled URL (e.g., Supabase pgbouncer on port 6543) if provided
    pooled_url = os.environ.get("SUPABASE_DB_POOLED_URL")
    database_url = os.environ.get("DATABASE_URL", DATABASE_URL)
    if pooled_url:
        database_url = pooled_url

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    # Serverless-friendly engine options
    engine_opts = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # On serverless (Vercel), avoid persistent connection pools
    if os.environ.get("VERCEL") or os.environ.get("READ_ONLY_FS"):
        engine_opts["poolclass"] = NullPool
    else:
        # Keep pool very small for low-resource envs
        engine_opts["pool_size"] = int(os.environ.get("DB_POOL_SIZE", "3"))
        engine_opts["max_overflow"] = int(os.environ.get("DB_MAX_OVERFLOW", "0"))

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the database
    db.init_app(app)
