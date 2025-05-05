from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Create a db instance that all models will use
db = SQLAlchemy(model_class=Base)
