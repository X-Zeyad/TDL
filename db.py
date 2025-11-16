# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


def get_database_url_from_env():
# Prefer full DATABASE_URL, else build from parts
    url = os.getenv('DATABASE_URL')
    if url:
        return url
    user = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    host = os.getenv('HOSTNAME')
    port = os.getenv('PORT', '3306')
    db = os.getenv('DB_NAME', 'todo_db')
    # SSL for Azure MySQL
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"


def init_db(database_url=None):
    database_url = database_url or get_database_url_from_env()
    connect_args = {"ssl": {"ssl_ca": "/etc/ssl/certs/ca-certificates.crt"}}
    engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)