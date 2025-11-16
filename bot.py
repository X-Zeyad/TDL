import datetime
from telegram import Bot
from db import init_db, wait_for_mysql
from models import Reminder
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import os

DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

wait_for_mysql(DATABASE_URL)
SessionLocal = init_db(DATABASE_URL)

scheduler = AsyncIOScheduler()
bot = Bot(token=TELEGRAM_TOKEN)

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

async def reschedule_pending():
    session = SessionLocal()
    try:
        now = datetime.now()
        pending = session.query(Reminder).filter(Reminder.sent == False, Reminder.notify_at > now).all()
        for r in pending:
            job_id = f"reminder-{r.id}"
            if not scheduler.get_job(job_id):
                scheduler.add_job(send_notification, trigger=DateTrigger(run_date=r.notify_at), args=[r.id], id=job_id)
    finally:
        session.close()

scheduler.start()

async def main():
    await reschedule_pending()
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
