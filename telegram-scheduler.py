# scheduler.py
import os
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from telegram import Bot
from db import init_db, wait_for_mysql
from models import Reminder

DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

wait_for_mysql(DATABASE_URL)
SessionLocal = init_db(DATABASE_URL)

scheduler = AsyncIOScheduler()
bot = Bot(token=TELEGRAM_TOKEN)
scheduler.start()

async def send_notification(reminder_id: int):
    session = SessionLocal()
    try:
        r = session.get(Reminder, reminder_id)
        if not r or r.sent:
            return
        await bot.send_message(chat_id=r.user_tg_id, text=f"🔔 Reminder: {r.text}")
        r.sent = True
        session.add(r)
        session.commit()
    finally:
        session.close()

async def schedule_reminder(reminder_id: int, run_at: datetime):
    job_id = f"reminder-{reminder_id}"
    if not scheduler.get_job(job_id):
        scheduler.add_job(send_notification, trigger=DateTrigger(run_date=run_at), args=[reminder_id], id=job_id)

async def reschedule_pending():
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        pending = session.query(Reminder).filter(Reminder.sent == False, Reminder.notify_at > now).all()
        for r in pending:
            await schedule_reminder(r.id, r.notify_at)
    finally:
        session.close()

asyncio.run(reschedule_pending())
