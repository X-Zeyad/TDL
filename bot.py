# bot.py
import os
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger


from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


from db import init_db
from models import Reminder


DATABASE_URL = os.getenv('DATABASE_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

SessionLocal = init_db(DATABASE_URL)
scheduler = AsyncIOScheduler()
app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send /remind YYYY-MM-DD HH:MM | message")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payload = update.message.text.partition(' ')[2]
    if '|' not in payload:
        return await update.message.reply_text("Format: /remind YYYY-MM-DD HH:MM | message")
    when_str, _, text = payload.partition('|')
    when_str = when_str.strip()
    text = text.strip()
    try:
# Accept ISO or space-separated
        if 'T' in when_str:
            dt = datetime.fromisoformat(when_str)
        else:
            dt = datetime.fromisoformat(when_str.replace(' ', 'T'))
    except Exception:
        return await update.message.reply_text("Invalid date format. Use YYYY-MM-DD HH:MM")


    session = SessionLocal()
    try:
        r = Reminder(user_tg_id=update.effective_user.id, text=text, notify_at=dt, sent=False)
        session.add(r)
        session.commit()
        session.refresh(r)
    finally:
        session.close()


    job_id = f"reminder-{r.id}"
    scheduler.add_job(send_notification, trigger=DateTrigger(run_date=dt), args=[r.id], id=job_id, replace_existing=True)
    await update.message.reply_text(f"Reminder scheduled for {dt.isoformat()} (id={r.id})")


async def send_notification(reminder_id: int):
    session = SessionLocal()
    try:
        r = session.get(Reminder, reminder_id)
        if not r or r.sent:
            return
        bot = app.bot
        await bot.send_message(chat_id=r.user_tg_id, text=f"🔔 Reminder: {r.text}")
        r.sent = True
        session.add(r)
        session.commit()
    finally:
        session.close()


async def reschedule_pending():
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        pending = session.query(Reminder).filter(Reminder.sent == False, Reminder.notify_at > now).all()
        for r in pending:
            job_id = f"reminder-{r.id}"
            if not scheduler.get_job(job_id):
                scheduler.add_job(send_notification, trigger=DateTrigger(run_date=r.notify_at), args=[r.id], id=job_id)
    finally:
        session.close()


if __name__ == '__main__':
    scheduler.start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind_command))


    async def main():
        await reschedule_pending()
        await app.run_polling()


    asyncio.run(main()) 