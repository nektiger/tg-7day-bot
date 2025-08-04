import os
import json
import aiosqlite
import asyncio
from aiohttp import web
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes
)

TOKEN = os.getenv("TOKEN")
WEBHOOK_SECRET = "secret-path"  # любой путь, сложный для подбора
PORT = int(os.environ.get('PORT', 10000))

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
        f"👋 Привет, {user.first_name}!\nЗдесь ты найдешь задания на 7 дней.\nВыбирай день ниже 👇",
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
    done = ", ".join([str(i) for i in completed]) if completed else "пока ничего"
    await update.message.reply_text(
        f"📊 Твоя статистика:\n\nВыполнено дней: {count} из 7\nЗавершено: {done}"
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

async def handler(request):
    if request.match_info.get('token') != WEBHOOK_SECRET:
        return web.Response(status=403)
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response()

async def main():
    global app
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button))

    await app.initialize()  # Важно!
    await app.bot.set_webhook(
        url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{WEBHOOK_SECRET}"
    )

    # AIOHTTP сервер
    web_app = web.Application()
    web_app.router.add_post(f'/{WEBHOOK_SECRET}', handler)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    print("✅ Webhook запущен")

    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())