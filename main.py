import json
import os
import aiosqlite
import asyncio
from datetime import datetime
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

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
    tasks = load_tasks()

    if data == "locked":
        await query.answer("Сначала выполни предыдущий день 🔒", show_alert=True)
        return

    if data.startswith("day_"):
        day = data.split("_")[1]
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

    # Запуск webhook
    WEBHOOK_PATH = "/webhook"
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

    await app.bot.set_webhook(WEBHOOK_URL)

    async def handler(request):
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response()

    web_app = web.Application()
    web_app.router.add_post(WEBHOOK_PATH, handler)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()

    print("✅ Бот запущен по webhook")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())