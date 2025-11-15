# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, index=True)
    username = Column(String(128), nullable=True)


class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    user_tg_id = Column(Integer, index=True)
    text = Column(Text)
    notify_at = Column(DateTime, index=True)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())