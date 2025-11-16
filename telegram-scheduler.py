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

bot = Bot(token=TELEGRAM_TOKEN)
scheduler = AsyncIOScheduler()

async def send_notification(reminder_id: int):
    """إرسال تذكير للمستخدم وتحديث الحالة في DB"""
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
    """جدولة جميع التذكيرات المستقبلية غير المرسلة"""
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        pending = session.query(Reminder).filter(Reminder.sent == False, Reminder.notify_at > now).all()
        for r in pending:
            job_id = f"reminder-{r.id}"
            if not scheduler.get_job(job_id):
                scheduler.add_job(
                    send_notification, 
                    trigger=DateTrigger(run_date=r.notify_at), 
                    args=[r.id],
                    id=job_id
                )
    finally:
        session.close()

async def main():
    scheduler.start()
    
    await reschedule_pending()
    
    scheduler.add_job(lambda: asyncio.create_task(reschedule_pending()), 'interval', minutes=1)

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
