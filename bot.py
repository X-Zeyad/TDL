import os
import asyncio
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import init_db, wait_for_mysql
from models import Reminder

DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

wait_for_mysql(DATABASE_URL)
SessionLocal = init_db(DATABASE_URL)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send /remind YYYY-MM-DD HH:MM | message")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    payload = update.message.text.partition(' ')[2]
    if '|' not in payload:
        return await update.message.reply_text("Format: /remind YYYY-MM-DD HH:MM | message")

    when_str, _, text = payload.partition('|')
    when_str = when_str.strip()
    text = text.strip()

    try:
        dt = datetime.fromisoformat(when_str.replace(' ', 'T'))
        dt = dt.replace(tzinfo=timezone.utc)  
    except Exception:
        return await update.message.reply_text("Invalid date format. Use YYYY-MM-DD HH:MM")

    session = SessionLocal()
    try:
        r = Reminder(user_tg_id=update.effective_user.id, text=text, notify_at=dt, sent=False)
        session.add(r)
        session.commit()
    finally:
        session.close()

    await update.message.reply_text(f"Reminder saved for {dt.isoformat()} (id={r.id})")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("remind", remind_command))

if __name__ == "__main__":
    asyncio.run(app.run_polling())
