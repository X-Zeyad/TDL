# db.py
from datetime import time
import os
from sqlite3 import OperationalError
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

def wait_for_mysql(url, retries=30, delay=2):
    for i in range(retries):
        try:
            engine = create_engine(url)
            conn = engine.connect()
            conn.close()
            print("MySQL is ready!")
            return
        except OperationalError:
            print(f"MySQL not ready yet... retry {i+1}/{retries}")
            time.sleep(delay)
    raise Exception("MySQL did not become ready in time")

def init_db(database_url=None):
    database_url = database_url or get_database_url_from_env()
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)