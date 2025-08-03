import json
import aiosqlite
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
import os

TOKEN = os.getenv("TOKEN")

def load_tasks():
    with open("tasks.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_day_keyboard(user_progress):
    buttons = []
    for i in range(1, 8):
        unlocked = str(i) == "1" or str(i - 1) in user_progress
        text = f"✅ День {i}" if str(i) in user_progress else f"🔓 День {i}" if unlocked else f"🔒 День {i}"
        cb_data = f"day_{i}" if unlocked else "locked"
        buttons.append(InlineKeyboardButton(text, callback_data=cb_data))
    return InlineKeyboardMarkup([buttons[i:i + 3] for i in range(0, len(buttons), 3)])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT day FROM progress WHERE user_id = ?", (user_id,)) as cursor:
            user_progress = {row[0] for row in await cursor.fetchall()}

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"Здесь ты найдешь задания на 7 дней.\n"
        f"Выбирай день ниже 👇",
        reply_markup=generate_day_keyboard(user_progress)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "locked":
        await query.answer("Сначала выполни предыдущий день 🔒", show_alert=True)
        return

    if data.startswith("day_"):
        day = data.split("_")[1]
        tasks = load_tasks()
        task = tasks.get(day, "❌ Задание не найдено.")
        await query.edit_message_text(
            f"📌 Задание для дня {day}:\n\n{task}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Завершить день", callback_data=f"done_{day}")]
            ])
        )

    elif data.startswith("done_"):
        day = data.split("_")[1]

        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT 1 FROM progress WHERE user_id = ? AND day = ?", (user_id, day)) as cursor:
                if await cursor.fetchone():
                    await query.answer("Этот день уже завершён ✅", show_alert=True)
                    return
            await db.execute(
                "INSERT INTO progress (user_id, day, completed_at) VALUES (?, ?, ?)",
                (user_id, day, datetime.utcnow().isoformat())
            )
            await db.commit()

            async with db.execute("SELECT day FROM progress WHERE user_id = ?", (user_id,)) as cursor:
                user_progress = {row[0] for row in await cursor.fetchall()}

        await query.edit_message_text(
            f"✅ День {day} завершён! Отличная работа!\n\nВыбирай следующий день:",
            reply_markup=generate_day_keyboard(user_progress)
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT day FROM progress WHERE user_id = ?", (user_id,)) as cursor:
            completed = sorted([int(row[0]) for row in await cursor.fetchall()])
    count = len(completed)
    done = ", ".join([f"{i}" for i in completed]) if completed else "пока ничего"
    await update.message.reply_text(
        f"📊 Твоя статистика:\n\n"
        f"Выполнено дней: {count} из 7\n"
        f"Завершено: {done}"
    )

async def send_daily_tasks(app):
    tasks = load_tasks()
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT DISTINCT user_id FROM progress") as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]
            for user_id in user_ids:
                now_day = str(datetime.utcnow().isoweekday())
                if now_day in tasks:
                    try:
                        await app.bot.send_message(chat_id=user_id, text=f"🌞 Доброе утро!\nВот задание на день {now_day}:\n\n{tasks[now_day]}")
                    except:
                        pass

async def init_db():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER,
                day TEXT,
                completed_at TEXT,
                PRIMARY KEY (user_id, day)
            );
        """)
        await db.commit()

async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button))

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(lambda: send_daily_tasks(app), 'cron', hour=7)
    scheduler.start()

    print("✅ Бот запущен")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())